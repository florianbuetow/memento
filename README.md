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

## Where the skill library lives

Every script and skill resolves `MEMENTO_ENV`, the library root, in this order:

1. An already-set `MEMENTO_ENV` environment variable — an explicit override.
2. A project-local `.memento/` in the current directory — a repository that
   carries its own skills shadows your personal library.
3. `$HOME/.memento` — the personal library that `just install` writes.

That is what makes the skills work outside this repository: run `just install`
once and `/memento` resolves your library from any directory. Keep skills you
do not want to commit in `~/.memento/skills/` — they stay out of the repo and
are still found everywhere.

`just env` prints the resolved path and the reason it was chosen.

## Install the Claude Code skills

The five memento slash commands ship as a Claude Code plugin. This repository is
also the marketplace that publishes it, so install it straight from GitHub:

```
/plugin marketplace add florianbuetow/memento
/plugin install memento@memento
```

`marketplace add` reads [`.claude-plugin/marketplace.json`](.claude-plugin/marketplace.json)
at the repository root, which points at the plugin in
[`plugins/memento/`](plugins/memento). The plugin name and the marketplace name
are both `memento`, hence `memento@memento`. Run `/plugin` any time to list,
update, or remove what you installed.

To work on the plugin itself, add your checkout as the marketplace instead — the
skills then load from your working tree:

```
/plugin marketplace add ~/path/to/memento
/plugin install memento@memento
```

The skills operate on a skill library, so you need one of those too: run
`just install` for a personal `~/.memento`, or keep a project-local `.memento/`.
See [Where the skill library lives](#where-the-skill-library-lives).

## How to use

Ask Claude with a slash command:

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
├── .claude-plugin/
│   └── marketplace.json           # the marketplace that publishes the plugin
├── plugins/
│   └── memento/                   # the plugin, installed via the marketplace
│       ├── .claude-plugin/
│       │   └── plugin.json        # plugin manifest
│       └── skills/                # Claude Code slash commands
│           ├── memento/           # /memento - plan a chain for a goal
│           ├── memento-add-skill/
│           ├── memento-update-skill/
│           ├── memento-remove-skill/
│           └── memento-rebuild-graph/
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
│   │   ├── memento_env.sh          # resolves MEMENTO_ENV (shell)
│   │   ├── memento_env.py          # resolves MEMENTO_ENV (Python)
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
├── justfile                       # init / build / test / install / env
├── CHANGELOG.md
├── LICENSE
└── README.md
```

## Details

For how it all works, see the presentation: **[`docs/memento_presentation.html`](docs/memento_presentation.html)**.

## License

[MIT](LICENSE) © 2026 Florian Buetow.
