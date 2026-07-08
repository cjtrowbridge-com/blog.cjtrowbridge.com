# WordPress Cleanup Runner

This directory contains local automation for cleaning imported WordPress Markdown posts with an Ollama instance on the LAN.

Run commands from the repository root.

## Requirements

- Ollama reachable at `http://xavier:11434` unless `--ollama-host` is supplied.
- The default `qwen3.5:9b` model installed on that Ollama host, or another model supplied through `OLLAMA_MODEL` or `--model`.
- Python 3 with the standard library.
- A clean or runner-owned staged worktree before mutating runs that use `--stage`.

The runner never commits or pushes.

Generated state is written under `runner/.state/`, which is ignored by Git and excluded from Jekyll.

## First Test

```powershell
python runner/clean_wordpress_posts.py --mode inventory
python runner/clean_wordpress_posts.py --mode next --dry-run
```

Expected result:

- `inventory` prints counts for `wordpress`, `markdown`, missing, malformed, failed-skipped, and eligible posts.
- `next --dry-run` selects one eligible `conversion_state: wordpress` post, calls Ollama, saves response/candidate/patch/report artifacts under `runner/.state/`, validates the candidate, and leaves the post file unchanged.

## One-Post Apply Test

```powershell
python runner/clean_wordpress_posts.py --mode next --stage
```

Expected result:

- Exactly one eligible post is attempted.
- Exact visible-text matches are marked `conversion_state: markdown`.
- Small visible-text differences within the configured thresholds are marked `conversion_state: review` and staged for human review.
- If validation fails, the post remains unchanged and `conversion_state: wordpress`.
- The process exits nonzero when the selected post fails.

## Batch Mode

```powershell
python runner/clean_wordpress_posts.py --mode batch --limit 25 --stage
```

Expected result:

- Up to 25 eligible posts are attempted in deterministic order.
- Safe iframe-wrapper and empty-media cleanup is attempted deterministically before Ollama.
- Per-post cleanup or validation failures are recorded and skipped by default.
- Successful validated posts are updated and staged.
- The batch exits `0` if the runner itself remained healthy, even when individual posts failed.

For debugging, stop at the first failed post:

```powershell
python runner/clean_wordpress_posts.py --mode batch --limit 25 --stop-on-failure --stage
```

## Progress Output

Mutating modes print and immediately flush progress throughout the run. Every line includes:

- Total elapsed time as `HH:MM:SS`.
- Completed attempts divided by the effective run limit.
- Estimated time remaining based on the average duration of completed attempts.
- The current phase and post path when applicable.

ETA is `unavailable` until the first attempt completes. The effective limit is the number of posts selected for this run, so `--limit 100` reports `0/37` when only 37 posts are eligible. During generation, the runner emits a streaming heartbeat approximately every 15 seconds with the number of response characters received.

Representative output:

```text
[elapsed=00:00:00 progress=0/? eta=unavailable] phase=health_check host=http://xavier:11434 model=qwen3.5:9b
[elapsed=00:00:01 progress=0/10 eta=unavailable] phase=post_started position=1/10 post=_posts/2009-02-23-kindred.md
[elapsed=00:00:16 progress=0/10 eta=unavailable] phase=ollama_streaming response_chars=642 post=_posts/2009-02-23-kindred.md
[elapsed=00:01:20 progress=1/10 eta=00:11:51] phase=complete result=SUCCESS post=_posts/2009-02-23-kindred.md attempt=00:01:19 successes=1 failures=0
```

Failures print the exact attempt and report artifact paths. Progress output is enabled by default; `--verbose` remains accepted for command compatibility.

## Last-Run Log

Every invocation deletes and recreates `runner/last_run.log` before parsing arguments. All stdout and stderr are written to that file and still printed to the console. Output is flushed immediately so the file can be monitored while a batch runs.

```powershell
Get-Content runner/last_run.log -Wait
```

The file contains only the latest invocation and is ignored by Git. Starting another runner command replaces the prior contents, including when the new command uses `inventory` or `report`.

## Ollama Memory Options

The runner sends explicit Ollama generation options so hosted models do not inherit a large default context window. Defaults are:

- Host: `http://xavier:11434`
- Model: `qwen3.5:9b`
- `--ollama-num-ctx 4096`
- `--ollama-num-predict 1536`
- `--ollama-num-batch 128`
- `think: false`

`OLLAMA_HOST` and `OLLAMA_MODEL` override the built-in host and model defaults. Explicit `--ollama-host` and `--model` flags override the environment.

`--ollama-num-predict` must be smaller than `--ollama-num-ctx` so the prompt and response fit in one context. If Ollama logs show `context limit hit - shifting`, lower `--ollama-num-predict` or raise `--ollama-num-ctx`.

Use a smaller context for constrained tests:

```powershell
python runner/clean_wordpress_posts.py --mode next --dry-run --ollama-num-ctx 2048 --ollama-num-predict 768 --ollama-num-batch 64
```

If the Ollama logs show excessive GPU graph allocation, reduce `--ollama-num-ctx` first. `--ollama-num-gpu N` can be supplied for model-specific GPU layer tuning when needed.

Reasoning mode is disabled by default in the request body so thinking models return visible cleaned Markdown instead of spending the output budget on hidden reasoning. Supply `--ollama-think` only for debugging model behavior.

