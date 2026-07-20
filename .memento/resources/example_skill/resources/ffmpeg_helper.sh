#!/usr/bin/env bash
# ffmpeg_helper.sh
# Deterministic wrapper around ffmpeg to encode INPUT_PATH into OUTPUT_PATH
# as CBR 192 kbit/s, 44.1 kHz, stereo MP3.
#
# Usage: ffmpeg_helper.sh <input_path> <output_path>
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <input_path> <output_path>" >&2
  exit 2
fi

INPUT_PATH="$1"
OUTPUT_PATH="$2"

ffmpeg -hide_banner -loglevel error -y \
  -i "$INPUT_PATH" \
  -vn \
  -c:a libmp3lame \
  -b:a 192k \
  -ar 44100 \
  -ac 2 \
  "$OUTPUT_PATH"
