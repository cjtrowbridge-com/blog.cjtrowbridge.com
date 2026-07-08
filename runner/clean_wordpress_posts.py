#!/usr/bin/env python3
"""Clean imported WordPress Markdown posts with a local Ollama model.

Run from the repository root. The runner is intentionally conservative:
it writes candidates and diagnostics to runner/.state, validates before
touching post files, and never commits.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Callable, Iterable, TextIO


PROMPT_VERSION = "wordpress-cleanup-runner-v4"
DEFAULT_OLLAMA_MODEL = "qwen3.5:9b"
LOCK_STALE_SECONDS = 24 * 60 * 60
REPAIR_DECISIONS = {
    "formatting_fix",
    "minor_text_fix",
    "substantive_change",
    "retry_main",
    "blocked",
}
SECTION_LABELS = (
    "Works Cited",
    "References",
    "Bibliography",
    "Appendix",
    "Footnotes",
    "Sources",
    "Term Paper",
)
WRAPPER_PATTERNS = (
    re.compile(r"<\s*main\b", re.I),
    re.compile(r"<\s*/\s*main\s*>", re.I),
    re.compile(r"<\s*article\b", re.I),
    re.compile(r"<\s*/\s*article\s*>", re.I),
    re.compile(r"<\s*footer\b[^>]*entry-footer", re.I),
    re.compile(r"<\s*div\b[^>]*class=[\"'][^\"']*entry-content", re.I),
)
COPIED_UI_PATTERNS = (
    re.compile(r"<\s*div\b[^>]*class=[\"'][^\"']*\bflex\b", re.I),
    re.compile(r"<\s*div\b[^>]*class=[\"'][^\"']*\bmarkdown\b", re.I),
)
EXPORT_ARTIFACT_PATTERNS = (
    re.compile(r"<\s*/?\s*center\b", re.I),
    re.compile(r"\bdata-mce-fragment\s*=", re.I),
    re.compile(r"<div\b[^>]*\bstyle=[\"'][^\"']*[\"'][^>]*>\s*<iframe\b", re.I),
    re.compile(r"<video\b(?![^>]*\bsrc\s*=)[^>]*>\s*</video\s*>", re.I),
)
WORDPRESS_SHORTCODE_TAG_PATTERN = re.compile(
    r"\\?\[\s*/?\s*(?:audio|caption|embed|gallery|playlist|video|wpvideo)\b[^\]]*\\?\]",
    re.I,
)


class RunnerError(Exception):
    """A runner-level error with a stable process exit code."""

    def __init__(self, message: str, exit_code: int = 2) -> None:
        super().__init__(message)
        self.exit_code = exit_code


@dataclasses.dataclass
class FrontMatter:
    text: str
    front_matter: str
    body: str
    blocks: dict[str, str]
    conversion_state: str | None
    malformed: bool = False
    reason: str = ""


@dataclasses.dataclass
class PostInfo:
    path: Path
    rel_path: str
    front_matter: FrontMatter


@dataclasses.dataclass
class ValidationResult:
    ok: bool
    checks: dict[str, Any]
    failures: list[str]
    review_required: bool = False
    review_reasons: list[str] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class RepairDecision:
    decision: str
    reason: str


class TeeStream:
    def __init__(self, console: TextIO, log: TextIO) -> None:
        self.console = console
        self.log = log

    def write(self, text: str) -> int:
        written = self.console.write(text)
        self.log.write(text)
        self.flush()
        return written

    def flush(self) -> None:
        self.console.flush()
        self.log.flush()

    def __getattr__(self, name: str) -> Any:
        return getattr(self.console, name)


class RunOutputLog:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.handle: TextIO | None = None
        self.original_stdout: TextIO | None = None
        self.original_stderr: TextIO | None = None

    def __enter__(self) -> "RunOutputLog":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.unlink(missing_ok=True)
        self.handle = self.path.open("x", encoding="utf-8", buffering=1, newline="")
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = TeeStream(self.original_stdout, self.handle)
        sys.stderr = TeeStream(self.original_stderr, self.handle)
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        assert self.handle is not None
        if exc_type is not None and not issubclass(exc_type, (SystemExit, KeyboardInterrupt)):
            traceback.print_exception(exc_type, exc, tb, file=self.handle)
        sys.stdout = self.original_stdout or sys.__stdout__
        sys.stderr = self.original_stderr or sys.__stderr__
        self.handle.flush()
        self.handle.close()
        return False


def format_duration(seconds: float) -> str:
    total_seconds = max(0, int(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class ProgressReporter:
    def __init__(self) -> None:
        self.started = time.monotonic()
        self.total: int | None = None
        self.completed = 0
        self.successes = 0
        self.reviews = 0
        self.failures = 0
        self.attempt_seconds = 0.0

    def set_total(self, total: int) -> None:
        self.total = total

    def _eta(self) -> str:
        if self.total is None or self.completed == 0:
            return "unavailable"
        average_seconds = self.attempt_seconds / self.completed
        return format_duration(average_seconds * max(0, self.total - self.completed))

    def log(self, message: str) -> None:
        total = "?" if self.total is None else str(self.total)
        elapsed = format_duration(time.monotonic() - self.started)
        print(
            f"[elapsed={elapsed} progress={self.completed}/{total} eta={self._eta()}] {message}",
            flush=True,
        )

    def finish_post(self, rel_path: str, result: str, attempt_seconds: float) -> None:
        self.completed += 1
        self.attempt_seconds += attempt_seconds
        if result == "success":
            self.successes += 1
        elif result == "review":
            self.reviews += 1
        else:
            self.failures += 1
        self.log(
            f"phase=complete result={result.upper()} post={rel_path} "
            f"attempt={format_duration(attempt_seconds)} successes={self.successes} "
            f"reviews={self.reviews} failures={self.failures}"
        )


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sanitize_id(rel_path: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", rel_path.replace("\\", "/"))
    digest = hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:12]
    return f"{clean}_{digest}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def atomic_write_json(path: Path, data: Any) -> None:
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def parse_front_matter(text: str) -> FrontMatter:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return FrontMatter(text, "", text, {}, None, True, "missing opening front matter delimiter")

    end_idx: int | None = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return FrontMatter(text, "".join(lines[1:]), "", {}, None, True, "missing closing front matter delimiter")

    front_matter = "".join(lines[1:end_idx])
    body = "".join(lines[end_idx + 1 :])
    blocks: dict[str, str] = {}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is not None:
            blocks[current_key] = "".join(current_lines)
        current_key = None
        current_lines = []

    for line in front_matter.splitlines(keepends=True):
        match = re.match(r"^([A-Za-z0-9_-]+):(.*)$", line)
        if match:
            flush()
            current_key = match.group(1)
            current_lines = [line]
        elif current_key is not None:
            current_lines.append(line)
    flush()

    conversion_state = None
    if "conversion_state" in blocks:
        first = blocks["conversion_state"].splitlines()[0]
        conversion_state = first.split(":", 1)[1].strip().strip("\"'")

    return FrontMatter(text, front_matter, body, blocks, conversion_state)


def rebuild_post_with_body(
    original: str,
    cleaned_body: str,
    conversion_state: str = "markdown",
    levenshtein_distance: int | None = None,
    levenshtein_ratio: float | None = None,
    review_required: bool | None = None,
) -> str:
    lines = original.splitlines(keepends=True)
    end_idx = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    front_matter_lines = [
        line
        for line in lines[1:end_idx]
        if not re.match(
            r"^(?:conversion_state|cleanup_levenshtein_distance|"
            r"cleanup_levenshtein_ratio|cleanup_review_required)\s*:",
            line,
        )
    ]
    front_matter_lines.append(f"conversion_state: {conversion_state}\n")
    if levenshtein_distance is not None:
        front_matter_lines.append(f"cleanup_levenshtein_distance: {levenshtein_distance}\n")
    if levenshtein_ratio is not None:
        front_matter_lines.append(f"cleanup_levenshtein_ratio: {levenshtein_ratio:.8f}\n")
    if review_required is not None:
        front_matter_lines.append(
            f"cleanup_review_required: {'true' if review_required else 'false'}\n"
        )
    prefix = lines[0] + "".join(front_matter_lines) + lines[end_idx]
    body = cleaned_body.strip("\r\n")
    return prefix + "\n" + (body + "\n" if body else "")


def is_instagram_post(front_matter: FrontMatter) -> bool:
    categories = front_matter.blocks.get("categories", "")
    return "instagram_image_id" in front_matter.blocks or bool(
        re.search(r"(?im)^\s*-\s*Instagram\s*$", categories)
    )


def deterministic_media_cleanup(body: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    text = body

    def simplify_iframe(match: re.Match[str]) -> str:
        tag = match.group(0)
        src_match = re.search(r"\bsrc\s*=\s*([\"'])(.*?)\1", tag, re.I | re.S)
        if not src_match:
            return tag
        fixes.append("simplified iframe attributes")
        escaped_src = html.escape(html.unescape(src_match.group(2)), quote=True)
        return (
            f'<iframe class="post-embed" src="{escaped_src}" '
            'loading="lazy"></iframe>'
        )

    text = re.sub(
        r"<iframe\b[^>]*(?:/\s*>|>\s*</iframe\s*>)",
        simplify_iframe,
        text,
        flags=re.I | re.S,
    )

    updated = re.sub(r"</?center\s*>", "", text, flags=re.I)
    if updated != text:
        fixes.append("removed center wrapper")
        text = updated

    simple_iframe = r'<iframe class="post-embed" src="[^"]+" loading="lazy"></iframe>'
    updated = re.sub(
        rf"<div\b[^>]*>\s*({simple_iframe})\s*</div\s*>",
        r"\1",
        text,
        flags=re.I | re.S,
    )
    if updated != text:
        fixes.append("removed iframe-only div wrapper")
        text = updated

    updated = re.sub(
        r"(?m)^[ \t]*>[ \t]*(<iframe class=\"post-embed\"[^\n]+</iframe>)[ \t]*$",
        r"\1",
        text,
    )
    if updated != text:
        fixes.append("removed iframe blockquote wrapper")
        text = updated

    updated = re.sub(
        r"<video\b(?![^>]*\bsrc\s*=)[^>]*>\s*</video\s*>",
        "",
        text,
        flags=re.I | re.S,
    )
    if updated != text:
        fixes.append("removed empty video export artifact")
        text = updated

    if fixes:
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip("\r\n") + "\n"
    return text, list(dict.fromkeys(fixes))


def split_markdown_media_blocks(body: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    text = body
    media_patterns = (
        r"(?:\[[ \t]*)?!\[[^\]]*]\((?:[^()]|\([^()]*\))+\)(?:[ \t]*]\((?:[^()]|\([^()]*\))+\))?",
        r"<iframe\b[^>]*(?:/\s*>|>.*?</iframe\s*>)",
        r"<img\b[^>]*>",
    )
    media_regex = re.compile("|".join(f"({pattern})" for pattern in media_patterns), re.I | re.S)

    def separate(match: re.Match[str]) -> str:
        nonlocal fixes
        media = match.group(0).strip()
        start = match.start()
        stop = match.end()
        before = "\n\n" if start > 0 and not text[:start].endswith("\n\n") else ""
        after = "\n\n" if stop < len(text) and not text[stop:].startswith("\n\n") else ""
        if before or after:
            fixes.append("separated media blocks from prose")
        return before + media + after

    updated = media_regex.sub(separate, text)
    if updated != text:
        updated = re.sub(r"[ \t]+\n", "\n", updated)
        updated = re.sub(r"\n{3,}", "\n\n", updated)
    return updated, list(dict.fromkeys(fixes))


def wrap_long_prose_lines(body: str, limit: int = 800, target: int = 560) -> tuple[str, list[str]]:
    fixes: list[str] = []
    wrapped_lines: list[str] = []
    in_code = False
    wrap_count = 0
    media_line = re.compile(r"^\s*(?:!\[[^\]]*]\(|\[!\[[^\]]*]\(|<iframe\b|<img\b)", re.I)
    list_line = re.compile(r"^(\s{0,8}(?:[-+*]|\d+[.)])\s+)(.+)$")

    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            wrapped_lines.append(line)
            continue
        if (
            in_code
            or len(line) <= limit
            or not stripped
            or stripped.startswith("|")
            or stripped.startswith("http")
            or media_line.match(line)
        ):
            wrapped_lines.append(line)
            continue

        prefix = ""
        content = line
        list_match = list_line.match(line)
        if list_match:
            prefix = " " * len(list_match.group(1))
            content = list_match.group(2)

        parts: list[str] = []
        remaining = content.strip()
        while len(remaining) > limit:
            split_at = -1
            for pattern in (r"(?<=[.!?;:])\s+", r"\s+"):
                candidates = [
                    match.end()
                    for match in re.finditer(pattern, remaining[: target + 120])
                    if match.end() >= max(80, target - 160)
                ]
                if candidates:
                    split_at = candidates[-1]
                    break
            if split_at < 1:
                break
            parts.append(remaining[:split_at].rstrip())
            remaining = remaining[split_at:].lstrip()
        if parts and remaining:
            parts.append(remaining)
            wrapped_lines.extend(
                (prefix + part if index else line[: len(line) - len(line.lstrip())] + part)
                for index, part in enumerate(parts)
            )
            wrap_count += 1
        else:
            wrapped_lines.append(line)

    if wrap_count:
        fixes.append(f"wrapped long prose lines: {wrap_count}")
    return "\n".join(wrapped_lines) + ("\n" if body.endswith(("\n", "\r\n")) else ""), fixes


def deterministic_structural_cleanup(body: str) -> tuple[str, list[str]]:
    fixes: list[str] = []
    text, media_fixes = split_markdown_media_blocks(body)
    fixes.extend(media_fixes)
    text, wrap_fixes = wrap_long_prose_lines(text)
    fixes.extend(wrap_fixes)
    if fixes:
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = text.strip("\r\n") + "\n"
    return text, list(dict.fromkeys(fixes))


def deterministic_typography_restore(
    original_body: str,
    candidate_body: str,
) -> tuple[str, list[str]]:
    fixes: list[str] = []
    text = candidate_body

    def restore_exact(original_value: str, candidate_value: str, label: str) -> None:
        nonlocal text
        missing = original_body.count(original_value) - text.count(original_value)
        introduced = text.count(candidate_value) - original_body.count(candidate_value)
        replacements = min(missing, introduced)
        if replacements <= 0:
            return
        text = text.replace(candidate_value, original_value, replacements)
        fixes.append(f"{label}: {replacements}")

    for mojibake, intended in (
        ("â€¦", "…"),
        ("â€™", "’"),
        ("â€˜", "‘"),
        ("â€œ", "“"),
        ("â€\x9d", "”"),
        ("â€”", "—"),
        ("â€“", "–"),
    ):
        restore_exact(intended, mojibake, "restored mojibake")

    curly_apostrophe_words = set(
        re.findall(r"\b[\w]+[’‘][\w]+\b", original_body, flags=re.UNICODE)
    )
    for original_word in sorted(curly_apostrophe_words, key=len, reverse=True):
        ascii_word = original_word.replace("’", "'").replace("‘", "'")
        restore_exact(original_word, ascii_word, "restored curly apostrophe")

    for pattern, label in (
        (r"“[^”\n]{1,200}”", "restored curly double quotes"),
        (r"‘[^’\n]{1,200}’", "restored curly single quotes"),
    ):
        for original_phrase in set(re.findall(pattern, original_body)):
            ascii_phrase = (
                original_phrase.replace("“", '"')
                .replace("”", '"')
                .replace("‘", "'")
                .replace("’", "'")
            )
            restore_exact(original_phrase, ascii_phrase, label)

    return text, fixes


def apply_post_model_deterministic_fixes(
    original_body: str,
    candidate_body: str,
) -> tuple[str, list[dict[str, Any]]]:
    history: list[dict[str, Any]] = []
    text, typography_fixes = deterministic_typography_restore(original_body, candidate_body)
    if typography_fixes:
        history.append({"stage": "deterministic_typography_restore", "fixes": typography_fixes})
    text, structural_fixes = deterministic_structural_cleanup(text)
    if structural_fixes:
        history.append({"stage": "deterministic_structural_cleanup", "fixes": structural_fixes})
    return text, history


def normalize_url(value: str) -> str:
    value = html.unescape(value.strip())
    value = re.sub(r"\\([\\`*{}\[\]()#+.!_>~-])", r"\1", value)
    value = value.strip(".,;:!?)\"]}'")
    return value


def extract_urls(text: str) -> Counter[str]:
    text = WORDPRESS_SHORTCODE_TAG_PATTERN.sub(" ", text)
    pattern = re.compile(r"https?://[^\s<>\"]*?(?=\\?[\])}]|[\s<>\"]|$)", re.I)
    return Counter(
        normalized
        for match in pattern.finditer(text)
        if (normalized := normalize_url(match.group(0))) and not is_allowlisted_removal(normalized)
    )


def extract_image_targets(text: str) -> Counter[str]:
    targets: list[str] = []
    for match in re.finditer(
        r"(?<![A-Za-z0-9])!\[[^\]]*]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
        text,
    ):
        targets.append(normalize_url(match.group(1)))
    for match in re.finditer(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", text, re.I):
        targets.append(normalize_url(match.group(1)))
    return Counter(target for target in targets if target and not is_allowlisted_removal(target))


def extract_linked_image_pairs(text: str) -> Counter[str]:
    pairs: list[str] = []
    image_pattern = re.compile(
        r"(?<![A-Za-z0-9])!\[[^\]]*]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)"
    )
    for image_match in image_pattern.finditer(text):
        search_start = max(0, image_match.start() - 500)
        prefix = text[search_start : image_match.start()]
        if re.search(r"\n[ \t]*\n", prefix):
            prefix = re.split(r"\n[ \t]*\n", prefix)[-1]
            search_start = image_match.start() - len(prefix)
        outer_start = text.rfind("[", search_start, image_match.start())
        if outer_start < 0 or text[outer_start + 1 : image_match.start()] != "":
            continue
        suffix = text[image_match.end() : image_match.end() + 500]
        close_match = re.match(
            r"(?:(?!\n[ \t]*\n)[\s\S])*?]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)",
            suffix,
        )
        if not close_match:
            continue
        image_target = normalize_url(image_match.group(1))
        link_target = normalize_url(close_match.group(1))
        if (
            image_target
            and link_target
            and not is_allowlisted_removal(image_target)
            and not is_allowlisted_removal(link_target)
        ):
            pairs.append(f"{image_target} -> {link_target}")
    return Counter(pairs)


def extract_emphasis_spans(text: str) -> Counter[str]:
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(
        r"(!?\[[^\]]*])\((?:[^()]|\([^()]*\))+\)",
        r"\1",
        text,
    )
    text = re.sub(r"https?://[^\s<>\"]+", "", text, flags=re.I)
    spans: list[str] = []
    pattern = re.compile(r"(?<!\\)(\*{1,3}|_{1,3})(?=\S)(.+?)(?<=\S)\1")
    for match in pattern.finditer(text):
        spans.append(f"{match.group(1)}{match.group(2)}{match.group(1)}")
    return Counter(spans)


def extract_embed_targets(text: str) -> Counter[str]:
    targets = [
        normalize_url(match.group(1))
        for match in re.finditer(r"<iframe\b[^>]*\bsrc=[\"']([^\"']+)[\"']", text, re.I)
    ]
    return Counter(target for target in targets if target and not is_allowlisted_removal(target))


def is_allowlisted_removal(target: str) -> bool:
    lowered = target.lower()
    return lowered.startswith("data:") or "tracking" in lowered or "pixel" in lowered or "1x1" in lowered


def counter_changes(expected: Counter[str], actual: Counter[str]) -> tuple[list[str], list[str]]:
    missing = [
        f"{value} (expected {count}, got {actual[value]})"
        for value, count in sorted(expected.items())
        if actual[value] < count
    ]
    added = [
        f"{value} (expected {expected[value]}, got {count})"
        for value, count in sorted(actual.items())
        if count > expected[value]
    ]
    return missing, added


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "img":
            return
        attributes = {name.lower(): value or "" for name, value in attrs}
        if attributes.get("alt"):
            self.parts.append(attributes["alt"])

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def canonical_visible_text(body: str) -> str:
    text = html.unescape(body)
    text = WORDPRESS_SHORTCODE_TAG_PATTERN.sub("", text)
    text = re.sub(r"(?<!\S)#{1,6}\s+", "", text)
    text = re.sub(r"(?<=\))#{1,6}\s+", "", text)
    text = re.sub(
        r"\[!\[([^\]]*)]\((?:[^()]|\([^()]*\))+\)]\((?:[^()]|\([^()]*\))+\)",
        lambda match: match.group(1),
        text,
    )
    text = re.sub(
        r"(?<![A-Za-z0-9])!\[([^\]]*)]\((?:[^()]|\([^()]*\))+\)",
        lambda match: match.group(1),
        text,
    )
    text = re.sub(
        r"\[([^\]]+)]\((?:[^()]|\([^()]*\))+\)",
        lambda match: match.group(1),
        text,
    )
    text = re.sub(r"https?://[^\s<>\"]+", "", text, flags=re.I)
    text = re.sub(r"\\([\\`*{}\[\]()#+.!_>~-])", r"\1", text)
    source_lines = text.splitlines()
    normalized_lines = []
    for index, line in enumerate(source_lines):
        line = re.sub(r"(?<!\S)#{1,6}\s+", "", line)
        line = re.sub(r"(?<=\))#{1,6}\s+", "", line)
        if (
            index + 1 < len(source_lines)
            and re.match(r"^\s*[-+*]\s+\S", source_lines[index + 1])
        ):
            line = re.sub(r"\s+[-+*]\s+(?=\S)", " ", line)
        line = re.sub(r"^\s{0,3}(?:#{1,6}\s+|>\s?|[-+*]\s+|\d+[.)]\s+)", "", line)
        normalized_lines.append(line)
    text = "\n".join(normalized_lines)
    text = re.sub(r"[*_~`]", "", text)
    parser = VisibleTextParser()
    parser.feed(text)
    parser.close()
    visible = "".join(parser.parts)
    return "".join(character for character in visible if not character.isspace())


def bounded_levenshtein(left: str, right: str, max_distance: int) -> int | None:
    if left == right:
        return 0
    if max_distance < 0 or abs(len(left) - len(right)) > max_distance:
        return None
    if len(left) < len(right):
        left, right = right, left
    if not right:
        return len(left) if len(left) <= max_distance else None
    previous = list(range(len(right) + 1))
    sentinel = max_distance + 1
    for left_index, left_character in enumerate(left, start=1):
        start = max(1, left_index - max_distance)
        stop = min(len(right), left_index + max_distance)
        current = [sentinel] * (len(right) + 1)
        if left_index <= max_distance:
            current[0] = left_index
        for right_index in range(start, stop + 1):
            substitution_cost = 0 if left_character == right[right_index - 1] else 1
            current[right_index] = min(
                previous[right_index] + 1,
                current[right_index - 1] + 1,
                previous[right_index - 1] + substitution_cost,
            )
        if min(current[start : stop + 1], default=sentinel) > max_distance:
            return None
        previous = current
    distance = previous[len(right)]
    return distance if distance <= max_distance else None


def first_mismatch(left: str, right: str, context: int = 30) -> dict[str, Any]:
    index = next(
        (position for position, pair in enumerate(zip(left, right)) if pair[0] != pair[1]),
        min(len(left), len(right)),
    )
    start = max(0, index - context)
    stop = index + context
    return {
        "offset": index,
        "original_context": left[start:stop],
        "candidate_context": right[start:stop],
    }


def visible_text_edits(left: str, right: str, limit: int = 20) -> list[dict[str, str]]:
    edits: list[dict[str, str]] = []
    for tag, left_start, left_stop, right_start, right_stop in difflib.SequenceMatcher(
        None,
        left,
        right,
        autojunk=False,
    ).get_opcodes():
        if tag == "equal":
            continue
        edits.append(
            {
                "operation": tag,
                "original": left[left_start:left_stop],
                "candidate": right[right_start:right_stop],
            }
        )
        if len(edits) >= limit:
            break
    return edits


def section_label_glue_failures(lines: list[str]) -> list[int]:
    failures: list[int] = []
    label_pattern = "|".join(re.escape(label) for label in SECTION_LABELS)
    regex = re.compile(rf"\S.+\s(?:\*\*)?(?:{label_pattern})(?:\*\*)?\s*(?:$|[#*:])", re.I)
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        if any(stripped.lower() == label.lower() for label in SECTION_LABELS):
            continue
        if regex.search(stripped):
            failures.append(idx)
    return failures


def count_long_prose_lines(text: str, limit: int = 800) -> int:
    in_code = False
    count = 0
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code or not stripped or stripped.startswith("|") or stripped.startswith("http"):
            continue
        if len(line) > limit:
            count += 1
    return count


def media_spacing_failures(lines: list[str]) -> list[int]:
    failures: list[int] = []
    media_regex = re.compile(r"^\s*(?:!\[[^\]]*]\([^)]+\)|<iframe\b|<img\b)", re.I)
    for idx, line in enumerate(lines):
        if not media_regex.search(line):
            continue
        prev_ok = idx == 0 or not lines[idx - 1].strip()
        next_ok = idx == len(lines) - 1 or not lines[idx + 1].strip()
        if not prev_ok or not next_ok:
            failures.append(idx + 1)
    return failures


def inline_heading_failures(lines: list[str]) -> list[int]:
    failures: list[int] = []
    for idx, line in enumerate(lines, start=1):
        if "###" in line and not line.lstrip().startswith("#"):
            failures.append(idx)
    return failures


def validate_candidate(
    original: str,
    candidate: str,
    include_missing_state: bool,
    review_max_distance: int = 10,
    review_max_ratio: float = 0.01,
    diagnostic_distance_limit: int = 256,
) -> ValidationResult:
    failures: list[str] = []
    review_reasons: list[str] = []
    checks: dict[str, Any] = {}

    original_fm = parse_front_matter(original)
    candidate_fm = parse_front_matter(candidate)
    checks["front_matter_valid"] = not candidate_fm.malformed
    if candidate_fm.malformed:
        failures.append(f"candidate front matter malformed: {candidate_fm.reason}")
        return ValidationResult(False, checks, failures)

    expected_front_matter = parse_front_matter(
        rebuild_post_with_body(original, original_fm.body)
    ).front_matter
    front_matter_unchanged = candidate_fm.front_matter == expected_front_matter
    checks["front_matter_preserved_exactly"] = front_matter_unchanged
    if not front_matter_unchanged:
        failures.append("front matter changed outside conversion_state")

    original_state = original_fm.conversion_state
    candidate_state = candidate_fm.conversion_state
    checks["conversion_state_markdown"] = candidate_state == "markdown"
    if candidate_state != "markdown":
        failures.append("candidate did not set conversion_state: markdown")
    if original_state is None and not include_missing_state:
        failures.append("missing-state posts require --include-missing-state")

    original_urls = extract_urls(original)
    candidate_urls = extract_urls(candidate)
    missing_urls, added_urls = counter_changes(original_urls, candidate_urls)
    checks["missing_urls"] = missing_urls
    checks["added_urls"] = added_urls
    if missing_urls:
        failures.append(f"candidate removed URLs: {', '.join(missing_urls[:5])}")
    if added_urls:
        failures.append(f"candidate added URLs: {', '.join(added_urls[:5])}")

    original_images = extract_image_targets(original)
    candidate_images = extract_image_targets(candidate)
    missing_images, added_images = counter_changes(original_images, candidate_images)
    checks["missing_images"] = missing_images
    checks["added_images"] = added_images
    if missing_images:
        failures.append(f"candidate removed image targets: {', '.join(missing_images[:5])}")
    if added_images:
        failures.append(f"candidate added image targets: {', '.join(added_images[:5])}")

    original_linked_images = extract_linked_image_pairs(original_fm.body)
    candidate_linked_images = extract_linked_image_pairs(candidate_fm.body)
    missing_linked_images, added_linked_images = counter_changes(
        original_linked_images,
        candidate_linked_images,
    )
    checks["missing_linked_image_pairs"] = missing_linked_images
    checks["added_linked_image_pairs"] = added_linked_images
    if missing_linked_images:
        failures.append(
            "candidate changed linked-image relationships: "
            f"{', '.join(missing_linked_images[:5])}"
        )
    if added_linked_images:
        failures.append(
            "candidate added linked-image relationships: "
            f"{', '.join(added_linked_images[:5])}"
        )

    original_embeds = extract_embed_targets(original)
    candidate_embeds = extract_embed_targets(candidate)
    missing_embeds, added_embeds = counter_changes(original_embeds, candidate_embeds)
    checks["missing_embeds"] = missing_embeds
    checks["added_embeds"] = added_embeds
    if missing_embeds:
        failures.append(f"candidate removed embed targets: {', '.join(missing_embeds[:5])}")
    if added_embeds:
        failures.append(f"candidate added embed targets: {', '.join(added_embeds[:5])}")

    original_emphasis = extract_emphasis_spans(original_fm.body)
    candidate_emphasis = extract_emphasis_spans(candidate_fm.body)
    missing_emphasis, added_emphasis = counter_changes(original_emphasis, candidate_emphasis)
    checks["missing_emphasis_spans"] = missing_emphasis
    checks["added_emphasis_spans"] = added_emphasis
    if missing_emphasis:
        failures.append(
            f"candidate removed emphasis spans: {', '.join(missing_emphasis[:5])}"
        )
    if added_emphasis:
        failures.append(
            f"candidate added emphasis spans: {', '.join(added_emphasis[:5])}"
        )

    original_visible = canonical_visible_text(original_fm.body)
    candidate_visible = canonical_visible_text(candidate_fm.body)
    visible_text_unchanged = candidate_visible == original_visible
    checks["visible_text_preserved"] = visible_text_unchanged
    checks["original_visible_length"] = len(original_visible)
    checks["candidate_visible_length"] = len(candidate_visible)
    checks["original_visible_sha256"] = sha256_text(original_visible)
    checks["candidate_visible_sha256"] = sha256_text(candidate_visible)
    if visible_text_unchanged:
        distance = 0
        distance_ratio = 0.0
    else:
        distance = bounded_levenshtein(
            original_visible,
            candidate_visible,
            max(diagnostic_distance_limit, review_max_distance),
        )
        distance_ratio = (
            distance / max(len(original_visible), len(candidate_visible), 1)
            if distance is not None
            else None
        )
        checks["first_visible_mismatch"] = first_mismatch(original_visible, candidate_visible)
        checks["visible_text_edits"] = visible_text_edits(
            original_visible,
            candidate_visible,
        )
    checks["levenshtein_distance"] = distance
    checks["levenshtein_distance_exceeds"] = (
        max(diagnostic_distance_limit, review_max_distance) if distance is None else None
    )
    checks["levenshtein_ratio"] = distance_ratio
    checks["review_max_distance"] = review_max_distance
    checks["review_max_ratio"] = review_max_ratio
    if not visible_text_unchanged:
        if (
            distance is None
            or distance > review_max_distance
            or distance_ratio is None
            or distance_ratio > review_max_ratio
        ):
            rendered_distance = (
                f">{max(diagnostic_distance_limit, review_max_distance)}"
                if distance is None
                else str(distance)
            )
            failures.append(
                "candidate changed visible text beyond review threshold: "
                f"distance={rendered_distance} ratio={distance_ratio}"
            )
        else:
            review_reasons.append(
                f"visible text changed: distance={distance} ratio={distance_ratio:.8f}"
            )

    wrapper_hits = [pattern.pattern for pattern in WRAPPER_PATTERNS if pattern.search(candidate)]
    checks["remaining_wordpress_wrappers"] = wrapper_hits
    if wrapper_hits:
        failures.append("candidate still contains WordPress wrapper HTML")

    ui_hits = [pattern.pattern for pattern in COPIED_UI_PATTERNS if pattern.search(candidate)]
    checks["remaining_copied_ui_wrappers"] = ui_hits
    if ui_hits:
        failures.append("candidate still contains copied UI wrapper HTML")

    export_hits = [
        pattern.pattern for pattern in EXPORT_ARTIFACT_PATTERNS if pattern.search(candidate_fm.body)
    ]
    checks["remaining_export_artifacts"] = export_hits
    if export_hits:
        failures.append("candidate still contains deterministic export artifacts")

    candidate_lines = candidate_fm.body.splitlines()
    long_lines = count_long_prose_lines(candidate_fm.body)
    checks["long_prose_lines_over_800"] = long_lines
    if long_lines:
        failures.append(f"candidate has {long_lines} long prose lines over 800 characters")

    glued = section_label_glue_failures(candidate_lines)
    checks["section_label_glue_lines"] = glued
    if glued:
        failures.append(f"section labels appear glued to prose on lines: {glued[:10]}")

    media_failures = media_spacing_failures(candidate_lines)
    checks["media_spacing_failure_lines"] = media_failures
    if media_failures:
        failures.append(f"media blocks are not separated from prose on lines: {media_failures[:10]}")

    heading_failures = inline_heading_failures(candidate_lines)
    checks["inline_heading_failure_lines"] = heading_failures
    if heading_failures:
        failures.append(f"headings appear inline on lines: {heading_failures[:10]}")

    review_required = bool(review_reasons) and not failures
    return ValidationResult(not failures, checks, failures, review_required, review_reasons)


class RunnerState:
    def __init__(self, state_dir: Path, write: bool) -> None:
        self.state_dir = state_dir
        self.write = write
        self.attempts_dir = state_dir / "attempts"
        self.responses_dir = state_dir / "responses"
        self.candidates_dir = state_dir / "candidates"
        self.patches_dir = state_dir / "patches"
        self.reports_dir = state_dir / "reports"
        self.runs_dir = state_dir / "runs"
        self.events_path = state_dir / "events.jsonl"
        self.staged_manifest_path = state_dir / "staged_manifest.json"
        self.last_run_path = state_dir / "last_run.json"
        if write:
            for path in (
                self.attempts_dir,
                self.responses_dir,
                self.candidates_dir,
                self.patches_dir,
                self.reports_dir,
                self.runs_dir,
            ):
                path.mkdir(parents=True, exist_ok=True)

    def attempt_id(self, rel_path: str) -> str:
        return sanitize_id(rel_path)

    def append_event(self, event: dict[str, Any]) -> None:
        if not self.write:
            return
        event = {"time": now_iso(), **event}
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")

    def load_attempt(self, rel_path: str) -> dict[str, Any] | None:
        path = self.attempts_dir / f"{self.attempt_id(rel_path)}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"status": "state_malformed", "rel_path": rel_path}

    def save_attempt(self, rel_path: str, data: dict[str, Any]) -> None:
        existing = self.load_attempt(rel_path) or {}
        merged = {**existing, **data, "rel_path": rel_path, "updated_at": now_iso()}
        if "status" in data:
            for stale_key in ("error", "validation_failures"):
                if stale_key not in data:
                    merged.pop(stale_key, None)
        atomic_write_json(self.attempts_dir / f"{self.attempt_id(rel_path)}.json", merged)

    def save_text_artifact(self, kind: str, rel_path: str, suffix: str, content: str) -> Path:
        base = {
            "response": self.responses_dir,
            "candidate": self.candidates_dir,
            "patch": self.patches_dir,
        }[kind]
        path = base / f"{self.attempt_id(rel_path)}{suffix}"
        atomic_write_text(path, content)
        return path

    def save_report(self, rel_path: str, data: dict[str, Any]) -> Path:
        path = self.reports_dir / f"{self.attempt_id(rel_path)}.json"
        atomic_write_json(path, data)
        return path

    def load_staged_manifest(self) -> dict[str, Any]:
        if not self.staged_manifest_path.exists():
            return {"files": {}}
        try:
            return json.loads(self.staged_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"files": {}}

    def record_staged(self, rel_path: str, current_hash: str, attempt_id: str) -> None:
        manifest = self.load_staged_manifest()
        files = manifest.setdefault("files", {})
        files[rel_path.replace("\\", "/")] = {
            "sha256": current_hash,
            "attempt_id": attempt_id,
            "staged_at": now_iso(),
        }
        atomic_write_json(self.staged_manifest_path, manifest)

    def start_run(self, args: argparse.Namespace, candidates: list[PostInfo]) -> dict[str, Any]:
        run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id += f"-{os.getpid()}-{time.time_ns() % 1_000_000:06d}"
        run = {
            "run_id": run_id,
            "status": "running",
            "started_at": now_iso(),
            "mode": args.mode,
            "dry_run": args.dry_run,
            "stage": args.stage,
            "retry_failed": args.retry_failed,
            "requested_limit": args.limit,
            "selected_count": len(candidates),
            "selected_paths": [post.rel_path for post in candidates],
            "attempted": 0,
            "successes": 0,
            "reviews": 0,
            "failures": 0,
            "attempts": [],
        }
        self._save_run(run)
        return run

    def record_run_attempt(
        self,
        run: dict[str, Any],
        rel_path: str,
        result: str,
        elapsed_seconds: float,
    ) -> None:
        attempt = self.load_attempt(rel_path) or {}
        run["attempts"].append(
            {
                "rel_path": rel_path,
                "result": result,
                "status": attempt.get("status", "unknown"),
                "elapsed_seconds": round(elapsed_seconds, 3),
                "levenshtein_distance": attempt.get("levenshtein_distance"),
                "levenshtein_ratio": attempt.get("levenshtein_ratio"),
            }
        )
        run["attempted"] += 1
        result_key = {
            "success": "successes",
            "review": "reviews",
            "failure": "failures",
        }[result]
        run[result_key] += 1
        self._save_run(run)

    def finish_run(self, run: dict[str, Any], status: str) -> None:
        run["status"] = status
        run["finished_at"] = now_iso()
        self._save_run(run)

    def load_last_run(self) -> dict[str, Any] | None:
        if not self.last_run_path.exists():
            return None
        try:
            return json.loads(self.last_run_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _save_run(self, run: dict[str, Any]) -> None:
        atomic_write_json(self.runs_dir / f"{run['run_id']}.json", run)
        atomic_write_json(self.last_run_path, run)

    def summarize(self) -> dict[str, Any]:
        summary = {
            "attempts": 0,
            "successes": 0,
            "reviews": 0,
            "failures": 0,
            "skipped": 0,
            "by_status": {},
        }
        if not self.attempts_dir.exists():
            return summary
        for path in self.attempts_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                status = "state_malformed"
            else:
                status = data.get("status", "unknown")
            summary["attempts"] += 1
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            if status in {"applied", "dry_run_validated", "staged"}:
                summary["successes"] += 1
            elif status in {"review_applied", "dry_run_review", "review_staged"}:
                summary["reviews"] += 1
            elif status.startswith("skipped"):
                summary["skipped"] += 1
            elif status not in {"selected", "candidate_received"}:
                summary["failures"] += 1
        return summary


class RunnerLock:
    def __init__(self, state: RunnerState, args: argparse.Namespace) -> None:
        self.state = state
        self.args = args
        self.path = state.state_dir / "runner.lock"
        self.acquired = False

    def acquire(self) -> None:
        self.state.state_dir.mkdir(parents=True, exist_ok=True)
        metadata = self._metadata()
        try:
            with self.path.open("x", encoding="utf-8") as handle:
                json.dump(metadata, handle, indent=2, sort_keys=True)
                handle.write("\n")
        except FileExistsError:
            existing = self._read_existing()
            stale = self._is_stale(existing)
            if not stale:
                raise RunnerError(f"runner lock exists and appears active: {self.path}", 2)
            if not self.args.replace_stale_lock:
                raise RunnerError(
                    f"stale runner lock exists at {self.path}; inspect it or rerun with --replace-stale-lock",
                    2,
                )
            atomic_write_json(self.path, metadata)
        self.acquired = True

    def heartbeat(self) -> None:
        if not self.acquired:
            return
        metadata = self._read_existing()
        metadata["heartbeat_at"] = now_iso()
        atomic_write_json(self.path, metadata)

    def release(self) -> None:
        if self.acquired and self.path.exists():
            self.path.unlink()
        self.acquired = False

    def _metadata(self) -> dict[str, Any]:
        return {
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "repo_root": str(Path.cwd().resolve()),
            "started_at": now_iso(),
            "heartbeat_at": now_iso(),
            "argv": sys.argv,
        }

    def _read_existing(self) -> dict[str, Any]:
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {"unreadable": True}

    def _is_stale(self, metadata: dict[str, Any]) -> bool:
        if metadata.get("hostname") == socket.gethostname() and isinstance(metadata.get("pid"), int):
            return not process_exists(metadata["pid"])
        heartbeat = metadata.get("heartbeat_at") or metadata.get("started_at")
        if not heartbeat:
            return True
        try:
            when = dt.datetime.fromisoformat(heartbeat.replace("Z", "+00:00"))
        except ValueError:
            return True
        age = dt.datetime.now(dt.timezone.utc) - when
        return age.total_seconds() > LOCK_STALE_SECONDS


def process_exists(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    return True


def ensure_inside(path: Path, root: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise RunnerError(f"path escapes repository root: {path}", 2) from exc
    return resolved


def run_git(repo_root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "-c", f"safe.directory={repo_root.as_posix()}", *args]
    result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
    if check and result.returncode != 0:
        raise RunnerError(result.stderr.strip() or result.stdout.strip() or f"git failed: {' '.join(args)}", 2)
    return result


def git_porcelain(repo_root: Path, extra: list[str] | None = None) -> list[str]:
    args = ["status", "--porcelain=v1"]
    if extra:
        args.extend(extra)
    result = run_git(repo_root, args)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def git_staged_paths(repo_root: Path) -> list[str]:
    paths: list[str] = []
    for line in git_porcelain(repo_root):
        if line.startswith("??"):
            continue
        if line[0] != " ":
            paths.append(line[3:].replace("\\", "/"))
    return paths


def git_unstaged_for_path(repo_root: Path, rel_path: str) -> bool:
    for line in git_porcelain(repo_root, ["--", rel_path]):
        if line.startswith("??"):
            continue
        if len(line) > 1 and line[1] != " ":
            return True
    return False


def preflight_staged(repo_root: Path, state: RunnerState, args: argparse.Namespace) -> None:
    if args.dry_run:
        return
    staged = git_staged_paths(repo_root)
    if not staged:
        return
    manifest = state.load_staged_manifest()
    allowed = manifest.get("files", {})
    unrelated: list[str] = []
    for rel_path in staged:
        record = allowed.get(rel_path)
        if not record:
            unrelated.append(rel_path)
            continue
        path = repo_root / rel_path
        if not path.exists() or sha256_file(path) != record.get("sha256"):
            unrelated.append(rel_path)
    if unrelated and not args.allow_unrelated_staged:
        raise RunnerError(
            "unrelated staged changes exist; commit/review them first or rerun with --allow-unrelated-staged: "
            + ", ".join(unrelated[:10]),
            2,
        )


def discover_posts(repo_root: Path, posts_dir: Path) -> list[PostInfo]:
    posts_root = ensure_inside(repo_root / posts_dir, repo_root)
    posts: list[PostInfo] = []
    for path in posts_root.rglob("*.md"):
        resolved = ensure_inside(path, repo_root)
        rel_path = resolved.relative_to(repo_root).as_posix()
        text = read_text(resolved)
        posts.append(PostInfo(resolved, rel_path, parse_front_matter(text)))
    return sorted(posts, key=lambda post: (post.path.name[:10], post.rel_path))


def is_post_failed(state: RunnerState, rel_path: str) -> bool:
    attempt = state.load_attempt(rel_path)
    if not attempt:
        return False
    status = attempt.get("status", "")
    return status in {
        "validation_failed",
        "cleanup_failed",
        "ollama_failed",
        "oversized_skipped",
        "apply_failed",
        "stage_failed",
    }


def eligible_posts(posts: list[PostInfo], state: RunnerState, args: argparse.Namespace) -> list[PostInfo]:
    selected: list[PostInfo] = []
    for post in posts:
        fm = post.front_matter
        if fm.malformed:
            continue
        if fm.conversion_state == "markdown":
            continue
        if fm.conversion_state is None and not args.include_missing_state:
            continue
        if fm.conversion_state not in {"wordpress", None}:
            continue
        if is_post_failed(state, post.rel_path) and not args.retry_failed:
            continue
        selected.append(post)
    return selected


def inventory_summary(posts: list[PostInfo], state: RunnerState, args: argparse.Namespace) -> dict[str, Any]:
    counts = {
        "wordpress": 0,
        "markdown": 0,
        "review": 0,
        "missing": 0,
        "malformed": 0,
        "other": 0,
        "failed_retry_skipped": 0,
    }
    for post in posts:
        fm = post.front_matter
        if fm.malformed:
            counts["malformed"] += 1
        elif fm.conversion_state == "wordpress":
            counts["wordpress"] += 1
        elif fm.conversion_state == "markdown":
            counts["markdown"] += 1
        elif fm.conversion_state == "review":
            counts["review"] += 1
        elif fm.conversion_state is None:
            counts["missing"] += 1
        else:
            counts["other"] += 1
        if is_post_failed(state, post.rel_path) and not args.retry_failed:
            counts["failed_retry_skipped"] += 1
    candidates = eligible_posts(posts, state, args)
    return {
        "counts": counts,
        "eligible": len(candidates),
        "next": candidates[0].rel_path if candidates else None,
    }


def print_inventory(summary: dict[str, Any]) -> None:
    counts = summary["counts"]
    print("Inventory")
    for key in (
        "wordpress",
        "markdown",
        "review",
        "missing",
        "malformed",
        "other",
        "failed_retry_skipped",
    ):
        print(f"  {key}: {counts[key]}")
    print(f"  eligible: {summary['eligible']}")
    print(f"  next: {summary['next'] or '-'}")


def front_matter_scalar(front_matter: FrontMatter, key: str) -> str | None:
    block = front_matter.blocks.get(key)
    if not block:
        return None
    return block.splitlines()[0].split(":", 1)[1].strip().strip("\"'")


def health_check_ollama(host: str, model: str, timeout: int) -> None:
    url = host.rstrip("/") + "/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RunnerError(f"ollama host is unavailable at {host}: {exc}", 3) from exc
    models = [item.get("name") for item in payload.get("models", []) if isinstance(item, dict)]
    if model not in models:
        raise RunnerError(f"ollama model '{model}' is not listed by {host}; available: {', '.join(models) or '-'}", 3)


def ollama_options(args: argparse.Namespace) -> dict[str, int | float]:
    options: dict[str, int | float] = {
        "temperature": 0,
        "top_p": 0.9,
        "num_ctx": args.ollama_num_ctx,
        "num_predict": args.ollama_num_predict,
        "num_batch": args.ollama_num_batch,
    }
    if args.ollama_num_gpu is not None:
        options["num_gpu"] = args.ollama_num_gpu
    return options


def ollama_generate(
    prompt: str,
    args: argparse.Namespace,
    on_progress: Callable[[str], None] | None = None,
) -> str:
    host = args.ollama_host.rstrip("/")
    url = host + "/api/generate"
    body = {
        "model": args.model,
        "prompt": prompt,
        "stream": True,
        "think": args.ollama_think,
        "options": ollama_options(args),
    }
    encoded = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, headers={"Content-Type": "application/json"}, method="POST")
    last_chunk = time.monotonic()
    parts: list[str] = []
    timeout = min(args.request_timeout_seconds, args.stalled_stream_timeout_seconds)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if on_progress:
            on_progress("phase=ollama_stream_connected")
        last_update = time.monotonic()
        response_chars = 0
        for raw_line in response:
            if time.monotonic() - last_chunk > args.stalled_stream_timeout_seconds:
                raise TimeoutError("ollama stream stalled")
            line = raw_line.decode("utf-8").strip()
            if not line:
                continue
            payload = json.loads(line)
            if "response" in payload:
                parts.append(payload["response"])
                response_chars += len(payload["response"])
                last_chunk = time.monotonic()
            if on_progress and time.monotonic() - last_update >= 15:
                on_progress(f"phase=ollama_streaming response_chars={response_chars}")
                last_update = time.monotonic()
            if payload.get("done"):
                break
    return "".join(parts)


def call_ollama_with_retries(
    prompt: str,
    args: argparse.Namespace,
    on_progress: Callable[[str], None] | None = None,
) -> str:
    last_error: Exception | None = None
    for attempt in range(1, args.max_retries + 2):
        try:
            return ollama_generate(prompt, args, on_progress)
        except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt > args.max_retries:
                break
            delay = min(30, 2**attempt)
            if on_progress:
                on_progress(
                    f"phase=ollama_retry attempt={attempt}/{args.max_retries + 1} "
                    f"delay_seconds={delay} error={exc}"
                )
            time.sleep(delay)
    raise RunnerError(f"ollama request failed after retries: {last_error}", 3)


def build_prompt(rel_path: str, post_body: str, nonce: str) -> str:
    return f"""Clean this WordPress-exported Markdown body.

