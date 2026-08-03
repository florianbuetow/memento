---
name: memento-rebuild-graph
description: Rebuild the memento skill graph from all SKILL.md files. Use when the user asks to rebuild or refresh the skill graph, after any manual edit under the memento skills directory, or when tools report the graph files are out of sync.
---

# Rebuild the skill graph

Regenerate `$MEMENTO_ENV/graph/skills_nodes.txt` and `$MEMENTO_ENV/graph/skills_edges.txt` from the frontmatter of every `SKILL.md` under `$MEMENTO_ENV/skills/`.

## Procedure

0. Resolve the library first — every path below is relative to it:
   ```bash
   MEMENTO_ENV="${MEMENTO_ENV:-$([ -d .memento ] && echo ./.memento || echo "$HOME/.memento")}"
   ```
   A project-local `.memento/` shadows the personal library in `~/.memento`; an already-set `MEMENTO_ENV` wins over both. Report which library was rebuilt — rebuilding the local one leaves the personal graph untouched, and vice versa.
1. Capture the current counts, if the files exist: `wc -l "$MEMENTO_ENV/graph/skills_nodes.txt" "$MEMENTO_ENV/graph/skills_edges.txt"`
2. Run `"$MEMENTO_ENV/scripts/build_skill_graph.sh"`. The builder prints the resolved paths and the fresh node and edge counts. Inside the memento repository `just build` does the same thing.
3. If the counts changed, summarize what appeared or disappeared (compare the node ids; `git diff` the graph directory when the files are tracked).
4. Inside the memento repository, run `just test` to assert the rebuilt graph is correct and the committed files are in sync. Outside it there is no test suite — verifying the counts from step 3 is the check.
