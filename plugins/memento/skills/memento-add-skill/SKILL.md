---
name: memento-add-skill
description: Add a new atomic skill to the .memento library and rebuild the skill graph. Use when the user asks to add or create a memento skill (e.g. "add a memento skill for extracting video frames"), or when /memento reported a MISSING SKILL that should now be created.
---

# Add a memento skill

Create one new atomic skill under `.memento/skills/` and rebuild the graph. The rebuild is mandatory — a skill that is not in the graph does not exist for chain finding.

## Procedure

1. Read `.memento/resources/skill_guide.md` — the canonical SKILL.md contract (frontmatter fields, valid TYPE values, required sections, validator and run-logging rules). Follow it exactly.
2. Choose `category/subcategory/skill_name` (all `snake_case`). Check `.memento/skills/categories.md`; if the category is new, add a row there.
3. Type the interface first: pick `inputs`/`outputs` from the guide's TYPE list. These types are what the graph builder chains on — use the most specific type that fits (`AUDIO_FILE`, not `FILE`) and unions (`[AUDIO_FILE | VIDEO_FILE]`) only where either is genuinely accepted. If this skill closes a reported gap, its input must match the `MISSING SKILL: input one of {...}` types and its output the `output one of {...}` types — otherwise the chain will not close.
4. Create `.memento/skills/<category>/<subcategory>/<skill_name>/`:
   - `SKILL.md` per the guide (frontmatter, title, Purpose, Inputs, Outputs, Procedure, Validation).
   - `resources/validate_input.sh`, `resources/validate_output.sh`, and the helper script the Procedure invokes — `set -euo pipefail`, absolute-path safe, deterministic.
5. Make the scripts executable: `find .memento/skills/<category>/<subcategory>/<skill_name> -name "*.sh" -exec chmod +x {} +`
6. Rebuild the graph and verify: `just test` (it runs `just build` first, then asserts graph correctness).
7. Report the result: the new node line from `.memento/graph/skills_nodes.txt` and its edges from `.memento/graph/skills_edges.txt` — i.e. which existing skills the new one can chain with. A new skill with zero edges is worth flagging to the user.
