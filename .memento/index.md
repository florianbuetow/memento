# memento

A filesystem-backed library of small, reusable skills (recipes) for AI agents
and human operators. Each skill is a self-contained directory holding a
`SKILL.md` (instructions) and an optional `resources/` folder (helper scripts
and assets).

## Layout

```
.memento/
├── index.md                              # this file — top-level entry point
├── graph/
│   ├── skills_nodes.txt                  # generated: one line per skill
│   └── skills_edges.txt                  # generated: chainable-skill edges
├── logs/
│   └── skill_runs-<YYYY-MM>.log          # append-only run log, rotated monthly
├── resources/
│   ├── skill_guide.md                    # canonical format for every SKILL.md
│   └── run_logged.sh                     # timing wrapper for skill tool runs
├── scripts/
│   ├── build_skill_graph.sh              # regenerates graph/ from all SKILL.md
│   ├── compute_edge_weights.py           # reweights edges from run-log durations
│   └── find_connection.py                # finds skill chains / missing skills
└── skills/
    ├── categories.md                     # registry of top-level categories
    └── <category>/<subcategory>/<skill>/
        ├── SKILL.md                      # instructions for the skill
        └── resources/                    # helper scripts used by the skill
```

## How to use a skill

1. Read `skills/categories.md` and pick the relevant category.
2. Descend into the category directory and locate the desired skill.
3. Read its `SKILL.md` to learn the inputs, outputs, and procedure.
4. Invoke the helper scripts under that skill's `resources/` directory.
   Wrap the main tool invocation (Procedure step 2) in
   `resources/run_logged.sh <category>/<subcategory>/<name> <tool> <args...>`
   so its duration lands in the monthly run log (see the "Run logging"
   section of `resources/skill_guide.md`).

## How to find a skill chain

Run `scripts/find_connection.py --from <skill-id|type:TYPE> --to <skill-id|type:TYPE>`
to search the generated graph — Dijkstra forward from the start and backward
from the goal. It prints the shortest chain of skills (`CHAIN:` / `STEP:`
lines) or, when no chain exists, explicitly flags the missing atomic skill
(`MISSING SKILL:` lines) with the input/output types it must have. Rebuild
the graph first if skills changed.

## How to add a skill

1. Read `resources/skill_guide.md` to understand the required SKILL.md format.
2. Create the skill directory at
   `skills/<category>/<subcategory>/<skill_name>/`.
3. Add `SKILL.md` and any helper scripts under `resources/`.
4. Register a new category in `skills/categories.md` if one does not exist.
5. Rebuild the graph with `scripts/build_skill_graph.sh` so the new skill
   appears in `graph/`. The same applies after updating or removing a skill.
