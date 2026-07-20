#!/usr/bin/env bash
# validate_output.sh
# Verifies that OUTPUT_PATH exists, is non-empty, and is an MP3 file as
# reported by ffprobe.
#
# Usage: validate_output.sh <output_path>
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <output_path>" >&2
  exit 2
fi

OUTPUT_PATH="$1"

if [[ ! -s "$OUTPUT_PATH" ]]; then
  echo "output missing or empty: $OUTPUT_PATH" >&2
  exit 1
fi

CODEC=$(ffprobe -hide_banner -loglevel error \
  -select_streams a:0 -show_entries stream=codec_name \
  -of csv=p=0 "$OUTPUT_PATH" || true)

if [[ "$CODEC" != "mp3" ]]; then
  echo "expected mp3 codec, got: ${CODEC:-<none>}" >&2
  exit 1
fi
