---
plan_id: 2026-06-25-18-48-50_build-agx-wordpress-cleanup-runner
title: Build AGX WordPress Cleanup Runner
summary: Create a failure-tolerant, resumable Python runner that uses Ollama on xavier to clean imported WordPress posts one at a time, validate and apply cleaned output, and support safe single-post testing.
status: current
created_at: 2026-06-25-18-48-50
---

# Build AGX WordPress Cleanup Runner

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Scope

- Script path: `runner/clean_wordpress_posts.py`.
- Primary model endpoint: Ollama HTTP API at `http://xavier:11434`.
- Target content: Markdown posts under `_posts/`.
- Completion source of truth: each post's `conversion_state` front matter.
- Completed state: `conversion_state: markdown`.
- Pending state: `conversion_state: wordpress`.
- Missing state: missing `conversion_state` must be reported separately and skipped by default unless an explicit implementation flag enables processing missing-state posts.
- Runner state: repo-local state directory at `runner/.state/` for attempts, raw model responses, candidate outputs, validation reports, and generated per-post patches.
- Git behavior: never commit; optionally stage only successfully validated post changes for later human review.
- Execution model: one post at a time, deterministic order, resumable after process crashes or host/network failures.
- Concurrency model: exactly one runner process may own the state directory at a time.

## Required Execution Pattern

The implementation must document and support these commands:

```powershell
python runner/clean_wordpress_posts.py --mode next --stage
python runner/clean_wordpress_posts.py --mode batch --stage
python runner/clean_wordpress_posts.py --mode batch --limit 25 --stage
python runner/clean_wordpress_posts.py --mode batch --limit 25 --stop-on-failure --stage
python runner/clean_wordpress_posts.py --mode inventory
python runner/clean_wordpress_posts.py --mode report
```

`--mode next` is the required test mode. It must select the next eligible `conversion_state: wordpress` post, attempt exactly one post, apply and stage that post only if validation passes, write a report, and exit. If the selected post fails cleanup or validation, `next` must record the failed attempt, leave the post `conversion_state: wordpress`, and exit nonzero.

`--mode batch` is the long-lived mode. It must loop through eligible posts until no posts remain, a configured `--limit` is reached, a configured runtime limit is reached, or the process is interrupted. Per-post cleanup or validation failures must be recorded and skipped by default so one bad response does not stop a week-long run. `--stop-on-failure` must stop after the first per-post failure for debugging.

`--mode inventory` must be read-only. It must report counts for `wordpress`, `markdown`, missing, malformed, skipped, and failed-retry candidates without calling Ollama or editing files.

`--mode report` must be read-only. It must summarize previous runner state, successful patches, failed attempts, validation failures, and remaining eligible posts.

## Plan

- [x] 1. Define the automation contract.
  - [x] 1.1 Confirm implementation constraints from the WordPress cleanup playbook.
    - [x] 1.1.1 Preserve meaning, wording, metadata, permalinks, links, citations, images, embeds, and source order.
    - [x] 1.1.2 Mark a post `conversion_state: markdown` only after cleanup, reread, structural validation, and repair pass complete.
    - [x] 1.1.3 Leave `conversion_state: wordpress` when cleanup is incomplete, uncertain, or validation fails.
    - [-] 1.1.4 Require moving-window cleanup for posts too large to send safely in one prompt. Closed for first checkpoint; oversized posts are skipped with reports instead of partially edited.
    - [x] 1.1.5 Require structural sweeps over first body lines, tail body lines, section labels, raw wrappers, images, embeds, and headings.
  - [x] 1.2 Define non-goals for the first implementation checkpoint.
    - [x] 1.2.1 Do not rewrite author voice or summarize posts.
    - [x] 1.2.2 Do not commit or push generated post changes.
    - [x] 1.2.3 Do not process files outside `_posts/`.
    - [x] 1.2.4 Do not trust model-generated shell commands or apply arbitrary model-supplied patch commands.
  - [x] 1.3 Define explicit safety boundaries.
    - [x] 1.3.1 The runner may write target post files only after validation passes.
    - [x] 1.3.2 The runner may write only its configured state directory before validation passes.
    - [x] 1.3.3 The runner must refuse to process a target post with unexpected uncommitted changes unless an explicit override is supplied.
    - [x] 1.3.4 The runner must never modify files whose final resolved path is outside the repository root.
    - [x] 1.3.5 The runner must never commit or push changes.
    - [x] 1.3.6 The runner must refuse to start when another active runner lock is present.
    - [x] 1.3.7 The runner must allow safe resume when prior staged post files match runner-owned successful attempts.

