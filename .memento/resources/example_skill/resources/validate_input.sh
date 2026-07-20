#!/usr/bin/env bash
# validate_input.sh
# Verifies that INPUT_PATH exists, is readable, and contains an audio stream.
# Exits 0 on success, non-zero with a stderr message on failure.
#
# Usage: validate_input.sh <input_path>
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <input_path>" >&2
  exit 2
fi

INPUT_PATH="$1"

if [[ ! -f "$INPUT_PATH" ]]; then
  echo "input not found: $INPUT_PATH" >&2
  exit 1
fi

if [[ ! -r "$INPUT_PATH" ]]; then
  echo "input not readable: $INPUT_PATH" >&2
  exit 1
fi

if ! ffprobe -hide_banner -loglevel error \
      -select_streams a -show_entries stream=codec_type \
      -of csv=p=0 "$INPUT_PATH" | grep -q '^audio$'; then
  echo "no audio stream in: $INPUT_PATH" >&2
  exit 1
fi
