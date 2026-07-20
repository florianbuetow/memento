---
name: to_mp3
category: audio
subcategory: conversion
summary: Convert an audio or video file to MP3 (CBR 192 kbit/s, 44.1 kHz, stereo) using ffmpeg.
inputs:
  - INPUT_PATH::FILE
  - ~OUTPUT_PATH::FILE
outputs:
  - OUTPUT_PATH::FILE
input_validation_script: resources/validate_input.sh
output_validation_script: resources/validate_output.sh
---

# Convert to MP3

## Purpose

Convert an arbitrary media file containing an audio stream into a standalone
MP3 file with fixed, predictable encoding parameters. Use this skill to
normalize heterogeneous input assets into a consistent MP3 form before further
processing or distribution.

## Inputs

- `INPUT_PATH` — absolute path (string). Must exist, must be readable, must
  contain at least one audio stream.
- `OUTPUT_PATH` — absolute path (string) ending in `.mp3`. The parent directory
  must exist. An existing file at this path will be overwritten.

## Outputs

- A file at `OUTPUT_PATH`: MPEG-1 Audio Layer III, CBR 192 kbit/s, 44.1 kHz,
  2 channels.

## Procedure

1. Run `resources/validate_input.sh "$INPUT_PATH"`. Abort on non-zero exit.
2. Run `resources/ffmpeg_helper.sh "$INPUT_PATH" "$OUTPUT_PATH"`. Abort on
   non-zero exit.
3. Run `resources/validate_output.sh "$OUTPUT_PATH"`. Abort on non-zero exit.

## Validation

- `resources/validate_input.sh` — verifies the input exists, is readable, and
  contains an audio stream.
- `resources/validate_output.sh` — verifies the output exists, is non-empty,
  and reports `mp3` as the codec of its first audio stream.