- [x] 2. Design the Python script interface.
  - [x] 2.1 Implement `argparse` command-line options.
    - [x] 2.1.1 Add required `--mode` choices: `next`, `batch`, `inventory`, and `report`.
    - [x] 2.1.2 Add `--ollama-host` with default from `OLLAMA_HOST`, falling back to `http://xavier:11434`.
    - [x] 2.1.3 Add `--model` with default `qwen3.5:9b`, allow `OLLAMA_MODEL` to override that default, and allow the CLI flag to override both.
    - [x] 2.1.4 Add `--posts-dir` defaulting to `_posts`.
    - [x] 2.1.5 Add `--state-dir` defaulting to `runner/.state`.
    - [x] 2.1.6 Add `--limit` for maximum attempted posts in a run.
    - [x] 2.1.7 Add `--max-runtime-minutes` for long-lived batch runs.
    - [x] 2.1.8 Add `--request-timeout-seconds` for Ollama HTTP calls.
    - [x] 2.1.9 Add `--max-retries` for transient Ollama/network failures.
    - [x] 2.1.10 Add `--retry-failed` to revisit previously failed posts.
    - [x] 2.1.11 Add `--stage` to stage successfully cleaned posts.
    - [x] 2.1.12 Add `--no-stage` to force no staging even if a config default later enables staging.
    - [x] 2.1.13 Add `--dry-run` to call validation/reporting without writing target post files.
    - [x] 2.1.14 Add `--post` to target one explicit post path for debugging.
    - [x] 2.1.15 Add `--verbose` for detailed progress logging.
    - [x] 2.1.16 Add `--stop-on-failure` so batch mode stops after the first per-post cleanup or validation failure.
    - [x] 2.1.17 Add `--include-missing-state` to opt in to processing posts without `conversion_state`.
    - [x] 2.1.18 Add `--single-pass-max-chars` to define when a post must use moving-window mode.
    - [x] 2.1.19 Add `--stalled-stream-timeout-seconds` to stop stalled Ollama streams.
    - [x] 2.1.20 Add `--replace-stale-lock` to explicitly replace a stale runner lock after reporting its metadata.
    - [x] 2.1.21 Add `--allow-unrelated-staged` for deliberate resume/testing scenarios where unrelated staged files already exist.
    - [x] 2.1.22 Add `--ollama-num-ctx`, `--ollama-num-predict`, `--ollama-num-batch`, and `--ollama-num-gpu` to bound hosted model memory allocation.
    - [x] 2.1.23 Reject `--ollama-num-predict` values greater than or equal to `--ollama-num-ctx` so generation does not fill the entire context window.
    - [x] 2.1.24 Add `--ollama-think` so reasoning mode can be explicitly enabled while default requests keep `think: false`.
  - [x] 2.2 Define exit codes.
    - [x] 2.2.1 Return `0` when the requested mode completes without runner errors.
    - [x] 2.2.2 In `--mode next`, return `1` when the selected post fails validation or cleanup but the runner remains healthy.
    - [x] 2.2.3 In `--mode batch`, continue after per-post failures by default and return `0` if the runner itself stayed healthy and all configured stop conditions were handled.
    - [x] 2.2.4 In `--mode batch --stop-on-failure`, return `1` when the first per-post cleanup or validation failure stops the run.
    - [x] 2.2.5 Always report per-post failure counts in output and state, even when batch mode exits `0`.
    - [x] 2.2.6 Return `2` when configuration, path safety, lock acquisition, or dirty-worktree preflight fails.
    - [x] 2.2.7 Return `3` when Ollama is unreachable after configured retries.
    - [x] 2.2.8 Return `130` on keyboard interrupt after writing final state.

- [x] 3. Implement post inventory and selection.
  - [x] 3.1 Discover candidate files deterministically.
    - [x] 3.1.1 Recursively list `*.md` files under `_posts/`.
    - [x] 3.1.2 Sort candidate paths by filename date prefix, then path.
    - [x] 3.1.3 Resolve every path and reject paths outside the repository root.
  - [x] 3.2 Parse front matter.
    - [x] 3.2.1 Split YAML front matter from body without altering content.
    - [x] 3.2.2 Parse required metadata fields into a stable metadata object.
    - [x] 3.2.3 Detect `conversion_state: wordpress`.
    - [x] 3.2.4 Detect `conversion_state: markdown`.
    - [x] 3.2.5 Detect missing `conversion_state` and classify it separately before any edits.
    - [x] 3.2.6 Detect malformed front matter and skip with a report.
  - [x] 3.3 Select the next eligible post.
    - [x] 3.3.1 In `--mode next`, choose at most one eligible post.
    - [x] 3.3.2 In `--mode batch`, choose eligible posts until stop conditions are met.
    - [x] 3.3.3 Skip `conversion_state: markdown` posts without consulting runner state.
    - [x] 3.3.4 Skip failed posts unless `--retry-failed` is set or retry policy allows another attempt.
    - [x] 3.3.5 If `--post` is supplied, validate that the explicit post is inside `_posts/` and not already `markdown`.
    - [x] 3.3.6 Skip missing-state posts by default.
    - [x] 3.3.7 If `--include-missing-state` is supplied, treat missing-state posts as eligible but require the final candidate to add `conversion_state: markdown` only after all validation gates pass.
    - [x] 3.3.8 If a missing-state post fails cleanup or validation, leave the original file unchanged and record the failure without adding `conversion_state`.
  - [x] 3.4 Add read-only inventory reporting.
    - [x] 3.4.1 Count `wordpress` posts.
    - [x] 3.4.2 Count `markdown` posts.
    - [x] 3.4.3 Count missing `conversion_state` posts.
    - [x] 3.4.4 Count malformed front matter posts.
    - [x] 3.4.5 Count posts skipped because of runner failure state.
    - [x] 3.4.6 Print the next eligible post path.

