---
name: memento
description: Map a goal to a chain of atomic memento skills using the skill graph (Dijkstra), or flag exactly which atomic skill is missing when no chain exists. Use when the user states a goal to accomplish with memento skills (e.g. "download video [url] and extract the transcript"), asks how to get from A to B with skills, or asks which skill is missing.
---

# Find a skill chain (or the missing link)

Resolve the user's goal to typed endpoints, then let `.memento/scripts/find_connection.py` search the skill graph — Dijkstra forward from the start and backward from the goal simultaneously. Either a shortest chain exists, or the finder reports the closest connection between the two frontiers and flags the missing atomic skill explicitly.

## Procedure

1. Freshen the graph: `just build` (idempotent and cheap; a stale graph gives wrong answers).
2. Read `.memento/graph/skills_nodes.txt` and map the goal to two endpoints:
   - FROM — what is available: a specific skill (`skill:<category/subcategory/name>`) or the TYPE held (`type:TEXT` for a URL or prompt, `type:VIDEO_FILE` for a video on disk, …).
   - TO — what is wanted: a specific skill, or the TYPE of the desired artifact (`type:TEXT_FILE_TXT` for a transcript or plain text, `type:TEXT_FILE_SRT` for subtitles, …).
   - Types are the TYPE values from `.memento/resources/skill_guide.md`. Example: "download video [url] and extract the transcript" → `--from skill:video/download/from_youtube --to type:TEXT_FILE_TXT`.
3. Run: `python3 .memento/scripts/find_connection.py --from <endpoint> --to <endpoint>`. If running it with the `python3` (or `bash`) prefix is prohibited by the permission allowlist, run the script directly by path instead — `.memento/scripts/find_connection.py --from <endpoint> --to <endpoint>` — since it is a shebang script.
4. Exit 0 — a chain exists. Present the `CHAIN:` in order with each `STEP:`'s linking type, and point each skill at its `.memento/skills/<id>/SKILL.md` for execution.
5. Exit 2 — no chain. Quote the `MISSING SKILL:` line(s) verbatim — that is the explicit flag naming the input/output types the missing atomic skill must have — and show `GAP CHAIN:`, which marks where it slots in. Offer to create it with /memento-add-skill; the new skill's frontmatter types must match the flagged signature or the chain will not close.
6. Exit 1 — error (unknown skill id, out-of-sync graph files). Fix per the message (usually `just build`) and retry once.
