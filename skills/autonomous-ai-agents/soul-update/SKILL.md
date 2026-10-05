---
name: soul-update
description: "Use when updating the agent's SOUL.md from a spec doc."
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [soul, personality, spec, identity, configuration, hermes]
    category: autonomous-ai-agents
    related_skills: [hermes-agent]
---

# Updating SOUL.md from a spec

SOUL.md is the agent's personality / system prompt, at `<HERMES_HOME>/SOUL.md`
(usually `~/.hermes/SOUL.md`). It is loaded **at the start of each session**, so
an edit takes effect on the next conversation or `/new`, not mid-conversation.

## Procedure

1. **Read the spec.** `read_file` auto-extracts `.docx`, `.md`, `.pdf` (text
   layer) and Office/OpenDocument — no external converter needed. Read the whole
   thing before drafting.
2. **Backup first.**
   `cp ~/.hermes/SOUL.md ~/.hermes/SOUL.md.bak.$(date +%Y%m%d-%H%M%S)`
   Never overwrite the current SOUL.md without a timestamped `.bak`.
3. **Draft faithfully.** Reproduce every section of the spec — role, mission,
   workflow, constraints, permissions, gates (Human Gate), risk matrix, stop
   conditions, failure behavior, evidence/status rules. Write it in the user's
   language. Preserve safety/policy wording verbatim ("never claim success
   without evidence"), do not soften gates.
4. **Show before saving.** Present the full proposed content and WAIT for an
   explicit "ok / validé / enregistre". The user reviews the text before it is
   written; do not save on an ambiguous signal.
5. **Save.** On approval, `write_file` to SOUL.md. If write_file refuses with
   `stale_write_blocked`, `read_file` the current SOUL.md fresh in this task,
   merge if anything changed on disk, then retry the write once.
6. **Tell the user how to reload.** State that SOUL.md loads at session start:
   start a new conversation or `/new` for the new personality to take effect;
   mid-conversation edits do not retroactively change the current context.

## Pitfalls

- write_file will NOT overwrite SOUL.md from a stale copy — it throws
  `stale_write_blocked` unless the file was freshly `read_file`'d in this task.
  The guard re-checks on disk; a fresh read (even if content is unchanged) then
  retry unblocks it.
- SOUL.md edits are invisible to the running session. If the user expects the
  new personality immediately, direct them to a new session rather than
  re-reading the file in place.
- Keep a rollback path explicit: name the `.bak` in your completion report so
  `cp <bak> ~/.hermes/SOUL.md` undoes the change.
