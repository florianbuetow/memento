#!/usr/bin/env bash
# Find a chain of skills between two endpoints, or the missing link.
#
# This is the entry point: agents call THIS script, never find_connection.py
# directly. A Python script is a worker, launched from inside a shell script --
# it is not something a SKILL.md or an agent invokes on its own.
#
# Every argument is passed through to find_connection.py untouched, and its
# exit code is preserved via `exec`, because callers switch on it:
#
#   0  a chain exists          (CHAIN: ... / STEP: ...)
#   1  error                   (unknown skill id, out-of-sync graph files)
#   2  no chain                (MISSING SKILL: ... / GAP CHAIN: ...)
#
# Usage: find_connection.sh --from ENDPOINT --to ENDPOINT [...]
#   ENDPOINT is `skill:<category/subcategory/name>` or `type:<TYPE>`.
#   Run with --help for the full argument list.
#
# MEMENTO_ENV is resolved by memento_env.sh: a project-local `.memento/`
# when the current directory has one, otherwise `$HOME/.memento`.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=memento_env.sh
source "$SCRIPT_DIR/memento_env.sh"

FINDER="$SCRIPT_DIR/find_connection.py"

if [[ ! -f "$FINDER" ]]; then
    echo "find_connection.sh: finder not found: $FINDER" >&2
    exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || true)}"
if [[ -z "$PYTHON_BIN" || ! -x "$PYTHON_BIN" ]]; then
    echo "find_connection.sh: python3 not found" >&2
    exit 1
fi

exec "$PYTHON_BIN" "$FINDER" "$@"
