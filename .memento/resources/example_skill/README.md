# Example Skill — Reference Artifact

This directory is a **reference example**, not a deployable skill. It is here
so readers of `skill_guide.md` and `wrapping_a_script.md` can see a complete,
compliant `SKILL.md` and its three executable helper scripts in their natural
shape.

The example is the original `audio/conversion/to_mp3` skill: convert any media
file containing an audio stream into an MP3 with fixed parameters, by calling
`ffmpeg` directly via a helper script. It is preserved here verbatim apart
from having the executable bit set on the helper scripts (which the spec
requires and the original was missing).

## What it shows

- The full required structure under `.memento/skills/<category>/<subcategory>/<skill_name>/`:
  ```
  SKILL.md
  resources/
  ├── validate_input.sh
  ├── ffmpeg_helper.sh
  └── validate_output.sh
  ```
- Frontmatter using every required field in the canonical order.
- A `Procedure` section that calls `validate_input.sh`, the work helper, and
  `validate_output.sh` in turn.
- Helper scripts that:
  - Begin with `#!/usr/bin/env bash` and `set -euo pipefail`.
  - Accept absolute paths and do not depend on the current working directory.
  - Print errors to stderr and exit non-zero on failure.

## What it deliberately does *not* show

- The "wrap an external shellscript" pattern documented in
  `wrapping_a_script.md`. This example wraps `ffmpeg` (a system binary)
  directly, which is also a valid shape. For the external-script-wrapping
  shape, see one of the live skills under `.memento/skills/`, for example
  `.memento/skills/video/download/from_youtube/`.

## Read alongside

- `../skill_guide.md` — the format spec this example conforms to.
- `../wrapping_a_script.md` — the worked-example walkthrough that cites this
  directory as its reference implementation.

## Do not invoke from `skills/`

This directory is intentionally outside `.memento/skills/`. The skill graph
builder (`build_skill_graph.sh`) scans only `.memento/skills/`, so this
example never appears as a node in `.memento/graph/skills_nodes.txt` /
`.memento/graph/skills_edges.txt`.
That is by design — the example is for humans to read, not for the graph to
chain.
