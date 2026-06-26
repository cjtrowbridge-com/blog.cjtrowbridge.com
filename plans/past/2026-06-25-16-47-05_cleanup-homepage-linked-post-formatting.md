---
plan_id: 2026-06-25-16-47-05_cleanup-homepage-linked-post-formatting
title: Cleanup Homepage-Linked Post Formatting
summary: Repair WordPress-to-Markdown formatting issues in posts currently linked from the homepage.
status: past
created_at: 2026-06-25-16-47-05
---

# Cleanup Homepage-Linked Post Formatting

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Objective

Improve the visible quality of the homepage-linked blog posts first, while leaving the rest of the imported archive for later cleanup.

## Scope

Homepage-linked posts include the current posts surfaced under:

- Latest Posts
- Adventures
- Reading List
- Essays

Known artifact families:

- giant single-line paragraphs from the WordPress-to-Markdown export,
- images or linked images glued inline to surrounding prose,
- raw WordPress wrapper HTML such as `<main>`, `<article>`, `entry-content`, and `entry-footer`,
- raw embed wrappers such as TikTok `<iframe>` blocks with export attributes,
- copied AI/chat UI wrapper HTML in long-form posts,
- headings collapsed into paragraph text,
- sparse or inconsistent blank lines around lists, headings, images, and embeds.

## Checklist

- [x] Rebuild the exact homepage-linked post list from the current generated homepage or `_layouts/frontpage.html` category queries.
- [x] Create a no-write cleanup report for the linked posts that groups each file by artifact type and cleanup risk.
- [x] Add or adjust post-level CSS for safe global presentation fixes such as image sizing, figure spacing, and responsive iframes.
- [x] Apply low-risk mechanical cleanup to homepage-linked posts only: remove WordPress wrapper shells, unwrap simple figure wrappers, and add missing blank lines around images, embeds, lists, and headings.
- [x] Review high-risk long-form posts manually before paragraph reconstruction, preserving meaning and citations.
- [x] Re-run homepage and post checks after each cleanup batch.
- [x] Update `README.md` if the cleanup workflow or archive-maintenance guidance changes.
- [x] Update the journal with each completed cleanup checkpoint.
- [x] Review git status and summarize completed batches before commit/push.

## Execution Notes

- Added `conversion_state` front matter to all 2,056 posts.
- Marked 2,018 posts as `conversion_state: wordpress`.
- Cleaned and marked 38 homepage-linked posts as `conversion_state: markdown`.
- Added post-level media styles for images, figures, and normalized iframe embeds.
- Created `playbooks/how_to_clean_wordpress_markdown_posts.md` as the reusable AGX cleanup prompt/playbook.
- Validation found no missing or duplicate `conversion_state` fields.
- Validation found no remaining wrapper HTML, raw HTML image tags, link-fragment artifacts, or over-threshold long lines in the 38 cleaned homepage-linked posts.

## Suggested Batch Order

1. Media and wrapper cleanup for short travel/book posts.
2. Gear/setup posts with many inline images and lists.
3. Long essay posts with collapsed paragraphs.
4. AI/chat-exported posts with copied UI wrappers.

## Validation

- The homepage still renders the same post links.
- Cleaned posts retain their original title, permalink, date, categories, and tags.
- Images are visible and not glued to adjacent text.
- Embeds are either cleanly preserved or intentionally replaced with links.
- Markdown headings, lists, and paragraphs render as separate readable blocks.
- No agent/framework directories appear as public site pages.
