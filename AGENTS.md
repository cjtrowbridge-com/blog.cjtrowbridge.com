# AGENTS Instructions

`README.md` is for humans. `AGENTS.md` is for agents.

Read `./agents/RULES.md` in its entirety before doing anything in this repository. Follow all instructions in `./agents/RULES.md` as though they are written directly in this file.

This repository consumes the agents framework as a Git submodule at `./agents`.

Canonical agent policy lives in `./agents/RULES.md`. Host-root shim files, including this file, direct runtimes to that policy source.

From the host repository root:

- Treat `./agents/RULES.md` as the canonical policy source.
- Use host-managed `./playbooks/`, `./references/`, `./templates/`, and `./scripts/` when present.
- Fall back to `./agents/playbooks/`, `./agents/references/`, `./agents/templates/`, and `./agents/scripts/` when host-managed copies are missing.
- For host-owned plans, run `python agents/scripts/regenerate_plan_indexes.py --repo-root .`.
- Do not overwrite host-managed framework copies blindly; synthesize host changes with upstream framework updates and ask for user approval before final merge decisions.

Host-owned operational artifacts:

- `./plans/future/`, `./plans/current/`, `./plans/past/`
- `./journal/`
- `./kanban/`
- `./downtime/reports/pending/`, `./downtime/reports/reviewed/`

Host-managed framework copies:

- `./playbooks/`
- `./references/`
- `./templates/`
- `./scripts/`