- [x] 4. Implement runner state and crash recovery.
  - [x] 4.1 Create a state directory layout.
    - [x] 4.1.1 Store append-only event logs as JSON Lines.
    - [x] 4.1.2 Store one per-post attempt metadata file keyed by a sanitized relative path or content hash.
    - [x] 4.1.3 Store raw Ollama responses for failed and successful attempts.
    - [x] 4.1.4 Store candidate cleaned files before applying them.
    - [x] 4.1.5 Store generated unified diffs for successful candidates.
    - [x] 4.1.6 Store validation reports for every attempt.
    - [x] 4.1.7 Store a runner-owned staged-file manifest for successful attempts staged with `--stage`.
    - [-] 4.1.8 Store chunk manifests for moving-window runs, including original line ranges, overlap ranges, and per-chunk hashes. Closed for first checkpoint because oversized posts are skipped.
  - [x] 4.2 Implement a single-runner lock.
    - [x] 4.2.1 Create `runner/.state/runner.lock` when a mutating mode starts.
    - [x] 4.2.2 Record PID, hostname, repo root, start time, command line, and heartbeat time in the lock.
    - [x] 4.2.3 Refuse to start a mutating mode when a live lock exists.
    - [x] 4.2.4 Detect stale locks and require an explicit override before replacing them.
    - [x] 4.2.5 Remove the lock on clean shutdown.
    - [x] 4.2.6 Leave enough lock metadata to diagnose interrupted runs.
    - [x] 4.2.7 Treat a lock owned by a dead PID on the local host as stale immediately instead of waiting for heartbeat age.
  - [x] 4.3 Make `conversion_state` the primary resume mechanism.
    - [x] 4.3.1 On startup, rescan `_posts/` instead of trusting prior state.
    - [x] 4.3.2 Treat any post now marked `markdown` as complete even if the runner state is missing.
    - [x] 4.3.3 Treat any post still marked `wordpress` as eligible unless retry policy says to skip it temporarily.
    - [x] 4.3.4 Reconcile runner state against actual front matter before selecting the next post.
  - [x] 4.4 Record per-post attempt lifecycle events.
    - [x] 4.4.1 Record `selected` before any model call.
    - [x] 4.4.2 Record original file SHA-256 before any model call.
    - [x] 4.4.3 Record `ollama_request_started`.
    - [x] 4.4.4 Record `ollama_request_failed` with error type and retry count.
    - [x] 4.4.5 Record `candidate_received` with candidate SHA-256.
    - [x] 4.4.6 Record `validation_failed` with failed checks.
    - [x] 4.4.7 Record `applied` after atomic file replacement succeeds.
    - [x] 4.4.8 Record `staged` after `git add` succeeds when `--stage` is enabled.
    - [x] 4.4.9 Record `skipped_after_failure` when batch mode skips a failed post and continues.
  - [x] 4.5 Make writes crash-tolerant.
    - [x] 4.5.1 Write state files through temporary files and atomic replace operations.
    - [x] 4.5.2 Write target post changes through a temporary file and atomic replace operation.
    - [x] 4.5.3 Never modify the target post while an Ollama request is in progress.
    - [x] 4.5.4 On startup, detect abandoned in-progress markers and reconcile them with actual file front matter.
    - [x] 4.5.5 On keyboard interrupt, finish the current state write and stop before selecting another post.

- [x] 5. Implement Ollama client behavior for `xavier`.
  - [x] 5.1 Add an Ollama HTTP client using Python standard library or a minimal dependency already accepted by the repo.
    - [x] 5.1.1 Call the Ollama generate or chat endpoint at the configured host.
    - [x] 5.1.2 Support configurable model name.
    - [x] 5.1.3 Set deterministic generation parameters where supported.
    - [x] 5.1.4 Use request timeouts.
    - [x] 5.1.5 Retry transient network errors with bounded backoff.
    - [x] 5.1.6 Fail clearly when hostname `xavier` cannot be resolved or the Ollama API is unavailable.
    - [x] 5.1.7 Prefer streaming Ollama responses so long generations produce progress and can be interrupted cleanly.
    - [x] 5.1.8 Treat stalled streaming responses as failures after `--stalled-stream-timeout-seconds`.
    - [x] 5.1.9 Save partial responses for diagnostics when a stream stalls or disconnects.
    - [x] 5.1.10 Send explicit Ollama `num_ctx`, `num_predict`, and `num_batch` options so hosted models do not inherit oversized default context windows.
    - [x] 5.1.11 Default `num_predict` below `num_ctx` after live logs showed `context limit hit - shifting` when both were set to 4096.
    - [x] 5.1.12 Send `think: false` by default after Qwen returned zero visible response characters with capped context/output settings.
  - [x] 5.2 Add health checks.
    - [x] 5.2.1 Check the Ollama host before batch mode starts.
    - [x] 5.2.2 Check that the requested model is available, or report the exact missing model error.
    - [x] 5.2.3 In `--mode next`, fail before selecting a post if the model is unavailable.
  - [x] 5.3 Capture model metadata.
    - [x] 5.3.1 Store host, model, prompt version, and generation parameters in each attempt report.
    - [x] 5.3.2 Store elapsed request time and response size in each attempt report.

