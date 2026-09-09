# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added a Claude Code plugin bundling the memento skills and its marketplace entry.
- Added a skill authoring guide and a categories entry to the memento resources.
- Added `MEMENTO_ENV` resolution: a project-local `.memento/` is preferred, otherwise `~/.memento`, with an environment variable override. Implemented once in `memento_env.sh` and `memento_env.py`.
- Added a `just env` target that prints the resolved library path and why it was chosen.
- Added a `/memento-install` skill that installs the memento machinery to `~/.memento` from the copy bundled with the plugin, so no clone, network or repository is needed. Re-running it replaces the machinery while leaving the user's skills and run logs alone.
- Added a justfile and a machinery payload inside `plugins/memento/`, making the plugin self-contained in the plugin cache where the repository is absent. Atomic skills are personal and are never bundled, so an installed library starts empty.
- Added a `just sync-plugin` target that copies the machinery into the plugin from an explicit allowlist, and `tests/test_plugin_payload.py`, which fails if any atomic skill or untracked file reaches the plugin or if the shipped machinery drifts from `.memento/`.
- Added `scripts/find_connection.sh`, the entry point for chain finding. It launches `find_connection.py`, passing every argument through and preserving its exit code, so a Python script is never invoked directly.

### Changed

- Changed every script and skill to read the library through `MEMENTO_ENV` instead of a hardcoded `.memento/` path, so the skills work from any directory once `just install` has run.
- Changed the memento skills to invoke the graph builder directly rather than `just build`, which only exists inside this repository.
- Changed the plugin skills to reference only `$MEMENTO_ENV`, so an installed plugin no longer hunts the filesystem for a repository checkout.
- Changed `/memento` to point users at `/memento-install` when no library resolves.
- Bumped the memento plugin to 1.1.0 so marketplace updates re-fetch the new skills.
- Changed `/memento` to call `scripts/find_connection.sh` instead of `find_connection.py`. Invoking the Python script directly was routinely denied by permission allowlists, which broke chain finding.
- Added a "Script invocation" rule to the skill authoring guide: every entry point a SKILL.md invokes must be a shell script, with other languages launched as workers from inside it.
- Bumped the memento plugin to 1.2.0 so marketplace updates re-fetch the shell entry point.
- Changed `/memento` to state the script boundary explicitly: a skill's `SKILL.md` is its complete interface, and everything under a skill's `resources/` or under `$MEMENTO_ENV/scripts/` is invoked, never opened. Agents were routinely inspecting helper implementations while planning and executing chains, which is exactly the coupling the library exists to remove. The rule names where each fact comes from instead, and allows a single debugging exception.
- Changed `/memento` to carry the two library-wide execution conventions that individual SKILL.md files do not all restate — every argument the Procedure lists is passed positionally with `""` for an omitted optional, and `run_logged.sh` wraps only the main tool call — so executing a chain no longer requires opening the authoring guide.
- Changed the library index's "How to use a skill" section to carry the same boundary and to name `$MEMENTO_ENV/resources/run_logged.sh` explicitly. It previously told the reader to invoke the helper scripts under a skill's `resources/` directory, handing over the directory with no restriction.
- Changed `/memento` to take TYPE values from the graph node file rather than from the authoring guide, removing the last reason for an executing agent to open `skill_guide.md`.
- Bumped the memento plugin to 1.3.0 so marketplace updates re-fetch the boundary rule.

### Fixed

- Fixed `just install`, which ran `rm -rf ~/.memento` before copying and would therefore have destroyed a user's entire skill library and run logs. The repository ships no atomic skills, so a single install wiped everything the user had added, despite the documentation promising the opposite. It now replaces only the machinery — `scripts/`, `resources/` and `index.md` — reports the skill count it left alone, and never removes the library as a whole, matching the installer the plugin already used.
- Fixed a test suite that could not pass. Both `test_memento_env.py` and `test_find_connection.py` asserted against atomic skills that stopped being committed when skills became personal, so the chain finder was asked to search an empty graph. The environment test now plants its own fixture skills, and the real-library test is phrased against whatever the committed graph holds instead of naming particular skills.
- Fixed the authoring guide's TYPE list, which omitted `PDF_FILE` even though two skills already declare it. The list is what `/memento` and `/memento-add-skill` treat as the vocabulary, so a type in active use was undocumented.
- Bumped the memento plugin to 1.3.1 so marketplace updates re-fetch the corrected TYPE list.

## 2026-07-21

### Added

- Added a skills system that chains atomic skills into goal-completing sequences.
- Added Dijkstra path-finding to locate the shortest chain between skills.
- Added commands to add, update, remove, and rebuild skills.
- Added an interactive HTML presentation that visualizes the skill graph.
- Added an example skill with input and output validation helper scripts.

## 2026-05-26

### Added

- Added the initial project scaffolding under the MIT License.
