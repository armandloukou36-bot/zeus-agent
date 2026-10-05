---
name: hermes-voice-stt
description: "Use when diagnosing Hermes voice transcription (STT)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [hermes, stt, voice, transcription, faster-whisper, troubleshooting]
---

# Hermes Voice Transcription (STT) — Setup & Troubleshooting

## When to Use

Use when a user reports that voice transcription (dictation) doesn't work in
Hermes, or when setting up STT from scratch. Trigger on: "voice transcription
doesn't pass", "dictation fails", "STT not working", or a request to enable
voice input.

Hermes transcribes voice messages via the `stt` config section. The default
provider is `local` (faster-whisper), which is free and runs on-machine with no
API key. This skill covers installing the engine, fixing the language, and
verifying the fix in the correct Python environment.

## Diagnose first (cheap, read-only)

```bash
hermes config get stt.enabled      # must be true
hermes config get stt.provider     # empty = default 'local'
hermes config get stt.language     # default 'en' — set to the user's language
hermes config get stt.local.model  # tiny|base|small|medium|large-v3
```

Symptom "voice transcription doesn't work" almost always means one of:
1. The local engine (`faster_whisper`) is not installed.
2. `stt.language` is `en` while the user speaks another language.

## Install the local engine

`faster_whisper` is installed as the **`stt-whisper` extra**, not as a package.
The `pm` module lives inside the Hermes repo and must be run with the Hermes
Python with the repo on `sys.path` — the plain system Python cannot import it.

```bash
cd /root/.hermes/hermes-agent
/root/.hermes/tools/python-3.14.7+*/bin/python3 -c \
  "import sys; sys.path.insert(0,'/root/.hermes/hermes-agent'); import pm; pm.sync_venv(['stt-whisper'], explicit=True)"
```

Resolve the exact Hermes Python path from the launcher shebang:
`head -1 $(which hermes)`.

## Verify in the SELECTED venv, not the tools Python

Hermes runs from a committed venv that is NOT the tools Python. Importing
`faster_whisper` in the tools Python fails even after a successful install.
Resolve the real venv and check there:

```bash
VENV=$(/root/.hermes/tools/python-3.14.7+*/bin/python3 -c \
  "import sys; sys.path.insert(0,'/root/.hermes/hermes-agent'); from pm.environments import selected_venv; from pathlib import Path; print(selected_venv(Path('/root/.hermes/hermes-agent')))")
$VENV/bin/python -c "import faster_whisper; print(faster_whisper.__version__)"
```

## Set the language

```bash
hermes config set stt.language fr   # or the user's language
hermes config get stt.language      # confirm
```

## Pitfalls

- **`hermes pm install stt-whisper` fails with `unknown package`** — `stt-whisper`
  is an *extra* (maps to `faster_whisper`), not a package name. Use
  `pm.sync_venv(['stt-whisper'], explicit=True)` instead.
- **`python -c "import pm; ..."` fails with `ModuleNotFoundError: No module named 'pm'`**
  from the system Python — `pm` is only importable from the Hermes repo with the
  Hermes Python and the repo on `sys.path`. The bundled docs' bare one-liner does
  not work as written.
- **Verifying in the wrong interpreter gives a false negative** — after a
  successful install, `import faster_whisper` still fails in the tools Python.
  Always verify in `selected_venv`.
- **Config changes take effect on a new session** — tell the user to run `/reset`
  (or restart the app) and then `/voice on` or `/voice tts` before testing.
- **Model `base` is coarse for non-English** — if transcription of the user's
  language is imprecise, offer `small` or `medium` (more accurate, slower).

## Delivery

Report the fix as a table (before/after) and state the required user action
(`/reset` + `/voice on`). Offer to test with a real audio file rather than
claiming success from the install alone.