- [x] 6. Implement prompt construction from the cleanup playbook.
  - [x] 6.1 Build a stable prompt version.
    - [x] 6.1.1 Include the AGX prompt rules from `playbooks/how_to_clean_wordpress_markdown_posts.md`.
    - [x] 6.1.2 Include the required front matter rule for `conversion_state`.
    - [-] 6.1.3 Include the moving-window protocol. Closed for first checkpoint; oversized posts are skipped with reports.
    - [x] 6.1.4 Include cleanup rules for wrappers, images, embeds, paragraphs, headings, lists, emphasis, references, and citations.
    - [x] 6.1.5 Include the small-model safety loop.
    - [x] 6.1.6 Include the validation checklist.
  - [x] 6.2 Require a machine-parseable response.
    - [x] 6.2.1 Use one exact response envelope for model output, not multiple accepted formats.
    - [x] 6.2.2 Generate a per-request nonce and require the cleaned full-file artifact between `BEGIN_CLEANED_POST <nonce>` and `END_CLEANED_POST <nonce>` markers.
    - [x] 6.2.3 Require the completion report between `BEGIN_CLEANUP_REPORT <nonce>` and `END_CLEANUP_REPORT <nonce>` markers.
    - [x] 6.2.4 Require the report to include `complete: true` or `complete: false`.
    - [x] 6.2.5 Require `complete: false` when the model is uncertain.
    - [x] 6.2.6 Reject responses that omit the full cleaned post artifact.
    - [x] 6.2.7 Reject responses that include more than one cleaned artifact block.
    - [x] 6.2.8 Reject responses whose artifact markers use the wrong nonce.
    - [x] 6.2.9 Treat Markdown code fences inside the cleaned post as content, not as response framing.
    - [x] 6.2.10 Use a short 8-character response nonce after live testing showed the model could truncate longer nonce markers.
  - [-] 6.3 Handle large posts with moving windows. Closed for first checkpoint; large posts are skipped rather than partially edited.
    - [x] 6.3.1 Estimate prompt size before calling Ollama.
    - [x] 6.3.2 For small posts, send the full post in one cleanup request.
    - [-] 6.3.3 For large posts, build a chunk manifest before model calls.
    - [-] 6.3.4 Split the body into ordered chunks at safe Markdown boundaries.
    - [-] 6.3.5 Include source line ranges for every chunk.
    - [-] 6.3.6 Include overlap windows at chunk boundaries.
    - [-] 6.3.7 Include original per-chunk hashes in the state report.
    - [-] 6.3.8 Include running state with each chunk: current section, open structures, references state, and anomalies.
    - [-] 6.3.9 Preserve front matter outside chunk edits.
    - [-] 6.3.10 Reassemble chunks in original order according to the chunk manifest.
    - [-] 6.3.11 Validate chunk seams against the overlap windows before accepting the candidate.
    - [-] 6.3.12 Run a second moving-window reread pass over the reassembled candidate.
    - [-] 6.3.13 Run a repair pass only on validation failures that can be isolated without reordering content.
    - [x] 6.3.14 If large-post chunking cannot be implemented safely in the first script checkpoint, skip oversized posts with a report instead of sending unsafe partial prompts.

- [x] 7. Implement candidate parsing and patch application.
  - [x] 7.1 Parse the model response safely.
    - [x] 7.1.1 Extract the cleaned post artifact.
    - [x] 7.1.2 Extract the completion report.
    - [x] 7.1.3 Reject responses with multiple conflicting cleaned artifacts.
    - [x] 7.1.4 Reject responses that include instructions instead of cleaned content.
    - [x] 7.1.5 Reject responses whose cleaned artifact does not contain valid front matter.
    - [x] 7.1.6 Reject responses whose completion report says `complete: false`.
  - [x] 7.2 Normalize only runner-level formatting.
    - [x] 7.2.1 Preserve original newline convention when practical.
    - [x] 7.2.2 Ensure the candidate ends with exactly one trailing newline.
    - [x] 7.2.3 Do not run broad auto-formatters over post content.
  - [x] 7.3 Compute runner-owned patches.
    - [x] 7.3.1 Diff original post content against cleaned candidate using Python unified diff generation.
    - [x] 7.3.2 Save the generated patch in the state directory.
    - [x] 7.3.3 Treat the saved patch as an audit artifact, not as executable model-supplied code.
  - [x] 7.4 Apply successful candidates.
    - [x] 7.4.1 Re-read the target file before applying and confirm its SHA-256 still matches the original attempt hash.
    - [x] 7.4.2 Refuse to apply if the target file changed during processing.
    - [x] 7.4.3 Write the candidate through an atomic replace.
    - [x] 7.4.4 If `--stage` is enabled, run `git add -- <post path>` only for the successfully applied post.
    - [x] 7.4.5 If staging fails, keep the file change, record `stage_failed`, and exit with a nonzero runner error.

