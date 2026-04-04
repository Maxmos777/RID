---
name: backend-engineer-python
description: >-
  Dispatches RID Python backend work to Ring agent ring:backend-engineer-python.
  Covers Django, FastAPI, django-tenants, pytest, ruff, and ADR compliance. Use when
  the task touches backend/*.py, migrations, ASGI, or Python service layers.
---

# Backend Engineer Python (RID + Ring)

## When to use

- Changes under `backend/` (Django, FastAPI, tests)
- Multi-tenant (`django-tenants`), `sync_to_async` / ADR-001 patterns
- New ADR compliance tests vs shell scripts

## Ring dispatch

Use the Ring orchestrator pattern: **Task** / subagent with:

- **Agent:** `ring:backend-engineer-python`
- **Prompt:** task description + paths + acceptance criteria + link to ADRs if relevant

Canonical agent definition: `ring/dev-team/agents/backend-engineer-python.md`

## Local verification (before merge)

```bash
cd backend && uv run ruff check .
cd backend && uv run pytest -q
```