POST_PATH={rel_path}
PROMPT_VERSION={PROMPT_VERSION}

Rules:
- Return exactly one cleaned Markdown body without YAML front matter.
- Preserve every authored word, spelling, capitalization, and punctuation mark exactly.
- Preserve all links, citations, image targets, embeds, and their occurrence counts.
- Do not add alt text, links, images, embeds, captions, or other content.
- Do not rewrite, copyedit, summarize, shorten, or add claims.
- Preserve source order exactly unless repairing a clearly broken wrapper requires moving content out of markup without changing its relative order.
- Make the Markdown readable and safe for Jekyll.
- Run a self-check after editing and fix any failures before reporting completion.
- If you are uncertain or cannot complete the cleanup safely, set complete: false in the report.

Cleanup requirements:
- Remove WordPress shell wrappers such as main, article, entry-content divs, and entry-footer footers while preserving content inside them.
- Remove copied UI wrapper HTML such as flex or markdown container divs and style-only spans while preserving visible content.
- Convert simple image tags to Markdown images only when all existing alt text and targets can be copied exactly.
- Preserve linked images, embeds, citations, URLs, and end matter.
- Put images and embeds on their own blocks with blank lines around them.
- Split giant single-line paragraphs into readable paragraphs without reordering content.
- Keep prose lines under roughly 800 characters unless they are URLs, tables, code blocks, or intentional artifacts.
- Make section labels such as Works Cited, References, Bibliography, Appendix, Footnotes, Sources, and Term Paper standalone.
- Preserve list indentation and meaningful emphasis.

