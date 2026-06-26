# Playbook: Clean WordPress-to-Markdown Blog Posts

## Objective

Clean one imported WordPress post at a time so it renders as readable Markdown while preserving the post's meaning, metadata, permalink, title, date, categories, tags, links, images, and embeds.

Use this playbook with a single post file path.

## AGX Prompt Template

```text
Clean this WordPress-exported Markdown post:

POST_PATH={{post_path}}

Rules:
- Edit only POST_PATH.
- Preserve all factual content, wording, links, citations, and media.
- Preserve YAML fields except update conversion_state from wordpress to markdown only after the validation checklist passes.
- Do not rewrite the author's voice.
- Do not summarize, shorten, or add new claims.
- Preserve source order exactly unless repairing a clearly broken wrapper requires moving content out of markup without changing its relative order.
- Read and clean the whole post in source order, using the moving-window protocol when the post is too large for one context window.
- Make the Markdown readable and safe for Jekyll.
- Run a self-check after editing and fix any failures before reporting completion.
- Report what artifact types you fixed.
```

## Required Front Matter

Every post must include:

```yaml
conversion_state: wordpress
```

After the post is cleaned, change it to:

```yaml
conversion_state: markdown
```

Do not mark `markdown` until the body has been reviewed and cleaned.

If the cleanup is incomplete or uncertain, leave `conversion_state: wordpress` and explain what remains in the report.

`conversion_state: markdown` means the post was read in source order, cleaned in source order, re-checked after editing, and all chunk seams plus the beginning and end of the post were reviewed.

## Moving-Window Reading Protocol

Some posts are too long to fit comfortably alongside the instructions. In that case, do not skim and do not rely on search results alone. Work through the post with a moving context window.

1. **Map the file first**
   - Read the front matter and enough of the body to identify the post type, major sections, media patterns, and whether references/citations are present.
   - Record a tiny running state before editing:
     - current section or heading
     - whether a list, table, blockquote, code block, embed, or HTML wrapper is open
     - whether references/citations/appendices have started
     - any unresolved formatting anomaly to revisit

2. **Clean in ordered chunks**
   - Process the body from top to bottom in chunks sized to fit the available context, usually 80-150 lines or roughly 2,000-4,000 words.
   - Preserve relative order inside and across chunks.
   - Never move a sentence, paragraph, image, citation, or embed earlier or later except to unwrap it from broken HTML while preserving its original relative position.
   - At each chunk boundary, inspect the last few lines of the previous chunk and the first few lines of the next chunk together so paragraphs, lists, blockquotes, tables, and citations do not get split incorrectly.

3. **Maintain running state**
   - Carry the tiny running state forward after each chunk.
   - If a chunk ends inside a list, blockquote, table, code block, HTML wrapper, citation list, or embed, continue the structure correctly in the next chunk.
   - If the next chunk reveals that a prior edit was wrong, go back and repair the earlier chunk before continuing.

4. **Read the cleaned result**
   - After editing all chunks, read the cleaned post again in source order.
   - If the whole cleaned post still does not fit in one context window, do a second moving-window pass over the cleaned file.
   - Do not set `conversion_state: markdown` until this second pass is complete.

5. **Run a structural sweep**
   - Always inspect:
     - the first 30 body lines
     - the last 50 body lines
     - every chunk seam
     - every line containing section labels such as `Works Cited`, `References`, `Bibliography`, `Appendix`, `Footnotes`, `Sources`, or `Term Paper`
     - every line containing raw or converted structure markers such as `<div`, `<span`, `</`, `<figure`, `<iframe`, `wp-block`, `![`, `[![]`, `**Works`, `## Works`, or `###`
   - Treat this sweep as a backstop, not a substitute for reading the post.

## Cleanup Rules

1. **Preserve Metadata**
   - Keep `id`, `title`, `date`, `author`, `layout`, `guid`, `permalink`, `categories`, and `tags`.
   - Add only `conversion_state` if it is missing.

2. **Remove WordPress Wrapper HTML**
   - Remove shell markup such as `<main>`, `<article>`, `<div class="entry-content">`, `<footer class="entry-footer">`, and matching close tags.
   - Preserve the text, links, images, and embeds inside those wrappers.

3. **Remove Copied UI Wrapper HTML**
   - Remove non-content layout wrappers copied from editors or chat UIs, especially `<div class="flex ...">`, `<div class="markdown ...">`, and style-only `<span ...>` wrappers.
   - Preserve the visible content inside them.

4. **Images**
   - Prefer Markdown image syntax: `![alt text](image-url)`.
   - Convert simple `<img src="..." alt="...">` tags to Markdown images.
   - Unwrap simple `<figure class="wp-block-image ...">...</figure>` blocks.
   - Put images on their own block with one blank line before and after.
   - If an image is linked, keep the linked image form: `[![alt](image-url)](target-url)`.
   - Do not delete images unless they are obvious empty tracking pixels.

