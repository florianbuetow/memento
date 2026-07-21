# Memento

Memento gives an AI agent a procedural memory: atomic, reusable skills that can be chained into workflows via a typesystem that matches outputs to inputs. State a goal in plain language and memento assembles the skills to reach it - or names the skill you need to build.

## Key Properties

- **Procedural agent memory** - stored how-to-do actinos the agent can run instead of re-deriving it every time.
- **Chainable atomic skills** - each skill does exactly one thing, with typed inputs and outputs.
- **Deterministic skill chaining** - every skill validates its inputs and outputs and runs the same way each time.
- **Graph search** - Dijkstra finds the shortest chain of skills for a goal, or flags missing skills if there is a gap.

## Setup

**Requirements:** [`just`](https://github.com/casey/just), `awk`, and `python3`.

```bash
git clone https://github.com/florianbuetow/memento
cd memento

just init      # verify tools
just build     # generate the skill graph
just test      # check the graph is valid
just install   # copy .memento to ~/.memento
```

Run `just` any time to see all commands.

## How to use

Memento ships with Claude Code skills in `.claude/skills/`. Ask Claude with a slash command:

| Command | What it does |
|---------|--------------|
| `/memento` | Describe a goal → get the chain of skills that achieves it (or the one skill you're missing). |
| `/memento-add-skill` | Add a new skill. |
| `/memento-update-skill` | Change an existing skill. |
| `/memento-remove-skill` | Remove a skill. |
| `/memento-rebuild-graph` | Rebuild the skill graph. |

**Example** - ask `/memento`:

> *"download this video and get me the transcript"*

Memento finds the chain of skills, then walks you through running it - or tells you exactly which skill to build if one is missing.

## Layout

```
memento/
├── .claude/
│   └── skills/                    # Claude Code slash commands
│       ├── memento/               # /memento - plan a chain for a goal
│       ├── memento-add-skill/
│       ├── memento-update-skill/
│       ├── memento-remove-skill/
│       └── memento-rebuild-graph/
├── .memento/
│   ├── index.md                   # overview / entry point
│   ├── skills/                    # atomic skills, grouped by category
│   │   ├── categories.md
│   │   ├── agents/
│   │   ├── audio/
│   │   │   └── transcription/whisper_mlx/
│   │   │       ├── SKILL.md        # typed contract + procedure
│   │   │       └── resources/      # tool + validation scripts
│   │   ├── images/
│   │   ├── system/
│   │   ├── text/
│   │   └── video/
│   ├── scripts/                   # build + query the skill graph
│   │   ├── build_skill_graph.sh
│   │   ├── compute_edge_weights.py
│   │   ├── dijkstra.py
│   │   └── find_connection.py
│   ├── graph/                     # generated skill graph
│   │   ├── skills_nodes.txt
│   │   └── skills_edges.txt
│   ├── resources/                 # shared helpers + skill guide
│   │   ├── skill_guide.md
│   │   └── run_logged.sh
│   └── logs/                      # per-run execution logs
├── docs/
│   └── memento_presentation.html
├── tests/
├── justfile                       # init / build / test / install
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Details

For how it all works, see the presentation: **[`docs/memento_presentation.html`](docs/memento_presentation.html)**.

## License

[MIT](LICENSE) © 2026 Florian Buetow.
