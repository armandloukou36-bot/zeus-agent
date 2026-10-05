---
name: supabase
description: "Use for Supabase: install, auth (PAT), projects, db push."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [supabase, cli, postgres, database, auth, deployment]
    category: software-development
    related_skills: [github]
---

# Supabase

Work with Supabase (hosted Postgres + Auth + Storage + Realtime + Edge Functions)
through the `supabase` CLI: install it, authenticate, link projects, push schema/
migrations, and manage services. This is the auth-and-connect baseline; the
full app workflow lives in the project session.

## Install (Linux)

Download the standalone binary from GitHub releases (no apt/npm needed):

```bash
VER=$(curl -s https://api.github.com/repos/supabase/cli/releases/latest \
  | grep -o '"tag_name": *"[^"]*"' | head -1 | cut -d'"' -f4)
curl -sL "https://github.com/supabase/cli/releases/download/${VER}/supabase_${VER#v}_linux_amd64.tar.gz" -o sb.tgz
cd /tmp && tar xzf sb.tgz && cp supabase /usr/local/bin/supabase && chmod +x /usr/local/bin/supabase
supabase --version   # verify
```

## Auth — Personal Access Token ONLY (no device flow)

Supabase has **no** OAuth device-code flow like `gh`. The CLI authenticates with a
Personal Access Token (starts `sbp_`):

```bash
supabase login --token <PAT>                 # interactive/foreground
# or, headless / non-interactive:
export SUPABASE_ACCESS_TOKEN=<PAT>
```

- `supabase login --no-browser` in a non-TTY fails with
  `LoginMissingTokenError` — it needs `--token` or the `SUPABASE_ACCESS_TOKEN`
  env var. There is no browser/device fallback.
- The user generates the PAT at **https://supabase.com/dashboard/account/tokens**.
- Store the token in a `0600` file or env; never echo it back after setup.

## Token permission scope

The token page shows a **Permissions** section with five categories, each set to
None/Read/Write, plus a **Read-only** preset. Minimum useful set for a full-stack
agent doing dev + migrations + deploy:

| Category | Level | Why |
|---|---|---|
| Project | Write | view/configure project settings, diagnostics |
| Database | Write | `db push`, SQL migrations, backups, data ops |
| Application services | Write | Auth, Storage, Realtime, Edge Functions, service config |
| Infrastructure and delivery | Write | domains, add-ons, network (needed to deploy) |
| Account and organization | Read | list/link projects (not needed to write globally) |

Do **not** use the Read-only preset — it blocks `db push` and deploys. Grant the
five categories individually.

## Core commands

```bash
supabase projects list                       # list projects (needs Account: Read)
supabase init                                # scaffold supabase/ in a project
supabase link --project-ref <ref>            # bind local project to a hosted project
supabase db push                             # apply local migrations to the linked DB
supabase db diff --linked -f <name>          # generate a migration from local change
supabase secrets list / secrets set NAME=...  # Edge Function secrets
supabase functions deploy <name>             # deploy an edge function
```

Use `-o json` on list commands and parse with `grep -o` + `head -1` (see pitfall).

## Pitfalls

- **"Vercel Security Checkpoint" (403) is not deployment protection.** A freshly
  deployed site returns 403 with an `<title>Vercel Security Checkpoint</title>`
  body to `curl` and to obvious headless browsers, while working fine for real
  users. Do not "fix" it by disabling SSO/password protection — check first:
  `GET /v9/projects/<projectId>?teamId=<teamId>` → `ssoProtection: null` means the
  site is already public. To test programmatically, use a realistic Playwright
  context (Chrome user-agent, `locale`, `viewport`,
  `--disable-blink-features=AutomationControlled`) and wait ~5 s for the JS
  challenge to resolve. Also raise navigation timeouts: cold starts and the
  challenge make production noticeably slower than localhost.