Responses are wrapped in nonce-delimited markers. The runner rejects responses that omit or alter the cleaned-body markers, writes the raw response under `runner/.state/responses/`, and leaves the post unchanged. If a response contains exactly one valid cleaned-body block but omits the cleanup report block, the runner synthesizes a report and still sends the candidate through local validation.

## Repair Pipeline

Each post runs through a bounded pipeline:

1. Deterministic cleanup simplifies iframe attributes while preserving `src`, removes iframe-only layout wrappers and empty source-less video tags, restores provable typography/encoding drift from the original, separates existing media blocks from prose, and wraps oversized prose lines without changing visible text.
2. If deterministic cleanup does not finish the post, the normal AGX cleanup prompt runs from the original body.
3. A non-exact or invalid candidate is sent to a classification prompt.
4. The classifier selects `formatting_fix`, `minor_text_fix`, `substantive_change`, `retry_main`, or `blocked`.
5. Formatting, substantive-change, and retry decisions use separate repair prompts and are revalidated locally.
6. The cycle stops after `--repair-rounds` or as soon as the candidate validates exactly.

Defaults:

- `--repair-rounds 2`
- `--repair-max-chars 12000`
- `--repair-diff-max-chars 8000`

Use `--repair-rounds 0` to reproduce the original single-pass behavior. A `minor_text_fix` remains `conversion_state: review`; AGX classification never promotes nonzero text changes directly to `markdown`. Pipeline decisions and reports are saved with the normal attempt artifacts.

## Safety Model

The runner does not send YAML front matter to Ollama. It sends only the post body, preserves the complete original front matter locally, and adds only runner-owned state and Levenshtein audit fields after validation.

The runner canonicalizes visible body text by decoding entities, stripping HTML and Markdown formatting syntax, ignoring recognized WordPress shortcode tags, and removing whitespace. Text enclosed by shortcodes remains part of the comparison. Shortcode tags are also omitted before URL comparison so escaped closing tags do not create false URL changes; URLs and media targets outside shortcode tags remain protected. It compares canonical strings directly and calculates bounded Levenshtein distance only when they differ.

Every applied post receives deterministic audit fields:

```yaml
cleanup_levenshtein_distance: 0
cleanup_levenshtein_ratio: 0.00000000
cleanup_review_required: false
```

Candidates are rejected when they:

- Exceed either conservative review control: `--review-max-distance 10` or `--review-max-ratio 0.01`.
- Add, remove, or duplicate URLs, image targets, or embed targets.
- Change linked-image relationships or add/remove emphasis spans.
- Leave deterministic export artifacts such as center wrappers, editor fragments, or empty source-less video tags.
- Change front matter outside runner-owned state and Levenshtein audit fields.
- Add enough visible text, including image alt text, to exceed the review thresholds.

Both review thresholds must pass for a nonzero candidate to enter `conversion_state: review`; otherwise it is rejected. Exact distance-zero candidates enter `conversion_state: markdown`.

Imported Instagram posts are handled deterministically without an Ollama call: the existing Markdown body is preserved, the final newline is normalized, and `conversion_state` is updated after validation.

Malformed Ollama response envelopes are retried once by default. Use `--response-retries N` to change that bounded retry count. A missing cleanup report block is not treated as malformed when the cleaned-body block is present exactly once; validation remains the authority for whether the candidate can be applied.

## Reports

```powershell
python runner/clean_wordpress_posts.py --mode report
```

Expected result:

- Summarizes attempts, successes, failures, skipped posts, remaining eligible posts, and staged files.
- Separates runner-owned staged post files from unrelated staged files.
- Prints a separate `Last Run` section with the selected, attempted, successful, and failed counts for the latest invocation.
- Lists `conversion_state: review` posts from highest to lowest Levenshtein distance.

## Resume Behavior

The primary resume signal is post front matter:

- `conversion_state: markdown` means complete.
- `conversion_state: review` means applied and excluded from reruns until a human approves or reverts it. Approval changes the state to `markdown` and `cleanup_review_required` to `false` while retaining distance and ratio.
- `conversion_state: wordpress` means eligible, unless a previous failed attempt is skipped by retry policy.
- Missing `conversion_state` is reported and skipped by default.

To retry failed posts:

```powershell
python runner/clean_wordpress_posts.py --mode batch --retry-failed --limit 10 --stage
```

To retry only one failure class:

```powershell
python runner/clean_wordpress_posts.py --mode batch --retry-failed --failure-class long_lines --limit 10 --stage
```

Failure reports include `failure_class` and `recommended_next_action`. `--mode report` prints aggregate failure-class counts so the next retry can focus on one class without disturbing review-state posts.

To include posts missing `conversion_state`:

```powershell
python runner/clean_wordpress_posts.py --mode batch --include-missing-state --limit 10 --stage
```

## Lock Recovery

Mutating modes use `runner/.state/runner.lock`.

If a prior run crashed, inspect `runner/.state/runner.lock`. If it is stale and you want to replace it:

```powershell
python runner/clean_wordpress_posts.py --mode batch --replace-stale-lock --limit 10 --stage
```

## Large Posts

The initial runner processes post bodies that fit within `--single-pass-max-chars` and skips larger bodies with a report. Front matter does not consume the model context. This avoids unsafe partial edits until chunked cleanup has been validated.

```powershell
python runner/clean_wordpress_posts.py --mode batch --single-pass-max-chars 180000 --limit 5 --stage
```