Response envelope:
BEGIN_CLEANED_BODY {nonce}
[cleaned Markdown body here]
END_CLEANED_BODY {nonce}
BEGIN_CLEANUP_REPORT {nonce}
complete: true|false
fixed:
- [artifact type]
validation_notes:
- [note]
END_CLEANUP_REPORT {nonce}

Original body:
BEGIN_ORIGINAL_BODY {nonce}
{post_body}
END_ORIGINAL_BODY {nonce}
"""


def validation_diagnostics(validation: ValidationResult) -> str:
    payload = {
        "failures": validation.failures,
        "review_reasons": validation.review_reasons,
        "checks": {
            key: validation.checks.get(key)
            for key in (
                "levenshtein_distance",
                "levenshtein_ratio",
                "first_visible_mismatch",
                "visible_text_edits",
                "missing_urls",
                "added_urls",
                "missing_images",
                "added_images",
                "missing_linked_image_pairs",
                "added_linked_image_pairs",
                "missing_embeds",
                "added_embeds",
                "missing_emphasis_spans",
                "added_emphasis_spans",
                "remaining_wordpress_wrappers",
                "remaining_copied_ui_wrappers",
                "remaining_export_artifacts",
                "long_prose_lines_over_800",
                "section_label_glue_lines",
                "media_spacing_failure_lines",
                "inline_heading_failure_lines",
            )
            if key in validation.checks
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def build_classification_prompt(
    rel_path: str,
    original_body: str,
    candidate_body: str,
    validation: ValidationResult,
    nonce: str,
    diff_limit: int = 8_000,
) -> str:
    body_diff = make_diff(rel_path, original_body, candidate_body)
    if len(body_diff) > diff_limit:
        body_diff = body_diff[:diff_limit] + "\n[diff truncated]\n"
    return f"""Classify why this WordPress cleanup candidate did not pass exactly.

