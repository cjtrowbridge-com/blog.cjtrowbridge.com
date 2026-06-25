---
plan_id: 2026-06-25-11-50-58_agents-framework-submodule-bootstrap
title: Agents Framework Submodule Bootstrap
summary: Integrate the agents framework as a host submodule and bootstrap host-managed operational artifacts.
status: current
created_at: 2026-06-25-11-50-58
---

# Agents Framework Submodule Bootstrap

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Checklist

- [x] Add `cjtrowbridge/agents` as the `./agents` Git submodule.
- [x] Read `./agents/AGENTS.md`, `./agents/RULES.md`, and the bootstrap playbook.
- [x] Create required host operational directories for plans, journal, kanban, and downtime reports.
- [x] Copy missing host-managed framework directories from `./agents/`.
- [x] Add host shim documentation pointing runtimes to `./agents/RULES.md`.
- [x] Update `README.md` with downstream integration notes.
- [x] Regenerate and validate host plan indexes.
- [x] Review git status and summarize checkpoint.
- [x] Move agent-facing README bootstrap notes into `AGENTS.md`.