- [x] 8. Implement validation gates.
  - [x] 8.1 Validate front matter preservation.
    - [x] 8.1.1 Confirm `id` is unchanged when present.
    - [x] 8.1.2 Confirm `title` is unchanged when present.
    - [x] 8.1.3 Confirm `date` is unchanged when present.
    - [x] 8.1.4 Confirm `author` is unchanged when present.
    - [x] 8.1.5 Confirm `layout` is unchanged when present.
    - [x] 8.1.6 Confirm `guid` is unchanged when present.
    - [x] 8.1.7 Confirm `permalink` is unchanged when present.
    - [x] 8.1.8 Confirm `categories` is unchanged when present.
    - [x] 8.1.9 Confirm `tags` is unchanged when present.
    - [x] 8.1.10 Confirm `conversion_state` changed to `markdown` only when all validations pass.
  - [x] 8.2 Validate content preservation signals.
    - [x] 8.2.1 Extract URLs from original and candidate.
    - [x] 8.2.2 Normalize comparable URLs before validation, including common HTML entity decoding and harmless surrounding punctuation cleanup.
    - [x] 8.2.3 Fail validation if any normalized original URL is missing from the candidate unless explicitly whitelisted in code.
    - [x] 8.2.4 Extract Markdown image targets and HTML image sources from original and candidate.
    - [x] 8.2.5 Normalize image/media targets before validation.
    - [x] 8.2.6 Fail validation if meaningful image/media targets disappear.
    - [x] 8.2.7 Extract iframe/embed sources from original and candidate.
    - [x] 8.2.8 Normalize iframe/embed sources before validation.
    - [x] 8.2.9 Fail validation if meaningful embed targets disappear.
    - [x] 8.2.10 Maintain a narrow, code-owned allowlist for removable tracking pixels or known export noise.
    - [x] 8.2.11 Include every allowlisted removal in the validation report.
  - [x] 8.3 Validate cleanup structure.
    - [x] 8.3.1 Check for remaining WordPress shell wrappers.
    - [x] 8.3.2 Check for copied UI wrapper HTML.
    - [x] 8.3.3 Count ordinary prose lines over 800 characters, excluding URLs, tables, code blocks, and intentional artifacts.
    - [x] 8.3.4 Check that section labels such as `Works Cited`, `References`, `Bibliography`, `Appendix`, `Footnotes`, `Sources`, and `Term Paper` are not glued to prose.
    - [x] 8.3.5 Check that image and embed blocks are separated from prose by blank lines.
    - [x] 8.3.6 Check that list-like lines still render as lists where detectable.
    - [x] 8.3.7 Check that headings start on their own line.
  - [-] 8.4 Validate moving-window requirements. Closed for first checkpoint because moving-window processing is not enabled yet.
    - [-] 8.4.1 Record whether chunks were used.
    - [-] 8.4.2 Record chunk boundaries.
    - [-] 8.4.3 Validate first body lines after cleanup.
    - [-] 8.4.4 Validate last body lines after cleanup.
    - [-] 8.4.5 Validate every chunk seam after reassembly.
  - [x] 8.5 Produce validation reports.
    - [x] 8.5.1 Write a pass/fail result for every validation gate.
    - [x] 8.5.2 Include the model completion report.
    - [x] 8.5.3 Include counts for fixed artifact types when available.
    - [x] 8.5.4 Include blocker notes when the candidate is rejected.

- [?] 9. Implement dirty-worktree and staging behavior.
  - [x] 9.1 Add git preflight checks.
    - [x] 9.1.1 Detect whether the repository is a git worktree.
    - [x] 9.1.2 Detect existing staged changes.
    - [x] 9.1.3 Detect existing unstaged changes.
    - [x] 9.1.4 Detect untracked files relevant to the runner state directory.
    - [x] 9.1.5 Print a clear warning when a long-lived run will add many staged changes.
    - [x] 9.1.6 Classify staged post files as runner-owned only when they appear in the staged-file manifest and their current hashes match the recorded successful attempt.
    - [x] 9.1.7 Refuse to start mutating modes when unrelated staged changes exist unless an explicit override is supplied.
  - [x] 9.2 Protect unrelated edits.
    - [x] 9.2.1 Before selecting a post, ensure the target post has no unstaged changes unless those changes match an in-progress runner attempt.
    - [x] 9.2.2 Before applying a candidate, compare the current file hash to the original attempt hash.
    - [x] 9.2.3 Refuse to overwrite user edits and record the conflict.
    - [x] 9.2.4 Allow resume with previously staged runner-owned post files without treating them as unrelated dirty state.
  - [x] 9.3 Stage only validated post changes.
    - [x] 9.3.1 If `--stage` is set, stage only the post file that just passed validation.
    - [x] 9.3.2 Do not stage runner state files by default.
    - [x] 9.3.3 Do not stage documentation or script changes during cleanup runs.
    - [x] 9.3.4 Print the exact staged path after each successful post.
  - [x] 9.4 Add review support for many staged files.
    - [x] 9.4.1 In `--mode report`, list staged cleaned posts if git is available.
    - [?] 9.4.2 In `--mode report`, summarize changed posts by year. Needs a follow-up enhancement if staged review becomes too large.
    - [?] 9.4.3 In `--mode report`, summarize largest diffs by line count. Needs a follow-up enhancement if staged review becomes too large.
    - [x] 9.4.4 In `--mode report`, list failed posts separately from staged successes.
    - [x] 9.4.5 In `--mode report`, distinguish runner-owned staged post files from unrelated staged files.

- [x] 10. Implement generated state ignore policy.
  - [x] 10.1 Decide whether runner state should be committed.
    - [x] 10.1.1 Default to keeping `runner/.state/` untracked and ignored.
    - [x] 10.1.2 Preserve optional exported reports that can be copied into tracked docs later if needed.
  - [x] 10.2 Add ignore coverage.
    - [x] 10.2.1 Create `.gitignore` if none exists.
    - [x] 10.2.2 Add `runner/.state/` to `.gitignore`.
    - [x] 10.2.3 Verify the state directory is not staged during normal cleanup runs.

