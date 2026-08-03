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

### Changed

- Changed every script and skill to read the library through `MEMENTO_ENV` instead of a hardcoded `.memento/` path, so the skills work from any directory once `just install` has run.
- Changed the memento skills to invoke the graph builder directly rather than `just build`, which only exists inside this repository.
- Changed the plugin skills to reference only `$MEMENTO_ENV`, so an installed plugin no longer hunts the filesystem for a repository checkout.
- Changed `/memento` to point users at `/memento-install` when no library resolves.
- Bumped the memento plugin to 1.1.0 so marketplace updates re-fetch the new skills.

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