POST_PATH={rel_path}
PROMPT_VERSION={PROMPT_VERSION}

Choose exactly one decision:
- formatting_fix: only formatting structure, wrappers, spacing, or media placement needs repair.
- minor_text_fix: the candidate made a small, apparently intentional typo or punctuation correction that should remain human review.
- substantive_change: authored letters, words, punctuation, order, links, or media relationships changed and must be restored from the original.
- retry_main: the candidate missed broad cleanup work or is malformed enough that cleanup should restart from the original.
- blocked: the correct repair is ambiguous and should not be automated.

Rules:
- The original body is authoritative.
- Shortcodes are opaque and are not defects.
- A low Levenshtein distance does not by itself make a text change safe.
- Added emphasis, headings, list semantics, alt text, or changed linked-image nesting count as substantive unless explicit source syntax supports them.
- Choose blocked when evidence is insufficient.

Response envelope:
BEGIN_REPAIR_DECISION {nonce}
decision: formatting_fix|minor_text_fix|substantive_change|retry_main|blocked
reason: [one concise line]
END_REPAIR_DECISION {nonce}

Local validation:
{validation_diagnostics(validation)}

Original-to-candidate diff:
BEGIN_CANDIDATE_DIFF {nonce}
{body_diff}
END_CANDIDATE_DIFF {nonce}
"""


def build_repair_prompt(
    decision: str,
    rel_path: str,
    original_body: str,
    candidate_body: str,
    validation: ValidationResult,
    nonce: str,
) -> str:
    if decision == "formatting_fix":
        task = """Repair only formatting and structure.