- [ ] 11. Add tests and fixtures.
  - [ ] 11.1 Create representative fixture posts.
    - [ ] 11.1.1 Add a fixture with WordPress wrapper HTML.
    - [ ] 11.1.2 Add a fixture with images and linked images.
    - [ ] 11.1.3 Add a fixture with iframe or embed HTML.
    - [ ] 11.1.4 Add a fixture with long paragraphs.
    - [ ] 11.1.5 Add a fixture with references or works cited end matter.
    - [ ] 11.1.6 Add a fixture with malformed front matter.
  - [ ] 11.2 Add unit tests for inventory.
    - [ ] 11.2.1 Test `wordpress` detection.
    - [ ] 11.2.2 Test `markdown` skipping.
    - [ ] 11.2.3 Test missing `conversion_state` classification.
    - [ ] 11.2.4 Test deterministic post ordering.
    - [ ] 11.2.5 Test that missing-state posts are skipped by default.
    - [ ] 11.2.6 Test that `--include-missing-state` makes missing-state posts eligible.
  - [ ] 11.3 Add unit tests for validation.
    - [ ] 11.3.1 Test metadata preservation checks.
    - [ ] 11.3.2 Test missing URL detection.
    - [ ] 11.3.3 Test missing image target detection.
    - [ ] 11.3.4 Test wrapper detection.
    - [ ] 11.3.5 Test line-length validation.
    - [ ] 11.3.6 Test section-label glue detection.
  - [ ] 11.4 Add unit tests for response parsing.
    - [ ] 11.4.1 Test valid cleaned artifact extraction.
    - [ ] 11.4.2 Test rejection of missing cleaned artifact.
    - [ ] 11.4.3 Test rejection of conflicting artifacts.
    - [ ] 11.4.4 Test rejection of wrong response nonce.
    - [ ] 11.4.5 Test that Markdown code fences inside the cleaned artifact do not break parsing.
    - [ ] 11.4.6 Test rejection of `complete: false` reports.
  - [ ] 11.5 Add unit tests for state and resume behavior.
    - [ ] 11.5.1 Test that `conversion_state: markdown` wins over stale runner state.
    - [ ] 11.5.2 Test that failed posts are skipped unless retry policy allows them.
    - [ ] 11.5.3 Test that interrupted attempts do not mark posts complete.
    - [ ] 11.5.4 Test that target hash mismatch prevents overwrite.
    - [ ] 11.5.5 Test that a live runner lock prevents a second mutating process.
    - [x] 11.5.6 Test stale-lock detection and explicit override behavior, including immediate detection of a dead local PID.
    - [ ] 11.5.7 Test that runner-owned staged files allow resume.
    - [ ] 11.5.8 Test that unrelated staged files block mutating modes.
  - [ ] 11.6 Add a mocked Ollama integration test.
    - [ ] 11.6.1 Use a local fake HTTP handler or injected client to return a deterministic cleaned post.
    - [ ] 11.6.2 Verify `--mode next` processes exactly one post.
    - [ ] 11.6.3 Verify `--mode batch --limit 2` processes at most two posts.
    - [ ] 11.6.4 Verify `--dry-run` does not modify target posts.
    - [ ] 11.6.5 Verify batch mode records a failed post and continues by default.
    - [ ] 11.6.6 Verify batch mode stops on a failed post when `--stop-on-failure` is set.
    - [ ] 11.6.7 Verify stalled stream timeout handling.

- [x] 12. Document the execution pattern.
  - [x] 12.1 Update `playbooks/how_to_clean_wordpress_markdown_posts.md`.
    - [x] 12.1.1 Add a section for the automated AGX/Ollama runner.
    - [x] 12.1.2 Document `--mode next` as the first required test command.
    - [x] 12.1.3 Document `--mode batch` as the long-lived command.
    - [x] 12.1.4 Document `--mode inventory` and `--mode report`.
    - [x] 12.1.5 Document `--stage` behavior and the expectation of many staged post changes.
    - [x] 12.1.6 Document crash recovery through `conversion_state` plus runner state.
    - [x] 12.1.7 Document how failed posts remain `wordpress` and are retried or skipped.
    - [x] 12.1.8 Document that the script never commits or pushes.
    - [x] 12.1.9 Document exact batch failure semantics and `--stop-on-failure`.
    - [x] 12.1.10 Document missing-state handling and `--include-missing-state`.
    - [x] 12.1.11 Document runner lock behavior and stale-lock recovery.
    - [x] 12.1.12 Document the exact model response envelope.
    - [x] 12.1.13 Document how runner-owned staged files are recognized on resume.
  - [x] 12.2 Update `README.md` only if the script becomes part of human-facing content maintenance workflow.
    - [x] 12.2.1 Add a concise maintenance note under Editing Content if warranted.
    - [x] 12.2.2 Keep detailed operational instructions in the playbook, not the README.
  - [-] 12.3 Update `agents/RULES.md` playbook index if playbook names, paths, or operational inventory change. Closed for this host checkpoint because no playbook was added or renamed, and editing the submodule policy file would dirty the submodule.
    - [-] 12.3.1 Ensure `how_to_clean_wordpress_markdown_posts.md` is listed if still missing. Existing index drift remains a separate framework sync issue.
    - [x] 12.3.2 Ensure any new playbook or reference is listed.

