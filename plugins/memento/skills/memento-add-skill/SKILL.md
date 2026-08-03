---
name: memento-add-skill
description: Add a new atomic skill to the memento library and rebuild the skill graph. Use when the user asks to add or create a memento skill (e.g. "add a memento skill for extracting video frames"), or when /memento reported a MISSING SKILL that should now be created.
---

# Add a memento skill

Create one new atomic skill under `$MEMENTO_ENV/skills/` and rebuild the graph. The rebuild is mandatory — a skill that is not in the graph does not exist for chain finding.

## Procedure

0. Resolve the library first — every path below is relative to it:
   ```bash
   MEMENTO_ENV="${MEMENTO_ENV:-$([ -d .memento ] && echo ./.memento || echo "$HOME/.memento")}"
   ```
   A project-local `.memento/` shadows the personal library in `~/.memento`; an already-set `MEMENTO_ENV` wins over both. The new skill lands in whichever library resolves — say which one before creating anything, so the user knows whether this skill becomes project-local or personal.
1. Read `$MEMENTO_ENV/resources/skill_guide.md` — the canonical SKILL.md contract (frontmatter fields, valid TYPE values, required sections, validator and run-logging rules). Follow it exactly.
2. Choose `category/subcategory/skill_name` (all `snake_case`). Check `$MEMENTO_ENV/skills/categories.md`; if the category is new, add a row there.
3. Type the interface first: pick `inputs`/`outputs` from the guide's TYPE list. These types are what the graph builder chains on — use the most specific type that fits (`AUDIO_FILE`, not `FILE`) and unions (`[AUDIO_FILE | VIDEO_FILE]`) only where either is genuinely accepted. If this skill closes a reported gap, its input must match the `MISSING SKILL: input one of {...}` types and its output the `output one of {...}` types — otherwise the chain will not close.
4. Create `$MEMENTO_ENV/skills/<category>/<subcategory>/<skill_name>/`:
   - `SKILL.md` per the guide (frontmatter, title, Purpose, Inputs, Outputs, Procedure, Validation).
   - `resources/validate_input.sh`, `resources/validate_output.sh`, and the helper script the Procedure invokes — `set -euo pipefail`, absolute-path safe, deterministic. Reference them as skill-relative `resources/<name>.sh`, never as a path under the library root, so the skill works from either library.
5. Make the scripts executable: `find "$MEMENTO_ENV/skills/<category>/<subcategory>/<skill_name>" -name "*.sh" -exec chmod +x {} +`
6. Rebuild the graph and verify: `"$MEMENTO_ENV/scripts/build_skill_graph.sh"`. Inside the memento repository run `just test` instead — it rebuilds first, then asserts graph correctness.
7. Report the result: the new node line from `$MEMENTO_ENV/graph/skills_nodes.txt` and its edges from `$MEMENTO_ENV/graph/skills_edges.txt` — i.e. which existing skills the new one can chain with. A new skill with zero edges is worth flagging to the user.
