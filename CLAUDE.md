# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
just            # help — every target, grouped
just init       # verify awk/python3, chmod +x the .memento scripts
just build      # regenerate .memento/graph/ from all SKILL.md files
just test       # build, then run all four test scripts (fail-fast)
just sync-plugin # copy the machinery into plugins/memento/memento/
just env        # print the resolved MEMENTO_ENV and why
just install    # install machinery to ~/.memento (interactive y/N prompt)
```

Run one test directly — each is a standalone script with no framework:

```bash
python3 tests/test_skill_graph.py       # graph builder, fixtures + real library
python3 tests/test_find_connection.py   # chain finder, fixtures + real graph
python3 tests/test_memento_env.py       # MEMENTO_ENV resolution (fake HOME)
python3 tests/test_plugin_payload.py    # plugin payload rules (needs `just` on PATH)
```

Tests build into temp dirs and never touch `.memento/graph/` or the real `~/.memento`. They print one line per assertion and exit 1 on any failure.

## Architecture

**Data flow.** `SKILL.md` frontmatter → `build_skill_graph.sh` (awk parses `name`/`category`/`subcategory`/`inputs`/`outputs`) → `graph/skills_nodes.txt` + `graph/skills_edges.txt` → `compute_edge_weights.py` reweights edges from run-log durations → `find_connection.sh` runs bidirectional Dijkstra over those two files.

**Edges are type matches.** An edge `A → B` exists when any output TYPE of A equals any input TYPE of B. Matching is by exact name — `FILE` is not a supertype of `AUDIO_FILE`. `~` marks an optional parameter and is stripped before matching; `[A | B]` is a union, normalized to `A|B`, matching when any alternative on either side is equal; `LIST_X` is a manifest file (one entry per line) that only connects to `LIST_X`, bridged to single-item skills by a `system/iteration/fan_in_*` skill.

**`find_connection.sh` exit codes are the API:** `0` chain found (`CHAIN:`/`STEP:` lines), `2` no chain (`MISSING SKILL:`/`GAP CHAIN:` naming the types a new skill must have), `1` error. Callers switch on them.

### MEMENTO_ENV

Every script and skill resolves the library root in this order: an already-set `MEMENTO_ENV`, else a project-local `./.memento/`, else `$HOME/.memento`. `.memento/scripts/memento_env.sh` and `memento_env.py` are the single source of truth — nothing else may hardcode a library path, and `test_memento_env.py` enforces that the dependent tools follow the resolved library rather than their own location.

### Two copies of the machinery

`.memento/` is the source of truth. `plugins/memento/memento/` is the plugin payload, and `test_plugin_payload.py` asserts `scripts/` and `resources/` are **byte-identical** between them. **After editing anything under `.memento/scripts/` or `.memento/resources/`, run `just sync-plugin`** or `just test` fails.

`sync-plugin` copies from an explicit allowlist (`index.md`, `scripts/`, `resources/`, `skills/categories.md`), never an exclude list.

### Atomic skills are never shipped, never committed

`.memento/skills/<category>/` holds the user's own atomic skills: personal, deliberately untracked, and not the plugin's to distribute. Only `skills/categories.md` is tracked. A fresh install starts with an empty library. This is the rule the payload tests exist to defend — do not add atomic skills to the repo or the payload.

`.memento/graph/` and `.memento/logs/` are generated and gitignored.

### The script boundary

Two rules the codebase treats as load-bearing:

1. **A `SKILL.md` is a skill's complete interface.** Files under a skill's `resources/` and under `$MEMENTO_ENV/scripts/` are invoked, never opened — not to check arguments, not to explain a chain. The `/memento` skill spells out the single debugging exception. Editing a skill is a different task from executing one.
2. **Every entry point a `SKILL.md` invokes is a shell script.** Other languages are workers launched from inside it (`find_connection.sh` → `find_connection.py`). A `SKILL.md` that invokes a `.py` directly is malformed. Invoking Python directly also trips permission allowlists in practice.

### Writing a SKILL.md

`.memento/resources/skill_guide.md` is the canonical contract; `.memento/resources/example_skill/` is a worked example. In short: `snake_case` everywhere, required frontmatter (`name`, `category`, `subcategory`, `summary`, typed `inputs`/`outputs`, both validation scripts), sections Purpose / Inputs / Outputs / Procedure / Validation in that order, mandatory `validate_input.sh` and `validate_output.sh`, helpers referenced skill-relative (`resources/<name>.sh`) so the skill works from either library, and `set -euo pipefail` with absolute-path-safe, deterministic behaviour.

Procedure step 2 (the main tool call only, never the validators) is wrapped in `"$MEMENTO_ENV/resources/run_logged.sh" <category>/<subcategory>/<name> <cmd> <args...>`, which is transparent and appends a line to `logs/skill_runs-<YYYY-MM>.log`. Arguments are positional and complete: an omitted optional input is passed as `""`, never dropped.

A new TYPE must be added to the guide's TYPE list — that list is the vocabulary `/memento` and `/memento-add-skill` work from.

## Plugin constraints enforced by tests

A plugin runs from the plugin cache, where this repository does not exist. `test_plugin_payload.py` fails a `plugins/memento/skills/*/SKILL.md` that:

- names a repository-only path (`.memento/scripts`, `tests/`, `docs/`, …),
- uses the words *repository*, *checkout*, `git `, or `just ` on a line that does not also mention `CLAUDE_PLUGIN_ROOT`,
- and it fails **any** tracked file containing an absolute home-directory path.

Version bumps are part of a user-visible change: `plugins/memento/.claude-plugin/plugin.json` is what marketplace updates re-fetch, `.claude-plugin/marketplace.json` carries its own `version` for the plugin entry, and CHANGELOG.md follows Keep a Changelog.

## justfile conventions

The header comment in `justfile` is the spec: `printf` (not `echo`) for colors, a blank `@echo ""` around every command block, every target listed in `help` in group order (setup → run → codegen → checks fastest-first), composite targets fail fast, and every target ends in a green `✓` success or a red `✗` failure followed by `exit 1`.
