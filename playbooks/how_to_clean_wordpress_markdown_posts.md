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
- Preserve YAML fields except update conversion_state from wordpress to markdown after cleanup.
- Do not rewrite the author's voice.
- Do not summarize, shorten, or add new claims.
- Make the Markdown readable and safe for Jekyll.
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

7. **Headings**
   - Move collapsed headings onto their own line.
   - Convert inline heading fragments like `paragraph text ### Heading` into:
     ```markdown
     paragraph text

     ### Heading
     ```
   - Keep heading levels unless they are clearly malformed image headings such as `## ![](image.jpg)`.

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
    - Do not invent bibliographic fields.

## Validation Checklist

- `conversion_state` is `markdown`.
- The post still has the same title, date, permalink, categories, and tags.
- No raw WordPress shell wrappers remain.
- No copied UI wrapper HTML remains.
- Images and embeds are separated from prose.
- Long paragraphs are readable.
- Markdown headings render as headings.
- Lists still render as lists.
- No content was intentionally removed.

## Completion Report Format

```text
Cleaned: POST_PATH
Conversion state: markdown
Fixed:
- [artifact type]
- [artifact type]
Notes:
- [anything risky, skipped, or manually interpreted]
```
