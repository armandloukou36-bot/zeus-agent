---
name: cvlynk-orchestrator
description: "Use for cvlynk orchestrator: enroll, heartbeat, tasks."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [orchestrator, cvlynk, multi-agent, agents, tasks, heartbeat, enrollment]
    category: software-development
---

# Cvlynk Multi-Agent Orchestrator

Connect an agent (this Hermes instance or any agent) to the online orchestrator at
`https://api.cvlynk.com/`. The root serves an admin SPA (React); the API lives under
`/api/v1/`. Service identity: `multi-agent-orchestrator` v1.0.0 (`GET /health` →
`{"status":"ok",...}`).

## Credentials (where they live)

- **Enrollment key** (register NEW agents): in the user's attachment
  `ORCHESTRATEUR EN LIGNE.txt` (Bearer, long token). Not stored in the repo —
  ask/read the attachment when needed.
- **Agent token** (post-enrollment credential for THIS instance):
  `/root/.hermes/cvlynk/credentials.env` (chmod 600), lines `agent_id=…` and
  `access_token=…`. Never echo it.

## Auth model

Two distinct credentials:
1. **Enrollment key** → `Authorization: Bearer <key>` ONLY for `POST /agents/enroll`.
2. **Agent token** (returned by enroll as `access_token`) → `Authorization: Bearer <token>`
   for everything else (heartbeat, me, tasks, results).

Admin-only endpoints (require an admin session via `/api/v1/auth/login`, NOT the agent
token) return `401 {"code":"UNAUTHENTICATED","message":"Session administrateur absente…"}`.

## Agent API (discovered, no OpenAPI exposed)

| Method + path | Auth | Body / returns |
|---|---|---|
| `POST /api/v1/agents/enroll` | Bearer enrollment key | `{client_instance_id, requested_name}` → `{agent_id, name, role, status, access_token, token_type}` |
| `POST /api/v1/agents/heartbeat` | Bearer agent token | `{}` → `{accepted, agent_status, orchestrator_status, server_time}` |
| `GET  /api/v1/agents/me` | Bearer agent token | my info incl. `capabilities[]`, `instance_id`, `last_seen_at` |
| `GET  /api/v1/agents/tasks` | Bearer agent token | array of my assigned tasks (may be `[]`) |
| `POST /api/v1/agents/tasks/{task_id}/result` | Bearer agent token | body needs `status` (+ result fields) |

## Enrollment protocol (critical pitfalls)

- `POST /agents/enroll` validates required fields first: it answers
  `VALIDATION_ERROR` listing missing fields (`client_instance_id`, `requested_name`) —
  that error is the fastest way to learn a field. Auth failures say
  `"Clé d'enregistrement requise."` (enrollment key) or `"Jeton d'agent requis."`
  (agent token) — use these messages to tell which credential an endpoint wants.
- **Enrollment is idempotent per `client_instance_id`.** Re-enrolling the same
  instance returns `AGENT_ALREADY_ENROLLED` and tells you to reuse the existing token.
  A fresh enrollment requires revocation first. So declare `capabilities` at FIRST
  enrollment — they cannot be patched afterward (no working PATCH/PUT on `/me` or
  `/capabilities`; those return 405).
- **`capabilities` IS a valid enroll field** (optional array). The orchestrator
  stores it and echoes it back on `/agents/me`. Omit it and the agent registers
  with `capabilities: []` permanently.
- **`requested_name` is globally unique**: enrolling a second agent with an
  already-taken name gets an auto suffix (`"Foo"` → `"Foo (2)"`, `"Foo (3)"`…).
  There is no rename endpoint, so pick the name once and never re-enroll under it.
- **Agent revocation/deletion is ADMIN-only.** `DELETE /api/v1/agents/me` and every
  revoke path return `401 Session administrateur absente` for an agent token — the
  agent cannot self-delete. To clean up a botched enrollment (wrong name/empty caps),
  a human must delete the agent from the admin dashboard.
- `status` starts `PENDING`, flips to `ONLINE` on first heartbeat. Heartbeats update
  `last_seen_at`; without periodic heartbeats the agent goes offline.
- No `/api/v1/openapi.json` or `/docs` (both return the SPA HTML or 404). Enumerate
  by probing: 401 = route exists (needs auth), 404 = route absent, 405 = exists but
  wrong method, 422 = exists but body invalid.

## Connect flow (full)

```bash
BASE=https://api.cvlynk.com
KEY='<enrollment key>'
# 1. enroll (idempotent per instance id)
curl -s -X POST "$BASE/api/v1/agents/enroll" \
  -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"client_instance_id":"zeus-builder-01","requested_name":"ZEUS Builder","capabilities":["web_development","backend","deployment"]}'
# -> capture agent_id + access_token, store 600
# 2. heartbeat to go ONLINE
curl -s -X POST "$BASE/api/v1/agents/heartbeat" -H "Authorization: Bearer $TOKEN" -d '{}'
# 3. poll tasks, then report results
curl -s "$BASE/api/v1/agents/tasks" -H "Authorization: Bearer $TOKEN"
curl -s -X POST "$BASE/api/v1/agents/tasks/$TASK_ID/result" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"completed","result":"..."}'
```