- [ ] 13. Verify the implementation.
  - [x] 13.1 Run static checks.
    - [x] 13.1.1 Run `python -m py_compile runner/clean_wordpress_posts.py`.
    - [-] 13.1.2 Run the Python unit test suite for the runner. Closed for this checkpoint because no dedicated test suite exists yet; read-only mode checks were run instead.
  - [x] 13.2 Run read-only script checks.
    - [x] 13.2.1 Run `python runner/clean_wordpress_posts.py --mode inventory`.
    - [x] 13.2.2 Run `python runner/clean_wordpress_posts.py --mode report`.
    - [x] 13.2.3 Confirm neither read-only mode changes repository files.
  - [ ] 13.3 Run mocked execution checks.
    - [ ] 13.3.1 Run mocked `--mode next` against a fixture workspace.
    - [ ] 13.3.2 Run mocked `--mode batch --limit 2` against a fixture workspace.
    - [ ] 13.3.3 Confirm resume behavior after a simulated crash.
    - [ ] 13.3.4 Confirm batch mode continues after one per-post validation failure.
    - [ ] 13.3.5 Confirm `--stop-on-failure` stops after one per-post validation failure.
    - [ ] 13.3.6 Confirm lock handling prevents two mutating runner instances.
    - [ ] 13.3.7 Confirm runner-owned staged-file resume behavior.
  - [x] 13.4 Run live AGX smoke checks when `xavier` is reachable.
    - [x] 13.4.1 Run a health check against `http://xavier:11434`.
    - [x] 13.4.2 Run `--mode next --dry-run` with the chosen model. `qwen3.5:9b` passed with `num_ctx=4096`, `num_predict=1536`, `num_batch=128`, and thinking disabled after the initial memory/context-limit diagnostics.
    - [x] 13.4.3 Review the generated candidate, validation report, and saved patch for `_posts/2008-08-25-unity.md`; validation passed without content or metadata loss.
    - [x] 13.4.4 Run `--mode next --stage` on `_posts/2008-08-25-unity.md`; the post passed and was staged as a runner-owned success.
    - [x] 13.4.5 Inspect the staged diff for the one-post test; only `conversion_state`, imported hard-break whitespace, and the missing final newline changed.
  - [x] 13.5 Run site-level validation after one real post is cleaned.
    - [-] 13.5.1 Run the smallest available Jekyll or Markdown build check. Closed because the repository has no `Gemfile` and `jekyll` is not installed in the execution environment.
    - [x] 13.5.2 Record the unavailable site-build dependency gap and manually verify the staged post diff, preserved front matter, preserved prose, normalized paragraph spacing, and final newline.

- [ ] 14. Prepare for long-lived operation.
  - [x] 14.1 Define the recommended first production command.
    - [x] 14.1.1 Start with `--mode next --stage` for one real post.
    - [x] 14.1.2 Review that staged diff before batch mode.
    - [x] 14.1.3 Start batch mode with a small `--limit` before an unattended long run.
    - [x] 14.1.4 Increase limit only after validation reports are acceptable.
  - [x] 14.2 Define operational monitoring.
    - [x] 14.2.1 Print flushed phase updates for selection, Ollama request, response receipt, validation, apply, staging, and failure.
    - [x] 14.2.2 Print cumulative success and failure counts after every attempted post.
    - [x] 14.2.3 Prefix progress output with total run elapsed time.
    - [x] 14.2.4 Print the current post path and one-based position before processing it.
    - [x] 14.2.5 Print the completed-to-run-limit ratio after every attempted post.
    - [x] 14.2.6 Estimate remaining time from average completed-attempt duration.
    - [x] 14.2.7 Show ETA as unavailable before the first post completes.
    - [x] 14.2.8 Use the selected candidate count as the effective limit when `--limit` is omitted or exceeds eligibility.
    - [x] 14.2.9 Print exact state/report paths for every failed post.
    - [x] 14.2.10 Document verbose progress fields and representative output in `runner/README.md`.
    - [x] 14.2.11 Verify progress output for `next`, limited batch, failure, and no-explicit-limit calculations; a live `next --dry-run` also confirmed streaming heartbeats and terminal ETA.
  - [x] 14.3 Define human review checkpoints.
    - [x] 14.3.1 Stop after first successful staged post for review.
    - [x] 14.3.2 Stop after a small batch for review.
    - [x] 14.3.3 Use `--mode report` before reviewing large staged diffs.
    - [x] 14.3.4 Do not commit generated post changes until the user approves a review strategy.
  - [x] 14.4 Persist complete output from the latest invocation.
    - [x] 14.4.1 Recreate `runner/last_run.log` when the script launches.
    - [x] 14.4.2 Tee stdout to both the console and `runner/last_run.log`.
    - [x] 14.4.3 Tee stderr to both the console and `runner/last_run.log`.
    - [x] 14.4.4 Flush console and file output immediately during long-running operations.
    - [x] 14.4.5 Ignore `runner/last_run.log` in Git.
    - [x] 14.4.6 Document log replacement and monitoring behavior in `runner/README.md`.
    - [x] 14.4.7 Test replacement, stdout capture, stderr capture, immediate flushing, and unhandled-exception capture.

- [ ] 15. Complete repository checkpoint hygiene.
  - [x] 15.1 Update this plan as implementation items are completed or intentionally closed.
  - [x] 15.2 Regenerate plan indexes after moving this plan to `current` or updating checklist status.
  - [x] 15.3 Append today's journal repo work log entry for implementation checkpoints.
  - [x] 15.4 Review `git status` and relevant diffs before any commit.
  - [x] 15.5 Suggest a checkpoint-scoped commit message after implementation verification.
  - [ ] 15.6 Commit only after the user approves the completed checkpoint.

