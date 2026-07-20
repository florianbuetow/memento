#!/usr/bin/env bash
# run_logged.sh SKILL_ID COMMAND [ARGS...]
# Run a skill's main tool and append its wall-clock duration to the
# append-only run log, so skill effectiveness/speed can be tracked.
#
# Log location: .memento/logs/skill_runs-<YYYY-MM>.log — one file per
# calendar month, which is the rotation scheme: a new month simply starts
# a new file, old files are never rewritten or truncated.
#
# Log line format (tab-separated):
#   <ISO8601 timestamp>  <skill id>  <duration ms>  exit=<code>
#
# The wrapped command's stdout/stderr pass through untouched and its exit
# code is propagated, so wrapping does not change skill behaviour.
set -uo pipefail  # deliberately no -e: a failing tool must still be logged

SKILL_ID="${1:-}"
if [[ -z "$SKILL_ID" || $# -lt 2 ]]; then
  echo "usage: run_logged.sh SKILL_ID COMMAND [ARGS...]" >&2
  echo "  SKILL_ID: category/subcategory/name, e.g. audio/tts/kokoro" >&2
  exit 2
fi
shift

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
LOG_DIR="${script_dir}/../logs"
mkdir -p "$LOG_DIR"
LOG_FILE="${LOG_DIR}/skill_runs-$(date +%Y-%m).log"

now_ms() {
  # macOS date(1) has no %N; python3 gives portable millisecond precision.
  python3 -c 'import time; print(int(time.time() * 1000))'
}

start_ms=$(now_ms)
"$@"
status=$?
end_ms=$(now_ms)

printf '%s\t%s\t%dms\texit=%d\n' \
  "$(date +%Y-%m-%dT%H:%M:%S%z)" \
  "$SKILL_ID" \
  "$((end_ms - start_ms))" \
  "$status" >> "$LOG_FILE"

exit "$status"