5. **Embeds**
   - Preserve meaningful embeds.
   - Remove export noise such as `data-mce-fragment` and random generated `name` attributes.
   - Use a simple iframe when needed:
     `<iframe class="post-embed" src="EMBED_URL" loading="lazy"></iframe>`
   - Put embeds on their own block with one blank line before and after.
   - If an embed is broken beyond repair, replace it with a plain Markdown link to the embed URL and note that in the report.

6. **Paragraphs**
   - Split giant single-line paragraphs into readable paragraphs.
   - Prefer natural topic shifts, sentence groups, and transitions.
   - Do not split every sentence into its own paragraph.
   - Do not merge lists, headings, or citations into prose paragraphs.
   - Insert real Markdown paragraph breaks, not just visual line wrapping.
   - Ensure every prose paragraph is separated from the next by one blank line.
   - As a validation gate, no normal prose line should remain over roughly 800 characters unless it is a URL, table row, code block, or other intentional long artifact.
   - Useful paragraph-break cues include examples, quotations, source transitions, "However," "Therefore," "For example," "First/Second/Third," and shifts from setup to analysis.
   - Do not rearrange paragraphs while splitting them.
   - Repair glued inline Markdown links such as `[label ](url)word` to `[label](url) word` when the source clearly intended surrounding prose.

7. **Headings**
   - Move collapsed headings onto their own line.
   - Section labels such as `Works Cited`, `References`, `Bibliography`, `Appendix`, `Footnotes`, `Sources`, and `Term Paper` must be standalone headings or standalone metadata lines, not glued to prose.
   - Convert inline heading fragments like `paragraph text ### Heading` into:
     ```markdown
     paragraph text

     ### Heading
     ```
   - Keep heading levels unless they are clearly malformed image headings such as `## ![](image.jpg)`.
   - Repair glued emphasis headings such as `paragraph text **Works Cited**` into a paragraph break plus a Markdown heading.

8. **Lists**
   - Ensure a blank line before a list.
   - Preserve nested indentation.
   - Do not rewrite list item text.
   - If a list item contains an image, put the image on a following indented block only when needed for valid Markdown.

9. **Emphasis and Content Warnings**
   - Preserve emphasis markers when they are meaningful.
   - Repair glued emphasis such as `***CW: SA***Text` to:
     ```markdown
     ***CW: SA***

     Text
     ```

10. **References and Citations**
    - Preserve every citation and URL.
    - Split citation blocks for readability only when safe.
    - Format references consistently: either one citation per paragraph or one citation per bullet.
    - If using bullets, ensure a blank line between adjacent citation bullets.
    - References and citations often appear at the end of posts; always inspect the tail of the file after cleanup.
    - Do not leave multiple citations collapsed into one paragraph when they were separate sources.
    - Do not split one citation across unrelated paragraphs unless the source already clearly does so.
    - Do not invent bibliographic fields.

## Small-Model Safety Loop

When delegating to a small model, require three passes:

1. **Moving-window cleanup pass**: read and clean the entire post in source order, chunk by chunk.
2. **Moving-window reread pass**: reread the cleaned post in source order, checking that source order, meaning, links, media, citations, and section boundaries are intact.
3. **Structural validation pass**: check front matter, raw wrapper HTML, paragraph separation, long prose lines, headings, lists, citations, images, embeds, chunk seams, first body lines, tail body lines, and section-label lines.
4. **Repair pass**: fix every validation failure before changing `conversion_state` to `markdown`.

If the model cannot confidently complete the repair pass, it must leave `conversion_state: wordpress` and report the blocker.

## Validation Checklist

- `conversion_state` is `markdown`.
- The post still has the same title, date, permalink, categories, and tags.
- No raw WordPress shell wrappers remain.
- No copied UI wrapper HTML remains.
- Images and embeds are separated from prose.
- Long paragraphs are readable, and ordinary prose lines are under roughly 800 characters.
- Every adjacent prose paragraph has a blank line between it and the next paragraph.
- Markdown headings render as headings.
- Section labels are standalone headings or metadata lines, never glued to prose.
- Lists still render as lists.
- Citation formatting is consistent.
- References, citations, footnotes, appendices, and end matter have been read and cleaned.
- Source order is preserved.
- Chunk seams were checked when moving-window cleanup was used.
- No content was intentionally removed.

## Completion Report Format

```text
Cleaned: POST_PATH
Conversion state: markdown
Fixed:
- [artifact type]
- [artifact type]
Validation:
- Raw wrapper HTML: pass/fail
- Long prose lines over 800 characters: count
- Paragraph blank lines: pass/fail
- Source order preserved: pass/fail
- Section labels standalone: pass/fail
- End matter checked: pass/fail
- Moving-window chunks used: yes/no
Notes:
- [anything risky, skipped, or manually interpreted]
```
