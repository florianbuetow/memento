#!/usr/bin/env bash
# Resolve MEMENTO_ENV -- the path to the memento directory every other
# script, skill and tool reads from.
#
# Resolution order:
#   1. An already-set MEMENTO_ENV wins, so a caller can point the whole
#      toolchain at any library (useful for tests and for a second
#      checkout).
#   2. A project-local `.memento/` in the current working directory. A
#      repository that carries its own skills always shadows the personal
#      library.
#   3. `$HOME/.memento` -- the library installed by `just install`. This
#      is what makes the skills work from any directory.
#
# Use it either way:
#   source .../memento_env.sh     # defines and exports MEMENTO_ENV
#   MEMENTO_ENV=$(.../memento_env.sh)   # prints the resolved path
#
# The value is a directory path, so every consumer composes it the same
# way: "$MEMENTO_ENV/skills", "$MEMENTO_ENV/graph", "$MEMENTO_ENV/logs".

memento_env_resolve() {
    if [[ -n "${MEMENTO_ENV:-}" ]]; then
        printf '%s\n' "$MEMENTO_ENV"
    elif [[ -d ".memento" ]]; then
        printf '%s\n' "./.memento"
    else
        printf '%s\n' "$HOME/.memento"
    fi
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    memento_env_resolve
else
    MEMENTO_ENV="$(memento_env_resolve)"
    export MEMENTO_ENV
fi
