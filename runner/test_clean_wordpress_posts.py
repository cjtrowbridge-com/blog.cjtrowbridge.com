import contextlib
import io
import unittest
from pathlib import Path
from unittest import mock

from runner.clean_wordpress_posts import (
    FrontMatter,
    PostInfo,
    ProgressReporter,
    RunnerLock,
    format_duration,
    parse_args,
    select_run_candidates,
)


def post(name: str) -> PostInfo:
    return PostInfo(Path(name), name, FrontMatter("", "", "", {}, "wordpress"))


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
        self.assertIn("successes=1 failures=0", lines[1])

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
        self.assertIn("successes=0 failures=1", line)

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
            self.assertEqual(parse_args(["--mode", "inventory"]).model, "qwen3.5:9b")
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


if __name__ == "__main__":
    unittest.main()
