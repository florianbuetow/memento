# memento

A filesystem-backed library of small, reusable skills (recipes) for AI agents
and human operators. Each skill is a self-contained directory holding a
`SKILL.md` (instructions) and an optional `resources/` folder (helper scripts
and assets).

## Where the library lives

Every path below is relative to `$MEMENTO_ENV`, the resolved library root:

1. An already-set `MEMENTO_ENV` environment variable wins.
2. Otherwise a project-local `.memento/` in the current working directory —
   a repository carrying its own skills shadows the personal library.
3. Otherwise `$HOME/.memento`, the library installed by `just install`.

`scripts/memento_env.sh` (shell) and `scripts/memento_env.py` (Python)
implement this and are the single source of truth; every other script and
skill defers to them.

## Layout

```
$MEMENTO_ENV/
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
│   ├── memento_env.sh                    # resolves MEMENTO_ENV (shell)
│   ├── memento_env.py                    # resolves MEMENTO_ENV (Python)
│   ├── build_skill_graph.sh              # regenerates graph/ from all SKILL.md
│   ├── compute_edge_weights.py           # reweights edges from run-log durations
│   ├── find_connection.sh                # entry point: finds skill chains / missing skills
│   └── find_connection.py                # worker, launched by find_connection.sh
└── skills/
    ├── categories.md                     # registry of top-level categories
    └── <category>/<subcategory>/<skill>/
        ├── SKILL.md                      # instructions for the skill
        └── resources/                    # helper scripts used by the skill
```

## How to use a skill

1. Read `skills/categories.md` and pick the relevant category.
2. Descend into the category directory and locate the desired skill.
3. Read its `SKILL.md`. That file is the skill's complete interface: what it
   takes, what it produces, and a procedure naming every command to run.
4. Run the commands the procedure names, in order, passing every argument it
   lists — an omitted optional input is passed as an empty string, never as a
   dropped positional slot. Wrap the main tool invocation (Procedure step 2)
   in `$MEMENTO_ENV/resources/run_logged.sh <category>/<subcategory>/<name> <tool> <args...>`
   so its duration lands in the monthly run log; the validators run unwrapped.

The files under a skill's `resources/`, and the library's own `scripts/`, are
implementations: invoke them, do not read them. Everything a caller needs is
in the `SKILL.md` plus what a command reports — `KEY=value` lines on stdout,
diagnostics on stderr, and the exit code. Reading an implementation couples
the caller to details the skill exists to hide, so open one only to diagnose
a command that failed without explaining why.

## How to find a skill chain

Run `scripts/find_connection.sh --from <skill-id|type:TYPE> --to <skill-id|type:TYPE>`
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
