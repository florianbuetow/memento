# Memento

Memento gives an AI agent a procedural memory: atomic, reusable skills that can be chained into workflows via a typesystem that matches outputs to inputs. State a goal in plain language and memento assembles the skills to reach it - or names the skill you need to build.

## Key Properties

- **Procedural agent memory** - stored how-to knowledge the agent runs instead of re-deriving it every time.
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

## Installation

The five memento slash commands ship as a Claude Code plugin. This repository is
also the marketplace that publishes it, so install it straight from GitHub.

```bash
# Add the marketplace (one time)
claude plugin marketplace add florianbuetow/memento

# Install the plugin
claude plugin install memento
```

Restart Claude Code after installing, then set up the library the commands
operate on:

```
/memento-install
```

That needs no clone and no repository — the plugin carries the memento
machinery and installs it to `~/.memento`. The library starts **empty**: atomic
skills are personal, so none ship with the plugin. Add your own with
`/memento-add-skill`. Re-running `/memento-install` is the upgrade path — the
machinery is replaced, your skills and run logs are not. See
[Where the skill library lives](#where-the-skill-library-lives) for how a
project-local `.memento/` shadows it.

### Updating

```bash
# Update to the latest version
claude plugin marketplace update memento

# Verify the installed version
find ~/.claude/plugins -name "plugin.json" -path "*memento*" -exec grep version {} \;
```

<details>
<summary>Manual / Development Installation</summary>

```bash
git clone https://github.com/florianbuetow/memento.git
cd memento
# Load the plugin for this session only
claude --plugin-dir ./plugins/memento
```

</details>

## How to use

Ask Claude with a slash command:

| Command | What it does |
|---------|--------------|
| `/memento` | Describe a goal → get the chain of skills that achieves it (or the one skill you're missing). |
| `/memento-add-skill` | Add a new skill. |
| `/memento-update-skill` | Change an existing skill. |
| `/memento-remove-skill` | Remove a skill. |
| `/memento-rebuild-graph` | Rebuild the skill graph. |
| `/memento-install` | Install the memento machinery to `~/.memento` (also the upgrade path). |

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
│       ├── justfile               # install recipe, runs from the plugin cache
│       ├── memento/               # bundled machinery, no atomic skills
│       └── skills/                # Claude Code slash commands
│           ├── memento/           # /memento - plan a chain for a goal
│           ├── memento-add-skill/
│           ├── memento-update-skill/
│           ├── memento-remove-skill/
│           ├── memento-rebuild-graph/
│           └── memento-install/
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
