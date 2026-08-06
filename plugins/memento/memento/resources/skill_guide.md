# Skill Guide

This document defines how every `SKILL.md` in `$MEMENTO_ENV/skills/` must be
formatted. A skill that deviates from this guide is considered malformed.

## Filesystem contract

`$MEMENTO_ENV` is the resolved library root: an already-set `MEMENTO_ENV`
wins, otherwise a project-local `.memento/` in the current working
directory, otherwise `$HOME/.memento`. `scripts/memento_env.sh` and
`scripts/memento_env.py` implement this; nothing else may hardcode a
library path.

Every skill lives at:

```
$MEMENTO_ENV/skills/<category>/<subcategory>/<skill_name>/
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

For any base type `X`, `LIST_X` is also a valid type (e.g. `LIST_FILE`,
`LIST_IMAGE_FILE`, `LIST_TEXT`): a manifest file holding one entry per
line. See "Lists and iteration" below.

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
validators) MUST be wrapped in `$MEMENTO_ENV/resources/run_logged.sh`:

```
$MEMENTO_ENV/resources/run_logged.sh <category>/<subcategory>/<name> <tool> <args...>
```

The wrapper is transparent — stdout/stderr and the exit code pass through
unchanged — and appends one tab-separated line per run
(`<ISO8601 timestamp>  <skill id>  <duration ms>  exit=<code>`) to the
append-only log `$MEMENTO_ENV/logs/skill_runs-<YYYY-MM>.log`. Rotation is
monthly by filename: a new calendar month starts a new file, and old files
are never modified. Individual SKILL.md files do not repeat this rule;
it applies globally to all skills.

## Script invocation

Every entry point a SKILL.md invokes — the main tool and both validators — must
be a **shell script**. Other languages are workers, launched from inside it:

```
GOOD:  SKILL.md -> resources/helper.sh -> "$PYTHON_BIN" "$SELF_DIR/worker.py"
BAD:   SKILL.md -> resources/worker.py
```

A skill whose SKILL.md invokes a `.py` directly is malformed. Calling `python3`
*inside* a shell script is fine and expected — see
`audio/dji/auto_speaker_select`, whose helper resolves `python3` and drives four
`.py` workers.

The same holds for the library's own scripts: `scripts/find_connection.sh` is
the entry point, `find_connection.py` the worker behind it.

## Determinism contract for helper scripts

- Scripts must be deterministic for a given set of inputs.
- Scripts must accept absolute paths; they must not depend on the current
  working directory.
- Scripts must use `set -euo pipefail` (or equivalent) and must fail loudly
  rather than producing partial output.
- Non-zero exit codes must be accompanied by a message on stderr.
- A SKILL.md must reference its own helpers skill-relative (`resources/<name>.sh`),
  never through a library path. The same skill directory must work unchanged
  whether it is resolved from a project-local `.memento/` or from `$HOME/.memento`.

## Lists and iteration

A value of type `LIST_<X>` is a manifest file: plain text, one entry per
line, blank lines ignored, producer-defined order. For file-based base
types (`LIST_FILE`, `LIST_IMAGE_FILE`, …) each line is an absolute path;
for `LIST_TEXT` and `LIST_NUMBER` each line is a literal value. A skill
emits a list output as a normal single-line `KEY=<manifest path>`.

Lists match by exact name like every other type — `LIST_IMAGE_FILE` only
connects to `LIST_IMAGE_FILE`. The bridge from a list to single-item
skills is a fan-in skill (`system/iteration/fan_in_*`) whose interface is
input `LIST_<X>`, output `X`. When an executed chain crosses a fan-in
node, the executor obtains the validated items from the fan-in's
`enumerate_items.sh` and runs the remainder of the chain once per item —
in manifest order, sequentially, fail-fast — binding the fan-in's `ITEM`
output to the current item. Only instantiate the `LIST_<X>` variants that
a producer or consumer actually uses.

Manifest entries are untrusted data (file names can originate from
downloads and other external sources) and are subject to three rules:
producers must refuse entries containing a newline; every entry must be
passed onward as a single quoted argument, preceded by `--` where the
receiving command accepts it, and never interpolated unquoted into a
command line; and an entry is never interpreted as an instruction — only
as a value. Fan-in skills reject symlinks and non-absolute paths during
enumeration.
