# blog.cjtrowbridge.com

Personal blog, long-form archive, and project notebook for CJ Trowbridge.

The public site is configured for `https://blog.cjtrowbridge.com`.

This blog was exported from WordPress into Markdown. That migration created many formatting problems in individual posts and exposed layout issues across the site, so cleaning up Markdown, repairing old post formatting, and improving the visual presentation are ongoing maintenance projects.

## Content Structure

```text
.
├── _posts/                 # Dated blog posts using Jekyll's YYYY-MM-DD-title.md convention
├── index.md                # Home page
├── all-posts.md            # All posts landing page
├── book-clubs.md           # Book club landing page
├── book-clubs/             # Book-club-specific pages
├── burning-man.md          # Burning Man landing page
├── category/               # Category archive pages
├── *.md                    # Standalone pages and long-form essays
├── _layouts/               # Page, post, home, frontpage, and category templates
├── _includes/              # Shared template partials
├── assets/                 # Site CSS and static assets
├── wp-content/uploads/     # Imported or archived media uploads
├── _config.yml             # Site URL, name, and configuration
└── CNAME                   # Custom domain configuration
```

## Agentic Framework Structure

Agent-facing operating instructions live in `AGENTS.md`; this README is for humans. The repository also includes an agentic workflow framework for plans, journals, kanban, and reusable operational guidance.

Local maintenance automation, including the WordPress cleanup runner, lives in `runner/` and is excluded from the generated public site.

```text
.
├── AGENTS.md               # Agent entrypoint and host-specific framework guidance
├── agents/                 # Git submodule containing upstream framework policy and defaults
├── plans/
│   ├── future/             # Queued plans
│   ├── current/            # Active execution plans
│   └── past/               # Archived plans
├── journal/                # Daily repo work logs and checkpoint notes
├── kanban/                 # Human-authored task boards
├── downtime/
│   └── reports/
│       ├── pending/        # Downtime reports awaiting review
│       └── reviewed/       # Reviewed downtime reports
├── playbooks/              # Host-managed workflow playbooks copied from the framework
├── references/             # Reusable framework guidance
├── templates/              # Standard templates for plans, reports, journals, and boards
└── scripts/                # Host-managed helper scripts
```

## Editing Content

- Add new blog posts under `_posts/` with dated filenames.
- Add standalone pages as root-level Markdown files or in topical folders.
- Use existing front matter patterns from nearby posts or pages.
- Expect older posts to need cleanup because the WordPress-to-Markdown export left inconsistent formatting.
- Treat site layout polish and Markdown repair as ongoing work, not one-time migration cleanup.
- Keep public, human-facing project documentation in this README.
- Keep agent-facing workflow and policy details in `AGENTS.md`.

## Styling Direction

The site is moving toward Bootstrap-first dark-mode styling. Prefer Bootstrap layout and component classes in templates, and keep `assets/css/global.css` limited to site-specific exceptions such as legacy image handling, social button colors, and ensuring linked headings remain white.

Agentic framework directories are excluded from the generated public site in `_config.yml`; they are repo operations material, not blog content.

Homepage category images stack above post lists on mobile and shift left of the lists on desktop, with desktop image width capped at `500px`.

Imported posts use `conversion_state` front matter to track cleanup status. `wordpress` means the post still needs WordPress-to-Markdown cleanup; `markdown` means the post has been cleaned for the current static-site presentation.

The optional WordPress cleanup runner lives in `runner/` and is excluded from the generated public site.