- Start from the original body and use the candidate only as a formatting hint.
- You may change whitespace, line breaks, and known wrapper syntax.
- You may relocate existing Markdown structure markers only when the original clearly contains them.
- Do not add emphasis, headings, list semantics, captions, or alt text by inference.
- Preserve linked-image nesting and every URL's role exactly."""
    elif decision == "substantive_change":
        task = """Restore every authored character and content relationship changed by the candidate.
- Use the prior candidate as the formatting template; do not collapse its repaired paragraphs or media blocks.
- Reverse every entry in local validation's visible_text_edits by replacing the candidate text with the exact original text.
- Keep only candidate formatting that can be reproduced without changing the original authored text.
- Restore original spelling, capitalization, punctuation, source order, links, image/link nesting, captions, and media targets.
- Remove any inferred emphasis, headings, list semantics, alt text, or claims."""
    elif decision == "retry_main":
        task = """Restart cleanup from the original body.
- Disregard the candidate except for the local validation failures.
- Perform the main formatting cleanup conservatively.
- If any repair is ambiguous, return complete: false."""
    else:
        raise ValueError(f"unsupported repair decision: {decision}")

    return f"""Repair this WordPress-exported Markdown body after a failed cleanup pass.

POST_PATH={rel_path}
PROMPT_VERSION={PROMPT_VERSION}
REPAIR_DECISION={decision}

{task}

Universal rules:
- Return exactly one cleaned Markdown body without YAML front matter.
- The original body is authoritative.
- Preserve every authored word, spelling, capitalization, and punctuation mark exactly.
- Preserve all URL, image, embed, citation, and shortcode occurrences in source order.
- Treat every shortcode and its attributes as opaque text; do not repair or remove it.
- Do not copyedit, summarize, shorten, or add content.
- Put repaired media blocks and headings on separate lines only when supported by source syntax.
- Set complete: false if the requested repair cannot be completed safely.

Response envelope:
BEGIN_CLEANED_BODY {nonce}
[cleaned Markdown body here]
END_CLEANED_BODY {nonce}
BEGIN_CLEANUP_REPORT {nonce}
complete: true|false
fixed:
- [artifact type]
validation_notes:
- [note]
END_CLEANUP_REPORT {nonce}

Local validation:
{validation_diagnostics(validation)}

BEGIN_ORIGINAL_BODY {nonce}
{original_body}
END_ORIGINAL_BODY {nonce}

BEGIN_PRIOR_CANDIDATE {nonce}
{candidate_body}
END_PRIOR_CANDIDATE {nonce}
"""


def extract_between(text: str, begin: str, end: str) -> str | None:
    begin_count = text.count(begin)
    end_count = text.count(end)
    if begin_count != 1 or end_count != 1:
        return None
    start = text.find(begin) + len(begin)
    stop = text.find(end)
    if stop < start:
        return None
    return text[start:stop].strip("\r\n") + "\n"


def parse_model_response(text: str, nonce: str) -> tuple[str, str, bool]:
    cleaned = extract_between(text, f"BEGIN_CLEANED_BODY {nonce}", f"END_CLEANED_BODY {nonce}")
    report = extract_between(text, f"BEGIN_CLEANUP_REPORT {nonce}", f"END_CLEANUP_REPORT {nonce}")
    if cleaned is None:
        raise RunnerError("model response did not contain exactly one cleaned body block", 1)
    if report is None:
        report = (
            "complete: true\n"
            "fixed:\n"
            "- model omitted cleanup report; runner accepted cleaned body for validation\n"
            "validation_notes:\n"
            "- synthesized by runner after exact cleaned-body envelope was present\n"
        )
    complete_match = re.search(r"(?im)^\s*complete\s*:\s*(true|false)\s*$", report)
    if not complete_match:
        raise RunnerError("cleanup report did not include complete: true|false", 1)
    complete = complete_match.group(1).lower() == "true"
    return cleaned, report, complete


