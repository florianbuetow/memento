# Memento

A filesystem-backed library of small, chainable skills for AI agents.

## About

Memento is a **procedural memory** for an AI agent: a set of atomic skills, each doing one thing (download a video, transcribe audio, summarize text, …). From a plain-language goal it chains the right skills together to get the job done - or tells you which skill is still missing, so the library grows exactly where you need it.

## Setup

**Requirements:** [`just`](https://github.com/casey/just), `gawk`, and `python3`.

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
├── .claude/skills/           # Claude Code slash commands (/memento, …)
├── .memento/
│   ├── index.md              # overview / entry point
│   ├── skills/               # atomic skills, grouped by category
│   │   ├── categories.md
│   │   ├── agents/
│   │   ├── audio/
│   │   │   └── transcription/whisper_mlx/
│   │   │       ├── SKILL.md       # typed contract + procedure
│   │   │       └── resources/     # tool + validation scripts
│   │   ├── images/
│   │   ├── system/
│   │   ├── text/
│   │   └── video/
│   ├── scripts/              # graph build + chain-finder
│   ├── graph/                # generated skill graph
│   ├── resources/            # skill guide + shared helpers
│   └── logs/                 # per-run execution logs
├── docs/                     # presentation
├── tests/
├── justfile                  # init / build / test / install
└── LICENSE
```

## Details

For how it all works, see the presentation: **[`docs/memento_presentation.html`](docs/memento_presentation.html)**.

## License

[MIT](LICENSE) © 2026 Florian Buetow.
