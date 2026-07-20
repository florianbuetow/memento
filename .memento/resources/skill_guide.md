# Skill Guide

This document defines how every `SKILL.md` in `.memento/skills/` must be
formatted. A skill that deviates from this guide is considered malformed.

## Filesystem contract

Every skill lives at:

```
.memento/skills/<category>/<subcategory>/<skill_name>/
```

The directory MUST contain:

- `SKILL.md` — the skill specification (see below).

The directory MAY contain:

- `resources/` — helper scripts and assets used by the skill. All shell helpers
  must have the executable bit set.

## Naming

- Categories, subcategories, and skill names use `snake_case`.
- Categories are short, plural nouns when possible (`audio`, `video`, `text`).
- Helper scripts are lowercase with a `.sh` extension.

## Required structure of SKILL.md

A `SKILL.md` must contain the following, in order:

### 1. YAML frontmatter

```yaml
---
name: <skill_name in snake_case>
category: <top-level category>
subcategory: <subcategory>
summary: <one-line description, < 120 chars>
inputs:
  - <input parameter name>::<TYPE>
  - ...
outputs:
  - <output parameter name>::<TYPE>
  - ...
input_validation_script: resources/validate_input.sh
output_validation_script: resources/validate_output.sh
---
```

Valid `<TYPE>` values: `FOLDER`, `FILE`, `AUDIO_FILE`, `VIDEO_FILE`,
`IMAGE_FILE`, `TEXT_FILE`, `TEXT_FILE_TXT`, `TEXT_FILE_SRT`, `TEXT`,
`NUMBER`, `TMUX_SESSION`.

`TEXT_FILE` is a plain-text file of unspecified format; `TEXT_FILE_<EXT>`
variants (`TEXT_FILE_TXT`, `TEXT_FILE_SRT`) pin the concrete format.

Prefer the specific file types over plain `FILE`: use `AUDIO_FILE` /
`VIDEO_FILE` when the parameter is known to be an audio or video file, and
plain `FILE` only when the format genuinely does not matter. Types match by
exact name — `FILE` is not a supertype of `AUDIO_FILE`.

A `<TYPE>` may also be a union of alternatives, written in square brackets
with `|` separators: `[AUDIO_FILE | VIDEO_FILE]`. A union means the parameter
accepts a value of any one of the listed types.

Prefix a parameter name with `~` to mark it optional (e.g., `~OUTPUT_PATH::FILE`). Parameters without the prefix are required.

### 2. Title

A single H1 heading describing the skill in human-readable terms.

### 3. ## Purpose

One paragraph. What problem the skill solves and when to apply it.

### 4. ## Inputs

A bulleted list. For each input, specify:

- Name (uppercase identifier, e.g. `INPUT_PATH`)
- Type (string, integer, path, …)
- Constraints (must exist, must be readable, allowed values, …)

### 5. ## Outputs

A bulleted list of artifacts the skill produces, with their location and type.

### 6. ## Procedure

A numbered list of steps. Each step is either an imperative instruction or a
direct invocation of a script under `resources/`, with explicit arguments.

### 7. ## Validation

Every skill MUST define two helpers under `resources/`:

- `validate_input.sh` — exits 0 iff the supplied inputs satisfy the contract.
- `validate_output.sh` — exits 0 iff the produced output satisfies the contract.

The Procedure section must call `validate_input.sh` before the main work and
`validate_output.sh` after it.

## Run logging

Every execution of a skill's main tool (the Procedure's step 2 — not the
validators) MUST be wrapped in `.memento/resources/run_logged.sh`:

```
.memento/resources/run_logged.sh <category>/<subcategory>/<name> <tool> <args...>
```

The wrapper is transparent — stdout/stderr and the exit code pass through
unchanged — and appends one tab-separated line per run
(`<ISO8601 timestamp>  <skill id>  <duration ms>  exit=<code>`) to the
append-only log `.memento/logs/skill_runs-<YYYY-MM>.log`. Rotation is
monthly by filename: a new calendar month starts a new file, and old files
are never modified. Individual SKILL.md files do not repeat this rule;
it applies globally to all skills.

## Determinism contract for helper scripts

- Scripts must be deterministic for a given set of inputs.
- Scripts must accept absolute paths; they must not depend on the current
  working directory.
- Scripts must use `set -euo pipefail` (or equivalent) and must fail loudly
  rather than producing partial output.
- Non-zero exit codes must be accompanied by a message on stderr.