def parse_repair_decision(text: str, nonce: str) -> RepairDecision:
    block = extract_between(
        text,
        f"BEGIN_REPAIR_DECISION {nonce}",
        f"END_REPAIR_DECISION {nonce}",
    )
    if block is None:
        raise RunnerError("model response did not contain exactly one repair decision block", 1)
    decision_match = re.search(r"(?im)^\s*decision\s*:\s*([a-z_]+)\s*$", block)
    reason_match = re.search(r"(?im)^\s*reason\s*:\s*(.+?)\s*$", block)
    if not decision_match or decision_match.group(1) not in REPAIR_DECISIONS:
        raise RunnerError("repair decision was missing or unsupported", 1)
    if not reason_match:
        raise RunnerError("repair decision did not include a reason", 1)
    return RepairDecision(decision_match.group(1), reason_match.group(1))


def request_cleaned_body(
    rel_path: str,
    post_body: str,
    state: RunnerState,
    args: argparse.Namespace,
    progress: ProgressReporter,
) -> tuple[str, str, bool, float, int]:
    total_elapsed = 0.0
    last_error: RunnerError | None = None
    for response_attempt in range(1, args.response_retries + 2):
        nonce = hashlib.sha1(
            f"{rel_path}:{response_attempt}:{time.time_ns()}".encode("utf-8")
        ).hexdigest()[:8]
        state.save_attempt(
            rel_path,
            {"response_nonce": nonce, "response_attempt": response_attempt},
        )
        prompt = build_prompt(rel_path, post_body, nonce)
        state.append_event(
            {
                "event": "ollama_request_started",
                "rel_path": rel_path,
                "response_attempt": response_attempt,
            }
        )
        progress.log(
            f"phase=ollama_request post={rel_path} model={args.model} "
            f"response_attempt={response_attempt}/{args.response_retries + 1} prompt_chars={len(prompt)}"
        )
        request_started = time.monotonic()
        response = call_ollama_with_retries(
            prompt,
            args,
            lambda message: progress.log(f"{message} post={rel_path}"),
        )
        request_elapsed = round(time.monotonic() - request_started, 3)
        total_elapsed += request_elapsed
        progress.log(
            f"phase=ollama_response post={rel_path} response_chars={len(response)} "
            f"request_elapsed={format_duration(request_elapsed)} response_attempt={response_attempt}"
        )
        state.save_text_artifact(
            "response",
            rel_path,
            f".attempt-{response_attempt}.txt",
            response,
        )
        try:
            cleaned_body, model_report, complete = parse_model_response(response, nonce)
        except RunnerError as exc:
            last_error = exc
            state.append_event(
                {
                    "event": "response_envelope_failed",
                    "rel_path": rel_path,
                    "response_attempt": response_attempt,
                    "error": str(exc),
                }
            )
            if response_attempt > args.response_retries:
                break
            progress.log(
                f"phase=response_envelope_retry post={rel_path} "
                f"response_attempt={response_attempt} error={exc}"
            )
            continue
        state.save_text_artifact("response", rel_path, ".txt", response)
        return cleaned_body, model_report, complete, total_elapsed, response_attempt
    raise RunnerError(
        f"model response envelope failed after {args.response_retries + 1} attempts: {last_error}",
        1,
    )


def request_custom_envelope(
    rel_path: str,
    state: RunnerState,
    args: argparse.Namespace,
    progress: ProgressReporter,
    phase: str,
    artifact_suffix: str,
    prompt_factory: Callable[[str], str],
    parser: Callable[[str, str], Any],
) -> tuple[Any, float, int]:
    total_elapsed = 0.0
    last_error: RunnerError | None = None
    for response_attempt in range(1, args.response_retries + 2):
        nonce = hashlib.sha1(
            f"{rel_path}:{phase}:{response_attempt}:{time.time_ns()}".encode("utf-8")
        ).hexdigest()[:8]
        prompt = prompt_factory(nonce)
        state.save_attempt(
            rel_path,
            {
                "response_nonce": nonce,
                "response_attempt": response_attempt,
                "pipeline_phase": phase,
            },
        )
        state.append_event(
            {
                "event": f"{phase}_started",
                "rel_path": rel_path,
                "response_attempt": response_attempt,
            }
        )
        progress.log(
            f"phase={phase}_request post={rel_path} model={args.model} "
            f"response_attempt={response_attempt}/{args.response_retries + 1} "
            f"prompt_chars={len(prompt)}"
        )
        request_started = time.monotonic()
        response = call_ollama_with_retries(
            prompt,
            args,
            lambda message: progress.log(f"{message} pipeline_phase={phase} post={rel_path}"),
        )
        request_elapsed = round(time.monotonic() - request_started, 3)
        total_elapsed += request_elapsed
        progress.log(
            f"phase={phase}_response post={rel_path} response_chars={len(response)} "
            f"request_elapsed={format_duration(request_elapsed)} "
            f"response_attempt={response_attempt}"
        )
        suffix = f"{artifact_suffix}.attempt-{response_attempt}.txt"
        state.save_text_artifact("response", rel_path, suffix, response)
        try:
            parsed = parser(response, nonce)
        except RunnerError as exc:
            last_error = exc
            state.append_event(
                {
                    "event": f"{phase}_envelope_failed",
                    "rel_path": rel_path,
                    "response_attempt": response_attempt,
                    "error": str(exc),
                }
            )
            if response_attempt > args.response_retries:
                break
            progress.log(
                f"phase={phase}_envelope_retry post={rel_path} "
                f"response_attempt={response_attempt} error={exc}"
            )
            continue
        state.save_text_artifact("response", rel_path, f"{artifact_suffix}.txt", response)
        return parsed, total_elapsed, response_attempt
    raise RunnerError(
        f"{phase} response envelope failed after "
        f"{args.response_retries + 1} attempts: {last_error}",
        1,
    )


def request_repair_decision(
    rel_path: str,
    original_body: str,
    candidate_body: str,
    validation: ValidationResult,
    round_number: int,
    state: RunnerState,
    args: argparse.Namespace,
    progress: ProgressReporter,
) -> tuple[RepairDecision, float, int]:
    parsed, elapsed, response_attempt = request_custom_envelope(
        rel_path,
        state,
        args,
        progress,
        f"repair_classification_round_{round_number}",
        f".classification-round-{round_number}",
        lambda nonce: build_classification_prompt(
            rel_path,
            original_body,
            candidate_body,
            validation,
            nonce,
            args.repair_diff_max_chars,
        ),
        parse_repair_decision,
    )
    return parsed, elapsed, response_attempt


def request_repaired_body(
    decision: str,
    rel_path: str,
    original_body: str,
    candidate_body: str,
    validation: ValidationResult,
    round_number: int,
    state: RunnerState,
    args: argparse.Namespace,
    progress: ProgressReporter,
) -> tuple[str, str, bool, float, int]:
    parsed, elapsed, response_attempt = request_custom_envelope(
        rel_path,
        state,
        args,
        progress,
        f"repair_generation_round_{round_number}",
        f".repair-round-{round_number}",
        lambda nonce: build_repair_prompt(
            decision,
            rel_path,
            original_body,
            candidate_body,
            validation,
            nonce,
        ),
        parse_model_response,
    )
    cleaned_body, model_report, complete = parsed
    return cleaned_body, model_report, complete, elapsed, response_attempt


def make_diff(rel_path: str, original: str, candidate: str) -> str:
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            candidate.splitlines(keepends=True),
            fromfile=f"a/{rel_path}",
            tofile=f"b/{rel_path}",
        )
    )


def stage_file(repo_root: Path, rel_path: str) -> None:
    run_git(repo_root, ["add", "--", rel_path], check=True)


