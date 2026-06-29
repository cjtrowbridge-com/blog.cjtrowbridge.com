import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from runner.clean_wordpress_posts import (
    FrontMatter,
    PostInfo,
    ProgressReporter,
    RunOutputLog,
    RunnerLock,
    RunnerState,
    bounded_levenshtein,
    canonical_visible_text,
    format_duration,
    is_instagram_post,
    parse_args,
    parse_front_matter,
    process_post,
    rebuild_post_with_body,
    request_cleaned_body,
    select_run_candidates,
    validate_candidate,
)


def post(name: str) -> PostInfo:
    return PostInfo(Path(name), name, FrontMatter("", "", "", {}, "wordpress"))


def full_post(body: str, extra_front_matter: str = "") -> str:
    return (
        "---\n"
        "title: Test Post\n"
        f"{extra_front_matter}"
        "conversion_state: wordpress\n"
        "---\n\n"
        f"{body}\n"
    )


class ProgressOutputTests(unittest.TestCase):
    def test_format_duration_supports_long_runs(self) -> None:
        self.assertEqual(format_duration(93784.9), "26:03:04")

    def test_eta_is_unavailable_until_first_attempt_finishes(self) -> None:
        output = io.StringIO()
        with mock.patch(
            "runner.clean_wordpress_posts.time.monotonic",
            side_effect=[100.0, 100.0, 110.0],
        ):
            reporter = ProgressReporter()
            reporter.set_total(4)
            with contextlib.redirect_stdout(output):
                reporter.log("phase=run_started")
                reporter.finish_post("_posts/example.md", "success", 20.0)

        lines = output.getvalue().splitlines()
        self.assertIn("progress=0/4 eta=unavailable", lines[0])
        self.assertIn("progress=1/4 eta=00:01:00", lines[1])
        self.assertIn("successes=1 reviews=0 failures=0", lines[1])

    def test_effective_limit_uses_selected_candidate_count(self) -> None:
        candidates = [post(f"_posts/{index}.md") for index in range(3)]
        self.assertEqual(len(select_run_candidates(candidates, "batch", None)), 3)
        self.assertEqual(len(select_run_candidates(candidates, "batch", 100)), 3)
        self.assertEqual(len(select_run_candidates(candidates, "batch", 2)), 2)
        self.assertEqual(len(select_run_candidates(candidates, "next", None)), 1)

    def test_failure_updates_counts_and_eta(self) -> None:
        output = io.StringIO()
        with mock.patch(
            "runner.clean_wordpress_posts.time.monotonic",
            side_effect=[100.0, 105.0],
        ):
            reporter = ProgressReporter()
            reporter.set_total(2)
            with contextlib.redirect_stdout(output):
                reporter.finish_post("_posts/failure.md", "failure", 30.0)

        line = output.getvalue()
        self.assertIn("progress=1/2 eta=00:00:30", line)
        self.assertIn("result=FAILURE", line)
        self.assertIn("successes=0 reviews=0 failures=1", line)

    def test_dead_local_process_makes_lock_stale_immediately(self) -> None:
        state = mock.Mock()
        state.state_dir = Path("runner/.state")
        lock = RunnerLock(state, mock.Mock())
        metadata = {
            "hostname": "test-host",
            "pid": 1234,
            "heartbeat_at": "2099-01-01T00:00:00+00:00",
        }
        with (
            mock.patch("runner.clean_wordpress_posts.socket.gethostname", return_value="test-host"),
            mock.patch("runner.clean_wordpress_posts.process_exists", return_value=False),
        ):
            self.assertTrue(lock._is_stale(metadata))

    def test_model_default_and_override_precedence(self) -> None:
        with mock.patch.dict("runner.clean_wordpress_posts.os.environ", {}, clear=True):
            defaults = parse_args(["--mode", "inventory"])
            self.assertEqual(defaults.model, "qwen3.5:9b")
            self.assertEqual(defaults.review_max_distance, 25)
            self.assertEqual(defaults.review_max_ratio, 0.01)
        with mock.patch.dict(
            "runner.clean_wordpress_posts.os.environ",
            {"OLLAMA_MODEL": "environment-model"},
            clear=True,
        ):
            self.assertEqual(parse_args(["--mode", "inventory"]).model, "environment-model")
            self.assertEqual(
                parse_args(["--mode", "inventory", "--model", "cli-model"]).model,
                "cli-model",
            )

    def test_last_run_log_replaces_and_tees_both_streams_immediately(self) -> None:
        console_out = io.StringIO()
        console_err = io.StringIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "last_run.log"
            log_path.write_text("old output\n", encoding="utf-8")
            with (
                mock.patch.object(sys, "stdout", console_out),
                mock.patch.object(sys, "stderr", console_err),
                RunOutputLog(log_path),
            ):
                print("stdout message")
                print("stderr message", file=sys.stderr)
                live_log = log_path.read_text(encoding="utf-8")
                self.assertIn("stdout message", live_log)
                self.assertIn("stderr message", live_log)
                self.assertNotIn("old output", live_log)

            self.assertEqual(console_out.getvalue(), "stdout message\n")
            self.assertEqual(console_err.getvalue(), "stderr message\n")

    def test_last_run_log_captures_unhandled_exception_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "last_run.log"
            with self.assertRaisesRegex(ValueError, "test failure"):
                with RunOutputLog(log_path):
                    raise ValueError("test failure")
            self.assertIn("ValueError: test failure", log_path.read_text(encoding="utf-8"))

    def test_rebuild_preserves_all_front_matter_except_conversion_state(self) -> None:
        original = full_post(
            "<div>Exact authored text.</div>",
            "custom_serialized_value: 'a:1:{s:3:\"url\";s:18:\"http://example.com\";}'\n",
        )
        candidate = rebuild_post_with_body(original, "Exact authored text.")
        self.assertIn(
            "custom_serialized_value: 'a:1:{s:3:\"url\";s:18:\"http://example.com\";}'",
            candidate,
        )
        self.assertIn("conversion_state: markdown", candidate)
        self.assertNotIn("conversion_state: wordpress", candidate)
        self.assertTrue(validate_candidate(original, candidate, False).ok)

    def test_batch_regression_candidates_are_classified(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "unsafe_candidates.json"
        fixtures = json.loads(fixture_path.read_text(encoding="utf-8"))
        for fixture in fixtures:
            with self.subTest(fixture["name"]):
                original = full_post(fixture["original_body"])
                candidate = rebuild_post_with_body(original, fixture["candidate_body"])
                result = validate_candidate(original, candidate, False)
                if fixture.get("expected_review"):
                    self.assertTrue(result.ok, result.failures)
                    self.assertTrue(result.review_required)
                    self.assertGreater(result.checks["levenshtein_distance"], 0)
                else:
                    self.assertFalse(result.ok)
                    self.assertTrue(
                        any(fixture["expected_failure"] in failure for failure in result.failures),
                        result.failures,
                    )

    def test_visible_text_ignores_html_and_whitespace(self) -> None:
        original = "<div>Hello&nbsp; world.</div>"
        candidate = "Hello\n\nworld."
        self.assertEqual(canonical_visible_text(original), canonical_visible_text(candidate))
        self.assertEqual(
            bounded_levenshtein(
                canonical_visible_text(original),
                canonical_visible_text(candidate),
                25,
            ),
            0,
        )

    def test_bounded_levenshtein_stops_after_limit(self) -> None:
        self.assertEqual(bounded_levenshtein("abcdef", "abcxef", 2), 1)
        self.assertEqual(bounded_levenshtein("abc", "", 3), 3)
        self.assertIsNone(bounded_levenshtein("a" * 100, "b" * 100, 5))

    def test_bounded_levenshtein_matches_reference_distances(self) -> None:
        def reference(left: str, right: str) -> int:
            row = list(range(len(right) + 1))
            for left_index, left_character in enumerate(left, start=1):
                next_row = [left_index]
                for right_index, right_character in enumerate(right, start=1):
                    next_row.append(
                        min(
                            row[right_index] + 1,
                            next_row[right_index - 1] + 1,
                            row[right_index - 1] + (left_character != right_character),
                        )
                    )
                row = next_row
            return row[-1]

        pairs = [
            ("", ""),
            ("a", ""),
            ("kitten", "sitting"),
            ("abcdef", "abqdef"),
            ("same", "same"),
        ]
        for left, right in pairs:
            distance = reference(left, right)
            for limit in range(5):
                expected = distance if distance <= limit else None
                self.assertEqual(bounded_levenshtein(left, right, limit), expected)

    def test_review_metadata_is_written_deterministically(self) -> None:
        candidate = rebuild_post_with_body(
            full_post("Original text."),
            "Original text!",
            conversion_state="review",
            levenshtein_distance=1,
            levenshtein_ratio=0.076923,
            review_required=True,
        )
        self.assertIn("conversion_state: review", candidate)
        self.assertIn("cleanup_levenshtein_distance: 1", candidate)
        self.assertIn("cleanup_levenshtein_ratio: 0.07692300", candidate)
        self.assertIn("cleanup_review_required: true", candidate)

    def test_instagram_detection_uses_front_matter(self) -> None:
        front_matter = FrontMatter(
            "",
            "",
            "",
            {"categories": "categories:\n    - Instagram\n"},
            "wordpress",
        )
        self.assertTrue(is_instagram_post(front_matter))

    def test_response_envelope_is_retried_once(self) -> None:
        state = mock.Mock()
        progress = mock.Mock()
        args = SimpleNamespace(response_retries=1, model="test-model")
        valid_response = (
            "BEGIN_CLEANED_BODY 12345678\nText.\nEND_CLEANED_BODY 12345678\n"
            "BEGIN_CLEANUP_REPORT 12345678\ncomplete: true\n"
            "END_CLEANUP_REPORT 12345678\n"
        )
        fake_digest = mock.Mock()
        fake_digest.hexdigest.return_value = "1234567890abcdef"
        with (
            mock.patch("runner.clean_wordpress_posts.hashlib.sha1", return_value=fake_digest),
            mock.patch(
                "runner.clean_wordpress_posts.call_ollama_with_retries",
                side_effect=["malformed", valid_response],
            ) as generate,
        ):
            cleaned, _, complete, _, response_attempt = request_cleaned_body(
                "_posts/test.md",
                "Text.",
                state,
                args,
                progress,
            )
        self.assertEqual(generate.call_count, 2)
        self.assertEqual(cleaned, "Text.\n")
        self.assertTrue(complete)
        self.assertEqual(response_attempt, 2)

    def test_per_run_manifest_tracks_only_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state = RunnerState(Path(temp_dir), write=True)
            args = SimpleNamespace(
                mode="batch",
                dry_run=True,
                stage=False,
                retry_failed=True,
                limit=10,
            )
            candidate = post("_posts/test.md")
            run = state.start_run(args, [candidate])
            state.save_attempt(candidate.rel_path, {"status": "dry_run_validated"})
            state.record_run_attempt(run, candidate.rel_path, "success", 12.5)
            state.finish_run(run, "completed")
            saved = state.load_last_run()
            self.assertIsNotNone(saved)
            self.assertEqual(saved["selected_count"], 1)
            self.assertEqual(saved["attempted"], 1)
            self.assertEqual(saved["successes"], 1)
            self.assertEqual(saved["reviews"], 0)
            self.assertEqual(saved["failures"], 0)
            self.assertEqual(saved["status"], "completed")

    def test_process_post_writes_review_yaml_for_small_visible_change(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "unsafe_candidates.json"
        fixture = json.loads(fixture_path.read_text(encoding="utf-8"))[0]
        original = full_post(fixture["original_body"])
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            post_path = repo_root / "_posts" / "test.md"
            post_path.parent.mkdir()
            post_path.write_text(original, encoding="utf-8")
            post_info = PostInfo(
                post_path,
                "_posts/test.md",
                parse_front_matter(original),
            )
            state = RunnerState(repo_root / "runner" / ".state", write=True)
            args = SimpleNamespace(
                single_pass_max_chars=120_000,
                model="test-model",
                ollama_host="http://example.invalid",
                ollama_num_ctx=4096,
                ollama_num_predict=1536,
                ollama_num_batch=128,
                ollama_num_gpu=None,
                ollama_think=False,
                response_retries=1,
                include_missing_state=False,
                review_max_distance=25,
                review_max_ratio=0.01,
                dry_run=True,
                stage=False,
            )
            with (
                mock.patch(
                    "runner.clean_wordpress_posts.git_unstaged_for_path",
                    return_value=False,
                ),
                mock.patch(
                    "runner.clean_wordpress_posts.request_cleaned_body",
                    return_value=(
                        fixture["candidate_body"],
                        "complete: true\n",
                        True,
                        1.0,
                        1,
                    ),
                ),
            ):
                result = process_post(
                    repo_root,
                    post_info,
                    state,
                    args,
                    None,
                    mock.Mock(),
                )
            self.assertEqual(result, "review")
            self.assertEqual(post_path.read_text(encoding="utf-8"), original)
            candidate_path = (
                state.candidates_dir / f"{state.attempt_id(post_info.rel_path)}.md"
            )
            candidate = candidate_path.read_text(encoding="utf-8")
            self.assertIn("conversion_state: review", candidate)
            self.assertIn("cleanup_levenshtein_distance: 1", candidate)
            self.assertIn("cleanup_review_required: true", candidate)


if __name__ == "__main__":
    unittest.main()
