# EXAMPLE — Wrapping an Existing Tool as an Atomic Skill

> **This document is a worked example, not a spec.** It illustrates how
> to take an existing external tool (in this case the shellscript
> `/Users/flo/scripts/transcribe.sh`) and wrap it as a memento atomic
> skill. The result was the skill at
> `.memento/skills/audio/transcription/whisper_mlx/`. The canonical format
> rules live in `.memento/resources/skill_guide.md`; this document shows
> how to apply them.

Use it as a template when you need to wrap any external tool — shellscript,
binary, Python entrypoint, whatever — as a memento atomic skill.

The single most important rule appears in step 6 below, and is summarised
in the "Things to pay attention to" section. Read both before you write
any code, or you will throw work away (we did).

## Prerequisites — read these first

1. `.memento/resources/skill_guide.md` — the canonical spec for `SKILL.md`,
   the I/O type system (`FILE`, `FOLDER`, `TEXT`, `NUMBER`), the
   `~` optional-parameter marker, and the validator contract.
2. `.memento/resources/example_skill/` — the reference implementation, kept
   as a documentation artifact (not a deployable skill). Copy the shape of
   its `SKILL.md` and its three helper scripts. See its `README.md` for
   what it does and does not illustrate.

Everything below assumes you have read both.

## What the source tool must provide

Wrapping only goes smoothly if the tool you are wrapping behaves like an
interface — i.e. it exposes the things below. If the tool you have in
front of you is missing any of these, fix the tool first; do not paper
over the gap inside the skill.

| The tool must provide                          | Why the skill needs it                                                |
|------------------------------------------------|-----------------------------------------------------------------------|
| A documented CLI (`--help` or equivalent)      | Lets you map arguments onto typed inputs without guessing.            |
| A documented output layout (paths, filenames)  | Lets the skill declare its outputs and `validate_output.sh` find them.|
| Deterministic outputs for given inputs         | The skill's I/O contract is only honest if the tool itself is.        |
| Loud failure (non-zero exit + stderr message)  | The helper just propagates the exit code; nothing else is needed.     |
| Self-contained input validation                | Lets `validate_input.sh` stay minimal — no duplicated rules.          |
| A stable absolute path to invoke it            | The helper hardcodes this path; it must not move.                     |

What `transcribe.sh` provided concretely:

- **Inputs (positional)**: `INPUT [OUTPUT] [NAMESPACE] [MODEL] [LANGUAGE]`.
  Documented as required vs. optional, with a usage block printed on
  `-h`/`--help` or no args.
- **Outputs**: two files written to
  `<OUTPUT>/<NAMESPACE>/<basename(INPUT)>.{txt,srt}`. Stated explicitly
  in the help text.
- **Defaults**: documented default for `OUTPUT`, documented defaulting
  logic for `MODEL` based on `LANGUAGE`.
- **Constraints**: documented enum for `MODEL`, documented `-en` model +
  `LANGUAGE` constraint, documented accepted file extensions.
- **Failure**: red `✗` messages printed to stderr followed by `exit 1`.
- **Location**: a stable absolute path at `/Users/flo/scripts/transcribe.sh`.

That set is the minimum we needed. Anything beyond it (what the tool does
internally, which libraries it calls, where it writes intermediate files)
is irrelevant to the skill and must be ignored — see step 6.

## Things to pay attention to

These are the traps we hit during this session, in priority order. Each
one corresponds to a step below, but is also worth holding in mind
throughout.

1. **The information boundary is the cardinal rule.** The wrapped tool is
   the interface. The skill must not contain references to anything that
   lives past it — no project paths, no internal pipeline stages, no
   library names, no defaulting logic the tool already applies, no enum
   lists the tool already enforces. Every such reference is a leak. We
   wrote the skill twice because we got this wrong the first time.

2. **Atomicity beats completeness.** If the tool bundles multiple
   logical capabilities (e.g. "fetch URL **and** transcribe"), keep
   only the capability that matches the skill's stated purpose and drop
   the rest. The graph composes; the skill should not.