- **A test suite that stops early hides untested features.** A Playwright run that
  throws mid-script still reports the checks it ran (e.g. "38/38") — read that as
  "38 of ~45", not success. Assert the final expected count, and treat
  `ERREUR FATALE` as a failure even when every printed line says OK. A test gated
  behind a missing credential (an `if (hasServiceKey)` branch) silently skips its
  feature: verify the branch was actually taken.
- **Make E2E tests idempotent before trusting them.** Data left by earlier runs
  breaks later assertions (a search filter matching two rows, no `pending` record
  left to act on). Generate a unique run id per execution and use it in every name
  and search term; create the record you need instead of relying on leftover state.
- **RLS hides rows from the client that just created them.** After
  `auth.admin.createUser`, the new user's `profiles` row belongs to the org the
  signup trigger created — invisible to the inviting user. Read it with the
  service-role client, or the cleanup (deleting the orphan org) silently no-ops.
- **A signup trigger calling `unaccent` fails with a generic
  `Database error saving new user` (HTTP 500 on `/auth/v1/signup`)** because the
  extension is not enabled by default. Either `create extension unaccent`, or
  transliterate with `translate()` in pure SQL — and build the source/target
  strings programmatically with an equal-length assertion: hand-counted accent
  tables mis-map silently, and multi-char ligatures (`æ`→`ae`) shift every later
  character.
- **Supabase rejects some email domains** (`email_address_invalid` on e.g.
  `@x.app`) and rate-limits signups (`over_email_send_rate_limit`). To seed a demo
  or test account reliably, insert into `auth.users` + `auth.identities` directly
  with `crypt(pw, gen_salt('bf'))` and `email_confirmed_at = now()`.
- **`mailer_autoconfirm` defaults to `false`**, so email/password signup returns no
  usable session until the address is confirmed — and there is no SMTP by default.
  Set it to `true` via `PATCH /v1/projects/<ref>/config/auth` for an app that must
  log users in immediately; also update `site_url` (default `http://localhost:3000`)
  before deploying.
- **`supabase link` may fail with `LinkAuthTokenError` even when the token works.**
  A PAT scoped with Project:Write + Database:Write can still be refused on the
  `/v1/projects/<ref>/database/migration` endpoints. Verify what the token CAN do
  before assuming it is invalid:

  ```bash
  curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $PAT" \
    https://api.supabase.com/v1/projects/<ref>/api-keys      # 200 = OK
  ```

  Workaround when `link`/`db push` are blocked: run SQL through the Management API,
  which only needs Database:Write:

  ```bash
  curl -s -X POST -H "Authorization: Bearer $PAT" -H "Content-Type: application/json" \
    -d "$(python3 -c 'import json,sys;print(json.dumps({"query":open(sys.argv[1]).read()}))' schema.sql)" \
    https://api.supabase.com/v1/projects/<ref>/database/query
  ```

  Encode the SQL as JSON with a real JSON encoder — hand-built quoting breaks on
  apostrophes inside SQL string literals.
- **`?reveal=true` on `/v1/projects/<ref>/api-keys` requires elevated permissions**
  and returns `Your account does not have the necessary privileges`. Plain
  `GET /api-keys` still returns legacy `anon`/`service_role` keys **masked**
  (`eyJhbG...zZSI`), but the newer `publishable` key is returned in full and works
  as the browser-side key.
- **`auth.users` is NOT covered by your table RLS**, but deleting a user does not
  cascade to `organizations` (that FK points the other way). Clean up test orgs
  explicitly, and check for pre-existing auth users before wiping anything.
- **Never extract one field from pretty-printed multi-line JSON with `sed`.**
  `sed 's/.*"login": *"\([^"]*\)".*/\1/'` on a multi-line JSON body leaves every
  non-matching line unchanged, so the captured variable becomes the whole blob
  (which then corrupts a downstream YAML/config). Extract with
  `grep -o '"login": *"[^"]*"' | head -1 | sed 's/"login": *"\([^"]*\)"/\1/'`
  instead. Applies to any `curl | jq-less` JSON parse, not just Supabase.
- The CLI needs Docker for local `supabase start`; without it, work against a
  linked (hosted) project via `db push` instead of local emulation.