def process_post(
    repo_root: Path,
    post: PostInfo,
    state: RunnerState,
    args: argparse.Namespace,
    lock: RunnerLock | None,
    progress: ProgressReporter,
) -> str:
    rel_path = post.rel_path
    attempt_id = state.attempt_id(rel_path)
    if lock:
        lock.heartbeat()

    if git_unstaged_for_path(repo_root, rel_path):
        raise RunnerError(f"target post has unstaged changes: {rel_path}", 2)

    original = read_text(post.path)
    original_hash = sha256_text(original)
    original_fm = parse_front_matter(original)
    progress.log(f"phase=selected post={rel_path} chars={len(original)}")
    state.append_event({"event": "selected", "rel_path": rel_path, "attempt_id": attempt_id})
    state.save_attempt(
        rel_path,
        {
            "attempt_id": attempt_id,
            "status": "selected",
            "original_sha256": original_hash,
            "prompt_version": PROMPT_VERSION,
            "model": args.model,
            "ollama_host": args.ollama_host,
            "generation_options": {**ollama_options(args), "think": args.ollama_think},
        },
    )

    if len(original_fm.body) > args.single_pass_max_chars:
        reason = (
            f"post body length {len(original_fm.body)} exceeds "
            f"--single-pass-max-chars {args.single_pass_max_chars}"
        )
        report = {"status": "oversized_skipped", "rel_path": rel_path, "reason": reason}
        state.save_attempt(rel_path, {"attempt_id": attempt_id, "status": "oversized_skipped", "reason": reason})
        state.save_report(rel_path, report)
        state.append_event({"event": "skipped_oversized", "rel_path": rel_path, "reason": reason})
        progress.log(f"phase=failure post={rel_path} reason={reason}")
        return "failure"

    pipeline_history: list[dict[str, Any]] = []
    request_elapsed = 0.0
    response_attempt = 0

    if is_instagram_post(original_fm):
        cleaned_body = original_fm.body
        model_report = (
            "complete: true\n"
            "fixed:\n"
            "- preserved existing Instagram Markdown body deterministically\n"
            "validation_notes:\n"
            "- Ollama was not called\n"
        )
        complete = True
        state.save_attempt(
            rel_path,
            {
                "attempt_id": attempt_id,
                "cleanup_mode": "deterministic_instagram",
                "ollama_elapsed_seconds": 0,
                "response_attempt": 0,
            },
        )
        state.append_event({"event": "deterministic_instagram_cleanup", "rel_path": rel_path})
        progress.log(f"phase=deterministic_instagram_cleanup post={rel_path}")
    else:
        deterministic_body, deterministic_fixes = deterministic_media_cleanup(original_fm.body)
        deterministic_validation: ValidationResult | None = None
        if deterministic_fixes:
            deterministic_candidate = rebuild_post_with_body(original, deterministic_body)
            deterministic_validation = validate_candidate(
                original,
                deterministic_candidate,
                args.include_missing_state,
                args.review_max_distance,
                args.review_max_ratio,
            )
            pipeline_history.append(
                {
                    "stage": "deterministic_media_cleanup",
                    "fixes": deterministic_fixes,
                    "validation": dataclasses.asdict(deterministic_validation),
                }
            )
            progress.log(
                f"phase=deterministic_media_cleanup post={rel_path} "
                f"fixes={json.dumps(deterministic_fixes)} "
                f"valid={str(deterministic_validation.ok).lower()}"
            )
        if (
            deterministic_validation is not None
            and deterministic_validation.ok
            and not deterministic_validation.review_required
        ):
            cleaned_body = deterministic_body
            model_report = (
                "complete: true\n"
                "fixed:\n"
                + "".join(f"- {fix}\n" for fix in deterministic_fixes)
                + "validation_notes:\n- Ollama was not called\n"
            )
            complete = True
            state.save_attempt(
                rel_path,
                {
                    "attempt_id": attempt_id,
                    "cleanup_mode": "deterministic_media",
                    "ollama_elapsed_seconds": 0,
                    "response_attempt": 0,
                },
            )
        else:
            try:
                main_input_body = (
                    deterministic_body if deterministic_fixes else original_fm.body
                )
                cleaned_body, model_report, complete, request_elapsed, response_attempt = request_cleaned_body(
                    rel_path,
                    main_input_body,
                    state,
                    args,
                    progress,
                )
            except RunnerError as exc:
                status = "ollama_failed" if exc.exit_code == 3 else "cleanup_failed"
                state.save_attempt(
                    rel_path,
                    {"attempt_id": attempt_id, "status": status, "error": str(exc)},
                )
                state.save_report(rel_path, {"status": status, "rel_path": rel_path, "error": str(exc)})
                state.append_event({"event": status, "rel_path": rel_path, "error": str(exc)})
                progress.log(f"phase=failure post={rel_path} reason={exc}")
                return "failure"
            cleaned_body, deterministic_fix_history = apply_post_model_deterministic_fixes(
                original_fm.body,
                cleaned_body,
            )
            for fix_entry in deterministic_fix_history:
                fix_entry["after"] = "main_cleanup"
                pipeline_history.append(fix_entry)
                progress.log(
                    f"phase={fix_entry['stage']} post={rel_path} "
                    f"fixes={json.dumps(fix_entry['fixes'])}"
                )
            pipeline_history.append(
                {
                    "stage": "main_cleanup",
                    "input": (
                        "deterministic_candidate"
                        if deterministic_fixes
                        else "original_body"
                    ),
                    "response_attempt": response_attempt,
                    "complete": complete,
                }
            )
            state.save_attempt(
                rel_path,
                {
                    "attempt_id": attempt_id,
                    "cleanup_mode": "ollama_repair_pipeline",
                    "ollama_elapsed_seconds": round(request_elapsed, 3),
                    "response_attempt": response_attempt,
                },
            )

    provisional_candidate = rebuild_post_with_body(original, cleaned_body)
    progress.log(
        f"phase=validation_started post={rel_path} candidate_chars={len(provisional_candidate)}"
    )
    validation = validate_candidate(
        original,
        provisional_candidate,
        args.include_missing_state,
        args.review_max_distance,
        args.review_max_ratio,
    )

    repair_rounds = getattr(args, "repair_rounds", 0)
    repair_max_chars = getattr(args, "repair_max_chars", 12_000)
    for round_number in range(1, repair_rounds + 1):
        if complete and validation.ok and not validation.review_required:
            break
        combined_chars = len(original_fm.body) + len(cleaned_body)
        if combined_chars > repair_max_chars:
            pipeline_history.append(
                {
                    "stage": "repair_blocked",
                    "round": round_number,
                    "reason": (
                        f"combined original and candidate length {combined_chars} "
                        f"exceeds repair limit {repair_max_chars}"
                    ),
                }
            )
            progress.log(
                f"phase=repair_blocked post={rel_path} round={round_number} "
                f"combined_chars={combined_chars} limit={repair_max_chars}"
            )
            break
        if not complete:
            decision = RepairDecision(
                "retry_main",
                "prior cleanup stage reported complete: false",
            )
            classify_elapsed = 0.0
            classify_attempt = 0
        else:
            try:
                decision, classify_elapsed, classify_attempt = request_repair_decision(
                    rel_path,
                    original_fm.body,
                    cleaned_body,
                    validation,
                    round_number,
                    state,
                    args,
                    progress,
                )
            except RunnerError as exc:
                pipeline_history.append(
                    {
                        "stage": "repair_classification_failed",
                        "round": round_number,
                        "error": str(exc),
                    }
                )
                progress.log(
                    f"phase=repair_classification_failed post={rel_path} "
                    f"round={round_number} error={exc}"
                )
                break
        if (
            decision.decision == "formatting_fix"
            and not validation.checks.get("visible_text_preserved", False)
        ):
            decision = RepairDecision(
                "substantive_change",
                "local override: formatting candidate also changed authored text",
            )
        elif decision.decision == "minor_text_fix" and not validation.ok:
            decision = RepairDecision(
                "substantive_change",
                "local override: minor text change accompanied validation failures",
            )
        request_elapsed += classify_elapsed
        pipeline_history.append(
            {
                "stage": "repair_classification",
                "round": round_number,
                "decision": decision.decision,
                "reason": decision.reason,
                "response_attempt": classify_attempt,
            }
        )
        state.append_event(
            {
                "event": "repair_classified",
                "rel_path": rel_path,
                "round": round_number,
                "decision": decision.decision,
                "reason": decision.reason,
            }
        )
        progress.log(
            f"phase=repair_classified post={rel_path} round={round_number} "
            f"decision={decision.decision} reason={decision.reason}"
        )
        if decision.decision in {"minor_text_fix", "blocked"}:
            break
        try:
            (
                repaired_body,
                repair_report,
                repair_complete,
                repair_elapsed,
                repair_attempt,
            ) = request_repaired_body(
                decision.decision,
                rel_path,
                original_fm.body,
                cleaned_body,
                validation,
                round_number,
                state,
                args,
                progress,
            )
        except RunnerError as exc:
            pipeline_history.append(
                {
                    "stage": "repair_generation_failed",
                    "round": round_number,
                    "decision": decision.decision,
                    "error": str(exc),
                }
            )
            progress.log(
                f"phase=repair_generation_failed post={rel_path} "
                f"round={round_number} error={exc}"
            )
            break
        request_elapsed += repair_elapsed
        pipeline_history.append(
            {
                "stage": "repair_generation",
                "round": round_number,
                "decision": decision.decision,
                "complete": repair_complete,
                "response_attempt": repair_attempt,
                "model_report": repair_report,
            }
        )
        cleaned_body, deterministic_fix_history = apply_post_model_deterministic_fixes(
            original_fm.body,
            repaired_body,
        )
        for fix_entry in deterministic_fix_history:
            fix_entry["after"] = f"repair_round_{round_number}"
            pipeline_history.append(fix_entry)
            progress.log(
                f"phase={fix_entry['stage']} post={rel_path} "
                f"round={round_number} fixes={json.dumps(fix_entry['fixes'])}"
            )
        model_report = repair_report
        complete = repair_complete
        provisional_candidate = rebuild_post_with_body(original, cleaned_body)
        validation = validate_candidate(
            original,
            provisional_candidate,
            args.include_missing_state,
            args.review_max_distance,
            args.review_max_ratio,
        )
        if not repair_complete:
            progress.log(
                f"phase=repair_incomplete post={rel_path} round={round_number}"
            )
        progress.log(
            f"phase=repair_validated post={rel_path} round={round_number} "
            f"valid={str(validation.ok).lower()} "
            f"review={str(validation.review_required).lower()} "
            f"failures={json.dumps(validation.failures)}"
        )

    if not complete:
        validation.failures.append("cleanup remained incomplete after repair rounds")
        validation.ok = False
        validation.review_required = False

    distance = validation.checks.get("levenshtein_distance")
    ratio = validation.checks.get("levenshtein_ratio")
    state.save_attempt(
        rel_path,
        {
            "attempt_id": attempt_id,
            "ollama_elapsed_seconds": round(request_elapsed, 3),
            "pipeline_history": pipeline_history,
        },
    )
    if validation.ok:
        if not isinstance(distance, int) or not isinstance(ratio, (int, float)):
            raise RunnerError("validation passed without exact Levenshtein diagnostics", 2)
        result_kind = "review" if validation.review_required else "success"
        candidate = rebuild_post_with_body(
            original,
            cleaned_body,
            conversion_state="review" if validation.review_required else "markdown",
            levenshtein_distance=distance,
            levenshtein_ratio=float(ratio),
            review_required=validation.review_required,
        )
    else:
        result_kind = "failure"
        candidate = provisional_candidate
    state.save_text_artifact("candidate", rel_path, ".md", candidate)
    state.append_event(
        {
            "event": "candidate_received",
            "rel_path": rel_path,
            "candidate_sha256": sha256_text(candidate),
        }
    )
    diff = make_diff(rel_path, original, candidate)
    state.save_text_artifact("patch", rel_path, ".diff", diff)
    if not validation.ok:
        validation_status = "validation_failed"
    elif validation.review_required:
        validation_status = "validation_review"
    else:
        validation_status = "validation_passed"
    report = {
        "status": validation_status,
        "rel_path": rel_path,
        "model_report": model_report,
        "pipeline_history": pipeline_history,
        "validation": dataclasses.asdict(validation),
        "patch_lines": len(diff.splitlines()),
    }

    if not validation.ok:
        state.save_attempt(
            rel_path,
            {
                "attempt_id": attempt_id,
                "status": "validation_failed",
                "validation_failures": validation.failures,
                "levenshtein_distance": distance,
                "levenshtein_ratio": ratio,
            },
        )
        state.save_report(rel_path, report)
        state.append_event({"event": "validation_failed", "rel_path": rel_path, "failures": validation.failures})
        progress.log(
            f"phase=failure post={rel_path} reason=validation_failed "
            f"failures={json.dumps(validation.failures)}"
        )
        return "failure"

    progress.log(
        f"phase={'validation_review' if validation.review_required else 'validation_passed'} "
        f"post={rel_path} distance={distance} ratio={float(ratio):.8f} "
        f"patch_lines={len(diff.splitlines())}"
    )
    if args.dry_run:
        dry_status = "dry_run_review" if validation.review_required else "dry_run_validated"
        state.save_attempt(
            rel_path,
            {
                "attempt_id": attempt_id,
                "status": dry_status,
                "candidate_sha256": sha256_text(candidate),
                "levenshtein_distance": distance,
                "levenshtein_ratio": ratio,
            },
        )
        dry_report = {**report, "status": dry_status}
        state.save_report(rel_path, dry_report)
        state.append_event({"event": dry_status, "rel_path": rel_path})
        progress.log(f"phase={dry_status} post={rel_path}")
        return result_kind

    current_hash = sha256_text(read_text(post.path))
    if current_hash != original_hash:
        state.save_attempt(rel_path, {"attempt_id": attempt_id, "status": "apply_failed", "error": "target changed during processing"})
        state.save_report(rel_path, {"status": "apply_failed", "rel_path": rel_path, "error": "target changed during processing"})
        state.append_event({"event": "apply_failed", "rel_path": rel_path, "error": "target changed during processing"})
        progress.log(f"phase=failure post={rel_path} reason=target_changed_during_processing")
        return "failure"

    progress.log(f"phase=apply_started post={rel_path}")
    atomic_write_text(post.path, candidate)
    applied_hash = sha256_text(candidate)
    applied_status = "review_applied" if validation.review_required else "applied"
    state.save_attempt(
        rel_path,
        {
            "attempt_id": attempt_id,
            "status": applied_status,
            "candidate_sha256": applied_hash,
            "levenshtein_distance": distance,
            "levenshtein_ratio": ratio,
        },
    )
    applied_report = {**report, "status": applied_status}
    state.save_report(rel_path, applied_report)
    state.append_event(
        {"event": applied_status, "rel_path": rel_path, "candidate_sha256": applied_hash}
    )
    progress.log(f"phase={applied_status} post={rel_path} sha256={applied_hash}")

    if args.stage:
        progress.log(f"phase=staging_started post={rel_path}")
        try:
            stage_file(repo_root, rel_path)
        except RunnerError as exc:
            state.save_attempt(rel_path, {"attempt_id": attempt_id, "status": "stage_failed", "error": str(exc)})
            state.append_event({"event": "stage_failed", "rel_path": rel_path, "error": str(exc)})
            progress.log(f"phase=failure post={rel_path} reason={exc}")
            raise
        state.record_staged(rel_path, applied_hash, attempt_id)
        staged_status = "review_staged" if validation.review_required else "staged"
        state.save_attempt(
            rel_path,
            {"attempt_id": attempt_id, "status": staged_status, "candidate_sha256": applied_hash},
        )
        state.append_event({"event": staged_status, "rel_path": rel_path})
        progress.log(f"phase={staged_status} post={rel_path}")
    return result_kind