3. **If you would have to mirror a tool default to function, make the
   input required instead.** This is the lever that removes defaulting
   knowledge from the wrapper. We applied it to `OUTPUT_DIR`: the tool
   has an internal default, but the skill cannot know that default
   without leaking it, so the skill demands the user supply it.

4. **Validators check the skill's contract, not the tool's.** The tool
   already validates its own inputs. Duplicating its rules in
   `validate_input.sh` is a leak (and rots when the tool changes).

5. **Helpers communicate outputs via `KEY=value` stdout.** When the
   skill declares multiple outputs, the helper must print
   `OUTPUT_X=<path>` lines on stdout so the procedure can capture them
   and pass them to `validate_output.sh`.

6. **Redirect the wrapped tool's stdout to stderr.** Otherwise its
   progress chatter contaminates the helper's own `KEY=value` lines and
   the procedure cannot parse them.

7. **Output paths must be derivable from the tool's documented public
   behaviour, not from its internal layout.** For `transcribe.sh` the
   layout `<OUTPUT>/<NAMESPACE>/<basename>.{txt,srt}` is documented in
   `--help`, which makes it fair game. If a tool's output paths are
   only knowable by inspecting its internals, push the tool to document
   them before you wrap it.

8. **All helpers must accept absolute paths and use `set -euo pipefail`.**
   This is in `skill_guide.md`; it is non-optional. Helpers that depend
   on the current working directory are malformed.

## The starting point

An existing tool you want to expose as an atomic skill. In this example:
`/Users/flo/scripts/transcribe.sh`, which transcribes a media file into a
cleaned `.txt` and `.srt` pair.

## The end state

A new directory under `.memento/skills/<category>/<subcategory>/<name>/`
containing exactly four files:

```
SKILL.md
resources/validate_input.sh
resources/<your-tool>_helper.sh
resources/validate_output.sh
```

The skill calls the underlying script and **knows nothing about what
happens past it**.

## Step 1 — Read the script's interface

Run `<script> --help`, or read the usage block at the top of the file. You
are looking for:

- The positional / named arguments and which are required vs optional.
- The output: where files are written, what they are named, how many.
- Any documented defaults the script applies when an argument is omitted.

For `transcribe.sh` this gave us:

| CLI arg     | Required? | Type            | Notes                         |
|-------------|-----------|-----------------|-------------------------------|
| `INPUT`     | yes       | file path / URL | accepts many media formats    |
| `OUTPUT`    | no        | folder          | has an internal default       |
| `NAMESPACE` | no        | text            | subfolder under `OUTPUT`      |
| `MODEL`     | no        | text (enum)     | internal default logic        |
| `LANGUAGE`  | no        | text (ISO code) | constraint with `-en` models  |

Output: `<OUTPUT>/<NAMESPACE>/<basename(INPUT)>.{txt,srt}`.

Do not read further into the script than its public interface. Whatever
the script does internally is none of the skill's business (see step 6).

## Step 2 — Choose where the skill lives

Decide `<category>/<subcategory>/<skill_name>/`.

- Pick an existing category from `.memento/skills/categories.md` if one
  fits. Only register a new top-level category if no existing one applies.
- Subcategory is a verb or domain noun (`conversion`, `download`,
  `transcription`).
- Skill name is `snake_case`. Either describes the target (`to_mp3`,
  `to_wav`) or names the method (`from_youtube`, `whisper_mlx`).

For our example: `audio/transcription/whisper_mlx/`. We added a new
subcategory `transcription` under the existing `audio` category. No change
to `categories.md` was needed because that file only tracks top-level
categories.

## Step 3 — Map the CLI to typed I/O

Translate each CLI argument into a frontmatter entry of the form
`[~]NAME::TYPE` (`~` = optional). Allowed types: `FILE`, `FOLDER`, `TEXT`,
`NUMBER`.

Rules of thumb:

- A local file path that must exist → `FILE`.
- A directory → `FOLDER`.
- An enum, ISO code, or free-form string → `TEXT`.
- A numeric scalar → `NUMBER`.
- Outputs follow the same vocabulary.

For `transcribe.sh` we mapped:

```yaml
inputs:
  - INPUT_PATH::FILE
  - OUTPUT_DIR::FOLDER
  - ~NAMESPACE::TEXT
  - ~MODEL::TEXT
  - ~LANGUAGE::TEXT
outputs:
  - OUTPUT_TXT::FILE
  - OUTPUT_SRT::FILE
```

Note `OUTPUT_DIR` is **required** in the skill even though it is optional
in the script. The reason is in step 6.

## Step 4 — Draw the atomicity boundary

Real scripts often do more than one logical thing. An atomic skill does
one. If your script bundles multiple capabilities, keep the one that
matches the skill's stated purpose and **drop the rest** — they belong in
other skills that can be chained via the graph.

`transcribe.sh` accepts both local file paths **and** YouTube URLs. We
dropped URL handling from the skill's interface (`INPUT_PATH::FILE`, not
`INPUT::TEXT`) because the existing `video/download/from_youtube` skill
already covers that step. The URL flow becomes the chain
`from_youtube → whisper_mlx`.

Atomic skills compose. Non-atomic skills duplicate.

## Step 5 — Decide the shape of the outputs

If the script produces multiple artefacts, you have two options:

- Expose each artefact as its own typed output (e.g.
  `OUTPUT_TXT::FILE`, `OUTPUT_SRT::FILE`). Downstream skills can consume
  them individually via the graph.
- Expose the containing directory as `OUTPUT_DIR::FOLDER`. Simpler but
  loses per-file edges in the skill graph.

We chose per-file outputs. The helper prints `KEY=value` lines on stdout
so the procedure can capture the resulting paths and pass them to
`validate_output.sh`.

## Step 6 — Lock down the information boundary (the rule)

**The wrapped script is the interface. The skill must know nothing about
what lives past it.**

This means the skill must not contain, refer to, or rely on:

- Internal pipeline stages of the script (ffmpeg, mlx-whisper, the
  cleaner, intermediate WAV files, temp directories, …).
- Project directories or file locations belonging to the script.
- Default values the script applies when an argument is omitted.
- Enum lists, language constraints, format restrictions the script
  enforces.
- The names of tools or libraries the script calls.

The pattern that makes this concrete: **if the script has a default for
an input and you would have to mirror that default in your skill to
function, make the skill require that input instead.** That removes the
defaulting knowledge from the wrapper entirely.

We applied this to `OUTPUT_DIR`. The script defaults it to a path inside
its own project tree. Mirroring that default in our helper would leak the
project's location into the skill. So we made `OUTPUT_DIR` required in
`SKILL.md`, and the skill is now ignorant of where the script would put
files by default.

## Step 7 — Write `SKILL.md`

Follow the section order from `skill_guide.md`: frontmatter → H1 →
Purpose → Inputs → Outputs → Procedure → Validation.

Keep each section honest to the boundary from step 6:

- **Summary / Purpose**: say what the skill produces and that it
  delegates to the wrapped tool. Do not describe how the tool works.
- **Inputs**: state what the skill itself requires (paths must exist,
  etc.). For pass-through arguments, say "passed through; see
  `<tool> --help`" instead of repeating the tool's allowed values.
- **Outputs**: state the paths your helper will print and what they
  contain at the artefact level (cleaned plain text, SRT, etc.). Do not
  describe intermediate processing.
- **Procedure**: three numbered steps — `validate_input.sh`, helper,
  `validate_output.sh`.

See the final result at
`.memento/skills/audio/transcription/whisper_mlx/SKILL.md`.

## Step 8 — Write `validate_input.sh`

This script validates **the skill's own contract**, not the wrapped
tool's. The wrapped tool will fail loudly on its own invalid inputs.

Per `skill_guide.md`:

- Shebang `#!/usr/bin/env bash`.
- `set -euo pipefail`.
- Strict argument count check; exit `2` on usage error.
- Each failure prints to stderr and exits non-zero.
- Accept only absolute paths; do not depend on the current working
  directory.

What we validate for `whisper_mlx`:

- `INPUT_PATH` non-empty, file exists, file readable.
- `OUTPUT_DIR` non-empty; if it already exists, it is a directory.

What we deliberately do **not** validate (the script handles all of
these):

- Whether the file extension is supported.
- Whether `MODEL` is a known model.
- Whether `LANGUAGE` is consistent with the chosen model.
- Whether the input contains an audio stream.

Lean validators are correct validators. Duplicated validation is leaked
knowledge.

## Step 9 — Write the helper

The helper is a thin pass-through. Its only jobs are:

1. Argument-count check and required-argument check.
2. Invoke the wrapped script with the user's arguments.
3. Print `KEY=value` lines on stdout naming the produced output paths so
   `validate_output.sh` can be called on them.

What the helper does **not** do:

- Apply defaults the wrapped tool already applies.
- Reference any path or tool the wrapped script uses internally.
- Re-validate the wrapped tool's CLI surface.

For `whisper_mlx` the helper computes the output paths using only the
wrapped tool's documented public output convention
(`<OUTPUT_DIR>/<NAMESPACE>/<BASE>.{txt,srt}`). It then invokes
`transcribe.sh` and prints the two `KEY=value` lines.

Redirect the wrapped tool's stdout to stderr (`>&2`) so it does not
contaminate the helper's own `KEY=value` lines on stdout.

## Step 10 — Write `validate_output.sh`

This script confirms the skill produced what it promised in `SKILL.md`'s
Outputs section. For `whisper_mlx`: both output files exist, are
non-empty, and have the declared extensions.

Same conventions as `validate_input.sh` (shebang, `set -euo pipefail`,
arg count, stderr on failure).

## Step 11 — Set the executable bit

```bash
chmod +x .memento/skills/<cat>/<sub>/<name>/resources/*.sh
```

`skill_guide.md` requires this. Skills with non-executable helpers are
malformed.

## Step 12 — Audit the boundary

Before declaring the skill done, walk every file you wrote and tag each
line of knowledge as either:

- **Interface** — the wrapped script's documented public CLI surface
  (entrypoint path, argument order, output layout).
- **Internal** — anything past that.

Every "internal" tag is a leak. Examples of leaks we removed during this
build:

- The default `OUTPUT` directory path used by `transcribe.sh` internally.
- The list of `MODEL` values the script accepts.
- The `-en` model + `LANGUAGE` constraint.
- The accepted file-extension list.
- The names of the underlying tools (ffmpeg, mlx-whisper, cleaner script).
- The description of the internal pipeline stages.

If the boundary is clean, the skill should still work unchanged if the
wrapped tool swaps its internal implementation for a completely
different one, as long as its CLI surface is preserved.

## Step 13 — Regenerate the skill graph

```bash
.memento/scripts/build_skill_graph.sh
```

This re-parses every `SKILL.md` and refreshes
`.memento/graph/skills_nodes.txt` and `.memento/graph/skills_edges.txt`.
The new skill is now visible to the Dijkstra-based chain finder.

## Checklist

Before considering the skill done, confirm:

- [ ] `SKILL.md` matches the section order in `skill_guide.md`.
- [ ] Frontmatter `inputs:` and `outputs:` use `[~]NAME::TYPE` correctly.
- [ ] Three helper scripts exist under `resources/`, all executable.
- [ ] All helpers use `set -euo pipefail` and accept absolute paths.
- [ ] `validate_input.sh` validates only the skill's own contract.
- [ ] No file in the skill mentions any tool, path, or behaviour past
      the wrapped script.
- [ ] The wrapped script's default values are not duplicated anywhere in
      the skill (inputs that depended on a default were made required).
- [ ] `build_skill_graph.sh` has been re-run after the new skill was
      added.