- [x] 16. Harden the runner based on the first 100-post batch review.
  - [x] 16.1 Preserve complete YAML front matter locally and send only the body to Ollama.
  - [x] 16.2 Add normalized visible-text comparison and bounded Levenshtein diagnostics.
    - [x] 16.2.1 Exclude YAML from text comparison.
    - [x] 16.2.2 Decode HTML entities and retain visible HTML text while stripping tags.
    - [x] 16.2.3 Remove Markdown formatting syntax while retaining visible labels and image alt text.
    - [x] 16.2.4 Remove whitespace and line breaks before comparison.
    - [x] 16.2.5 Compare canonical strings directly before calculating distance.
    - [x] 16.2.6 Use bounded rolling-row Levenshtein only for mismatched canonical strings.
    - [x] 16.2.7 Record hashes, lengths, distance, ratio, first mismatch, and context in reports.
  - [x] 16.3 Add deterministic review metadata and state.
    - [x] 16.3.1 Write `cleanup_levenshtein_distance` and `cleanup_levenshtein_ratio` to applied post YAML.
    - [x] 16.3.2 Mark distance-zero candidates `conversion_state: markdown`.
    - [x] 16.3.3 Mark small nonzero candidates `conversion_state: review`.
    - [x] 16.3.4 Require both `--review-max-distance` and `--review-max-ratio` thresholds.
    - [x] 16.3.5 Exclude `review` posts from automatic reruns and list them by descending distance.
  - [x] 16.4 Compare URL, image, and embed occurrence counts so additions and duplicates fail validation.
  - [x] 16.5 Handle imported Instagram post bodies with deterministic cleanup rules.
  - [x] 16.6 Add per-run manifests and reports that distinguish the current batch from cumulative state.
  - [x] 16.7 Retry malformed response envelopes under a bounded policy.
  - [x] 16.8 Add regression fixtures from rejected and false-positive candidates found in the first batch.
  - [x] 16.9 Revert all unsafe staged candidates from the first batch before rerunning.
  - [x] 16.10 Run and review a 10-post `--retry-failed --dry-run` smoke batch; 7 exact distance-zero candidates passed, 3 candidates were safely rejected for unresolved long prose lines, one malformed response succeeded on its bounded retry, and no post files changed.

- [x] 17. Review and checkpoint the full cleanup batch.
  - [x] 17.1 Review the completed 1,827-post run manifest and aggregate outcomes.
  - [x] 17.2 Confirm all 484 failed candidates left their original posts unchanged.
  - [x] 17.3 Unstage all 47 new `conversion_state: review` candidates.
  - [x] 17.4 Audit all 152 distance-zero Ollama candidates for formatting-semantic changes outside visible-text comparison.
  - [x] 17.5 Unstage 45 distance-zero candidates with unresolved wrappers, shortcodes, export noise, inferred emphasis, broken linked-image structure, or incomplete Markdown lists.
  - [x] 17.6 Retain 1,251 conservative candidates: 1,144 deterministic Instagram posts and 107 audited distance-zero Ollama edits.
  - [x] 17.7 Ignore recognized WordPress shortcode tags during visible-text comparison while retaining enclosed text and non-shortcode media-target validation.
  - [x] 17.8 Verify staged scope, runner tests, diff whitespace, and absence of staged review-state posts before commit.
  - [x] 17.9 Manually audit, conservatively clean, validate at distance zero, and stage all 12 shortcode-containing posts while preserving their shortcode syntax.

18. [x] Add a bounded multi-stage repair pipeline for second-wave cleanup.
  - [x] 18.1 Add deterministic iframe simplification, iframe-only wrapper removal, empty source-less video cleanup, and evidence-based typography restoration.
  - [x] 18.2 Reject unresolved export artifacts, changed linked-image relationships, and inferred emphasis.
  - [x] 18.3 Add AGX classification for formatting fixes, minor text fixes, substantive changes, main-prompt retries, and blocked cases.
  - [x] 18.4 Add specialized formatting, restoration, and restart prompts that retain the original body as authority.
  - [x] 18.5 Bound repair rounds and prompt sizes with CLI controls and persist pipeline history in attempt reports.
  - [x] 18.6 Lower the default review ceiling to distance 10 while retaining the 1 percent ratio cap.
  - [x] 18.7 Add deterministic, structural-validation, classifier-envelope, and repair-branch regression tests.

19. [x] Harden the runner after the completed incomplete-post retry batch.
  - [x] 19.1 Commit and push 145 staged `conversion_state: markdown` posts after unstaging all `cleanup_review_required: true` posts.
  - [x] 19.2 Review saved runner reports and confirm the largest unresolved classes are long prose lines, response-envelope/report omissions, incomplete repair rounds, visible-text changes, and media/emphasis validation failures.
  - [x] 19.3 Add deterministic structural cleanup that separates existing Markdown/HTML media blocks from prose and wraps oversized prose lines without changing canonical visible text.
  - [x] 19.4 Fix canonical visible-text normalization for linked-image Markdown before plain-image normalization.
  - [x] 19.5 Accept exactly one cleaned-body response block with a missing cleanup report by synthesizing a local report and letting validation decide.
  - [x] 19.6 Document the deterministic structural pass and cleanup-report fallback in `runner/README.md`.
  - [x] 19.7 Add regression tests for media separation, long-line wrapping, and missing-report response parsing.

## Success Criteria

- The runner can clean exactly one eligible post with `--mode next`.
- The runner can run for a long batch and resume from actual post front matter after a crash or restart.
- Batch mode records per-post failures and continues by default.
- Batch mode can stop after the first per-post failure with `--stop-on-failure`.
- The runner leaves completed posts marked `conversion_state: markdown`.
- The runner marks small normalized visible-text differences `conversion_state: review` with YAML distance metadata.
- The runner leaves failed or uncertain posts marked `conversion_state: wordpress`.
- Missing-state posts are reported and skipped by default.
- The runner enforces a single active mutating process with a recoverable lock.
- The runner parses one exact nonce-delimited model response envelope.
- The runner validates metadata, URLs, media, wrappers, paragraph structure, headings, and section labels before applying changes.
- Oversized posts are skipped with reports until chunked cleanup is implemented and validated.
- The runner stages only successfully validated post changes when `--stage` is enabled.
- The runner resumes safely with previously staged runner-owned post files and blocks unrelated staged changes.
- The runner never commits or pushes.
- The execution pattern is documented in the WordPress cleanup playbook.