def print_report(repo_root: Path, posts: list[PostInfo], state: RunnerState, args: argparse.Namespace) -> None:
    summary = state.summarize()
    last_run = state.load_last_run()
    inv = inventory_summary(posts, state, args)
    staged = git_staged_paths(repo_root)
    manifest = state.load_staged_manifest()
    owned = []
    unrelated = []
    review_posts: list[tuple[int, float, str]] = []
    for post in posts:
        if post.front_matter.conversion_state != "review":
            continue
        try:
            distance = int(
                front_matter_scalar(post.front_matter, "cleanup_levenshtein_distance") or "-1"
            )
            ratio = float(
                front_matter_scalar(post.front_matter, "cleanup_levenshtein_ratio") or "-1"
            )
        except ValueError:
            distance = -1
            ratio = -1.0
        review_posts.append((distance, ratio, post.rel_path))
    review_posts.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    for rel_path in staged:
        if rel_path in manifest.get("files", {}):
            owned.append(rel_path)
        else:
            unrelated.append(rel_path)
    print("Runner Report")
    print(f"  attempts: {summary['attempts']}")
    print(f"  successes: {summary['successes']}")
    print(f"  reviews: {summary['reviews']}")
    print(f"  failures: {summary['failures']}")
    print(f"  skipped: {summary['skipped']}")
    print(f"  by_status: {json.dumps(summary['by_status'], sort_keys=True)}")
    print(f"  eligible_remaining: {inv['eligible']}")
    print(f"  next: {inv['next'] or '-'}")
    print(f"  runner_owned_staged: {len(owned)}")
    print(f"  unrelated_staged: {len(unrelated)}")
    print(f"  review_posts: {len(review_posts)}")
    if owned:
        print("  runner_owned_staged_paths:")
        for path in owned[:50]:
            print(f"    - {path}")
    if unrelated:
        print("  unrelated_staged_paths:")
        for path in unrelated[:50]:
            print(f"    - {path}")
    if review_posts:
        print("  review_posts_by_distance:")
        for distance, ratio, path in review_posts[:50]:
            print(f"    - distance={distance} ratio={ratio:.8f} {path}")
    if last_run:
        print("Last Run")
        print(f"  run_id: {last_run['run_id']}")
        print(f"  status: {last_run['status']}")
        print(f"  selected: {last_run['selected_count']}")
        print(f"  attempted: {last_run['attempted']}")
        print(f"  successes: {last_run['successes']}")
        print(f"  reviews: {last_run.get('reviews', 0)}")
        print(f"  failures: {last_run['failures']}")
        print(f"  dry_run: {str(last_run['dry_run']).lower()}")
        print(f"  stage: {str(last_run['stage']).lower()}")


def require_model(args: argparse.Namespace) -> None:
    if not args.model:
        raise RunnerError("mutating modes require a non-empty Ollama model", 2)


def explicit_post(repo_root: Path, posts: list[PostInfo], args: argparse.Namespace) -> PostInfo | None:
    if not args.post:
        return None
    requested = ensure_inside((repo_root / args.post).resolve(), repo_root)
    for post in posts:
        if post.path.resolve() == requested:
            fm = post.front_matter
            if fm.malformed:
                raise RunnerError(f"--post has malformed front matter: {post.rel_path}", 2)
            if fm.conversion_state == "markdown":
                raise RunnerError(f"--post is already conversion_state: markdown: {post.rel_path}", 2)
            if fm.conversion_state is None and not args.include_missing_state:
                raise RunnerError(f"--post is missing conversion_state; use --include-missing-state to process it: {post.rel_path}", 2)
            if fm.conversion_state not in {"wordpress", None}:
                raise RunnerError(f"--post has unsupported conversion_state '{fm.conversion_state}': {post.rel_path}", 2)
            return post
    raise RunnerError(f"--post is not an indexed Markdown file under {args.posts_dir}: {args.post}", 2)


def select_run_candidates(candidates: list[PostInfo], mode: str, limit: int | None) -> list[PostInfo]:
    selected = candidates[:1] if mode == "next" else candidates
    return selected[:limit] if limit is not None else selected


def run_next_or_batch(repo_root: Path, posts: list[PostInfo], state: RunnerState, args: argparse.Namespace) -> int:
    progress = ProgressReporter()
    require_model(args)
    progress.log(f"phase=health_check host={args.ollama_host} model={args.model}")
    health_check_ollama(args.ollama_host, args.model, args.request_timeout_seconds)
    progress.log("phase=health_check_passed")
    progress.log("phase=git_preflight")
    preflight_staged(repo_root, state, args)
    progress.log("phase=git_preflight_passed")
    lock = RunnerLock(state, args)
    lock.acquire()
    success_count = 0
    review_count = 0
    failure_count = 0
    run_record: dict[str, Any] | None = None
    run_status = "aborted"
    try:
        explicit = explicit_post(repo_root, posts, args)
        candidates = [explicit] if explicit else eligible_posts(posts, state, args)
        candidates = select_run_candidates(candidates, args.mode, args.limit)
        run_record = state.start_run(args, candidates)
        progress.set_total(len(candidates))
        if not candidates:
            progress.log("phase=complete result=NO_ELIGIBLE_POSTS")
            run_status = "completed_no_eligible_posts"
            return 0
        deadline = time.monotonic() + args.max_runtime_minutes * 60 if args.max_runtime_minutes else None
        progress.log(
            f"phase=run_started mode={args.mode} effective_limit={len(candidates)} "
            f"requested_limit={args.limit if args.limit is not None else 'none'}"
        )
        for position, post in enumerate(candidates, start=1):
            if deadline and time.monotonic() > deadline:
                progress.log("phase=runtime_limit_reached")
                run_status = "runtime_limit_reached"
                break
            attempt_started = time.monotonic()
            progress.log(f"phase=post_started position={position}/{len(candidates)} post={post.rel_path}")
            try:
                result = process_post(repo_root, post, state, args, lock, progress)
            except RunnerError:
                elapsed_seconds = time.monotonic() - attempt_started
                progress.finish_post(post.rel_path, "failure", elapsed_seconds)
                state.record_run_attempt(run_record, post.rel_path, "failure", elapsed_seconds)
                progress.log(
                    f"phase=failure_artifacts post={post.rel_path} "
                    f"attempt={state.attempts_dir / (state.attempt_id(post.rel_path) + '.json')} "
                    f"report={state.reports_dir / (state.attempt_id(post.rel_path) + '.json')}"
                )
                run_status = "runner_error"
                raise
            elapsed_seconds = time.monotonic() - attempt_started
            progress.finish_post(post.rel_path, result, elapsed_seconds)
            state.record_run_attempt(run_record, post.rel_path, result, elapsed_seconds)
            if result == "success":
                success_count += 1
            elif result == "review":
                review_count += 1
            else:
                failure_count += 1
                progress.log(
                    f"phase=failure_artifacts post={post.rel_path} "
                    f"attempt={state.attempts_dir / (state.attempt_id(post.rel_path) + '.json')} "
                    f"report={state.reports_dir / (state.attempt_id(post.rel_path) + '.json')}"
                )
                state.append_event({"event": "skipped_after_failure", "rel_path": post.rel_path})
                if args.mode == "next" or args.stop_on_failure:
                    progress.log("phase=run_stopped reason=post_failure")
                    run_status = "stopped_on_failure"
                    return 1
        progress.log(
            f"phase=run_complete successes={success_count} reviews={review_count} "
            f"failures={failure_count}"
        )
        if run_status == "aborted":
            run_status = "completed"
        return 0
    finally:
        if run_record is not None:
            state.finish_run(run_record, run_status)
        lock.release()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["next", "batch", "inventory", "report"], required=True)
    parser.add_argument("--ollama-host", default=os.environ.get("OLLAMA_HOST", "http://xavier:11434"))
    parser.add_argument("--model", default=os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL))
    parser.add_argument("--posts-dir", default="_posts")
    parser.add_argument("--state-dir", default="runner/.state")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-runtime-minutes", type=int, default=None)
    parser.add_argument("--request-timeout-seconds", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--response-retries", type=int, default=1)
    parser.add_argument("--repair-rounds", type=int, default=2)
    parser.add_argument("--repair-max-chars", type=int, default=12_000)
    parser.add_argument("--repair-diff-max-chars", type=int, default=8_000)
    parser.add_argument("--review-max-distance", type=int, default=10)
    parser.add_argument("--review-max-ratio", type=float, default=0.01)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--stage", action="store_true")
    parser.add_argument("--no-stage", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--post")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--stop-on-failure", action="store_true")
    parser.add_argument("--include-missing-state", action="store_true")
    parser.add_argument("--single-pass-max-chars", type=int, default=120_000)
    parser.add_argument("--stalled-stream-timeout-seconds", type=int, default=120)
    parser.add_argument("--ollama-num-ctx", type=int, default=int(os.environ.get("OLLAMA_NUM_CTX", "4096")))
    parser.add_argument("--ollama-num-predict", type=int, default=int(os.environ.get("OLLAMA_NUM_PREDICT", "1536")))
    parser.add_argument("--ollama-num-batch", type=int, default=int(os.environ.get("OLLAMA_NUM_BATCH", "128")))
    parser.add_argument("--ollama-num-gpu", type=int, default=int(os.environ["OLLAMA_NUM_GPU"]) if "OLLAMA_NUM_GPU" in os.environ else None)
    parser.add_argument("--ollama-think", action="store_true")
    parser.add_argument("--replace-stale-lock", action="store_true")
    parser.add_argument("--allow-unrelated-staged", action="store_true")
    args = parser.parse_args(argv)
    for name in ("ollama_num_ctx", "ollama_num_predict", "ollama_num_batch"):
        if getattr(args, name) < 1:
            parser.error(f"--{name.replace('_', '-')} must be greater than 0")
    if args.ollama_num_predict >= args.ollama_num_ctx:
        parser.error("--ollama-num-predict must be smaller than --ollama-num-ctx so the prompt and response fit in one context")
    if args.ollama_num_gpu is not None and args.ollama_num_gpu < 0:
        parser.error("--ollama-num-gpu must be 0 or greater")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be greater than 0")
    if args.response_retries < 0:
        parser.error("--response-retries must be 0 or greater")
    if args.repair_rounds < 0:
        parser.error("--repair-rounds must be 0 or greater")
    if args.repair_max_chars < 1:
        parser.error("--repair-max-chars must be greater than 0")
    if args.repair_diff_max_chars < 1:
        parser.error("--repair-diff-max-chars must be greater than 0")
    if args.review_max_distance < 0:
        parser.error("--review-max-distance must be 0 or greater")
    if not 0 <= args.review_max_ratio <= 1:
        parser.error("--review-max-ratio must be between 0 and 1")
    if args.no_stage:
        args.stage = False
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = Path.cwd().resolve()
    state = RunnerState(ensure_inside(repo_root / args.state_dir, repo_root), write=args.mode in {"next", "batch"})
    try:
        posts = discover_posts(repo_root, Path(args.posts_dir))
        if args.mode == "inventory":
            print_inventory(inventory_summary(posts, state, args))
            return 0
        if args.mode == "report":
            print_report(repo_root, posts, state, args)
            return 0
        return run_next_or_batch(repo_root, posts, state, args)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130
    except RunnerError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code


def logged_main(argv: list[str] | None = None) -> int:
    log_path = Path.cwd().resolve() / "runner" / "last_run.log"
    with RunOutputLog(log_path):
        return main(argv)


if __name__ == "__main__":
    raise SystemExit(logged_main())
