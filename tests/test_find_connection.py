#!/usr/bin/env python3
"""Assertion tests for the skill-chain connection finder.

Usage:
    tests/test_find_connection.py

Runs .memento/scripts/find_connection.py against synthetic graph fixtures
with exactly known expected output, then against the committed real graph
under .memento/graph/ to check semantic invariants. Nothing under
.memento/ is modified — fixtures live in a temporary directory.

Exits 0 if every assertion holds, 1 otherwise, printing one line per test.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FINDER = REPO_ROOT / ".memento" / "scripts" / "find_connection.py"
REAL_NODES = REPO_ROOT / ".memento" / "graph" / "skills_nodes.txt"
REAL_EDGES = REPO_ROOT / ".memento" / "graph" / "skills_edges.txt"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
RESET = "\033[0m"

_results: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    _results.append((name, "" if condition else detail or "assertion failed"))


def run_finder(
    nodes: Path, edges: Path, src: str, dst: str, *extra: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(FINDER),
            "--nodes",
            str(nodes),
            "--edges",
            str(edges),
            "--from",
            src,
            "--to",
            dst,
            *extra,
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def write_graph(tmp: Path, name: str, node_lines: list[str], edge_lines: list[str]) -> tuple[Path, Path]:
    graph_dir = tmp / name
    graph_dir.mkdir(parents=True, exist_ok=True)
    nodes = graph_dir / "skills_nodes.txt"
    edges = graph_dir / "skills_edges.txt"
    nodes.write_text("".join(line + "\n" for line in node_lines), encoding="utf-8")
    edges.write_text("".join(line + "\n" for line in edge_lines), encoding="utf-8")
    return nodes, edges


def parse_real_nodes() -> dict[str, tuple[list[str], list[str]]]:
    nodes: dict[str, tuple[list[str], list[str]]] = {}
    for line in REAL_NODES.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        node_id, raw_inputs, raw_outputs = line.split("\t")
        parse = lambda raw: [] if raw == "-" else [t.lstrip("~") for t in raw.split(",")]
        nodes[node_id] = (
            parse(raw_inputs.removeprefix("inputs=")),
            parse(raw_outputs.removeprefix("outputs=")),
        )
    return nodes


# --------------------------------------------------------------------------
# Fixture tests — synthetic graphs with exactly known expected output
# --------------------------------------------------------------------------

LINEAR_NODES = [
    "a/a/start\tinputs=TEXT\toutputs=AUDIO_FILE",
    "a/a/mid\tinputs=AUDIO_FILE\toutputs=TEXT_FILE_TXT",
    "a/a/end\tinputs=TEXT_FILE_TXT\toutputs=NUMBER",
    "b/b/island\tinputs=IMAGE_FILE\toutputs=-",
    "b/b/sink\tinputs=NUMBER\toutputs=-",
    "c/c/noin\tinputs=-\toutputs=TEXT",
]
LINEAR_EDGES = [
    "a/a/start a/a/mid 1",
    "a/a/mid a/a/end 1",
    "a/a/end b/b/sink 1",
    "c/c/noin a/a/start 1",
]


def test_chains(tmp: Path) -> None:
    nodes, edges = write_graph(tmp, "linear", LINEAR_NODES, LINEAR_EDGES)

    result = run_finder(nodes, edges, "a/a/start", "a/a/end")
    check("fixture: skill-to-skill chain exits 0", result.returncode == 0, result.stderr.strip())
    check(
        "fixture: shortest chain is printed in order",
        "CHAIN: a/a/start -> a/a/mid -> a/a/end" in result.stdout,
        result.stdout,
    )
    check(
        "fixture: steps carry the linking type",
        "STEP: a/a/start -[AUDIO_FILE]-> a/a/mid" in result.stdout,
        result.stdout,
    )

    result = run_finder(nodes, edges, "type:TEXT", "type:NUMBER")
    check("fixture: type-to-type endpoints exit 0", result.returncode == 0, result.stderr.strip())
    check(
        "fixture: type endpoints resolve to the same chain",
        "CHAIN: a/a/start -> a/a/mid -> a/a/end" in result.stdout,
        result.stdout,
    )

    result = run_finder(nodes, edges, "TEXT", "NUMBER")
    check("fixture: bare uppercase endpoints auto-detect as types", result.returncode == 0)

    result = run_finder(nodes, edges, "a/a/start", "a/a/start")
    check("fixture: identical endpoints yield the single-skill chain", result.returncode == 0)
    check(
        "fixture: single-skill chain has no arrow and no steps",
        "CHAIN: a/a/start" in result.stdout.splitlines() and "STEP:" not in result.stdout,
        result.stdout,
    )


def test_gaps(tmp: Path) -> None:
    nodes, edges = write_graph(tmp, "gaps", LINEAR_NODES, LINEAR_EDGES)

    result = run_finder(nodes, edges, "a/a/start", "b/b/island")
    check("fixture: unreachable goal exits 2", result.returncode == 2, str(result.returncode))
    check("fixture: NO CHAIN is reported", "NO CHAIN:" in result.stdout, result.stdout)
    check(
        "fixture: forward frontier is listed with distances",
        "FORWARD REACHABLE: a/a/start (0), a/a/mid (1), a/a/end (2), b/b/sink (3)" in result.stdout,
        result.stdout,
    )
    check(
        "fixture: backward frontier is listed with distances",
        "BACKWARD REACHABLE: b/b/island (0)" in result.stdout,
        result.stdout,
    )
    check(
        "fixture: closest connection picks the cheapest anchor pair",
        "CLOSEST CONNECTION: a/a/start ~~> b/b/island (existing steps: 0 from start, 0 to goal)"
        in result.stdout,
        result.stdout,
    )
    check(
        "fixture: missing skill is flagged with required types",
        "MISSING SKILL: input one of {AUDIO_FILE}; output one of {IMAGE_FILE}" in result.stdout,
        result.stdout,
    )
    check(
        "fixture: gap chain inlines the missing skill",
        "GAP CHAIN: a/a/start -> [MISSING SKILL] -> b/b/island" in result.stdout,
        result.stdout,
    )

    rerun = run_finder(nodes, edges, "a/a/start", "b/b/island")
    check("fixture: gap report is deterministic", rerun.stdout == result.stdout)

    result = run_finder(nodes, edges, "a/a/start", "type:IMAGE_FILE")
    check("fixture: unproduced goal type exits 2", result.returncode == 2)
    check(
        "fixture: unproduced goal type is shown with no producers",
        "TO: type IMAGE_FILE (producers: none)" in result.stdout,
        result.stdout,
    )
    check(
        "fixture: goal type anchors the missing skill directly",
        "MISSING SKILL: input one of {AUDIO_FILE}; output one of {IMAGE_FILE}" in result.stdout
        and "GAP CHAIN: a/a/start -> [MISSING SKILL] -> (goal type IMAGE_FILE)" in result.stdout,
        result.stdout,
    )

    result = run_finder(nodes, edges, "type:VIDEO_FILE", "a/a/end")
    check("fixture: unconsumed start type exits 2", result.returncode == 2)
    check(
        "fixture: start type anchors the missing skill directly",
        "MISSING SKILL: input one of {VIDEO_FILE}; output one of {TEXT_FILE_TXT}" in result.stdout,
        result.stdout,
    )

    result = run_finder(nodes, edges, "b/b/sink", "a/a/end")
    check("fixture: start skill without outputs exits 2", result.returncode == 2)
    check(
        "fixture: outputless forward region is flagged unbridgeable",
        "UNBRIDGEABLE:" in result.stdout and "MISSING SKILL:" not in result.stdout,
        result.stdout,
    )

    result = run_finder(nodes, edges, "a/a/start", "c/c/noin")
    check("fixture: goal skill without inputs exits 2", result.returncode == 2)
    check(
        "fixture: inputless backward region is flagged unbridgeable",
        "UNBRIDGEABLE:" in result.stdout,
        result.stdout,
    )


def test_weights_and_unions(tmp: Path) -> None:
    nodes, edges = write_graph(
        tmp,
        "weighted",
        [
            "w/w/p\tinputs=TEXT\toutputs=NUMBER",
            "w/w/q\tinputs=NUMBER\toutputs=NUMBER",
            "w/w/r\tinputs=NUMBER\toutputs=NUMBER",
            "w/w/s\tinputs=NUMBER\toutputs=FOLDER",
        ],
        ["w/w/p w/w/q 1", "w/w/q w/w/r 1", "w/w/r w/w/s 1", "w/w/p w/w/s 5"],
    )
    result = run_finder(nodes, edges, "w/w/p", "w/w/s")
    check(
        "fixture: edge weights steer the shortest chain",
        "CHAIN: w/w/p -> w/w/q -> w/w/r -> w/w/s" in result.stdout,
        result.stdout,
    )

    nodes, edges = write_graph(
        tmp,
        "union",
        [
            "u/u/producer\tinputs=TEXT\toutputs=AUDIO_FILE",
            "u/u/consumer\tinputs=AUDIO_FILE|VIDEO_FILE\toutputs=-",
        ],
        ["u/u/producer u/u/consumer 1"],
    )
    result = run_finder(nodes, edges, "type:VIDEO_FILE", "u/u/consumer")
    check(
        "fixture: union input matches a type endpoint alternative",
        result.returncode == 0 and "CHAIN: u/u/consumer" in result.stdout.splitlines(),
        result.stdout,
    )


def test_errors(tmp: Path) -> None:
    nodes, edges = write_graph(tmp, "errors", LINEAR_NODES, LINEAR_EDGES)

    result = run_finder(nodes, edges, "a/a/nope", "a/a/end")
    check("fixture: unknown skill id exits 1", result.returncode == 1, str(result.returncode))
    check("fixture: unknown skill id names the culprit", "a/a/nope" in result.stderr, result.stderr)

    stale = write_graph(tmp, "stale", LINEAR_NODES[:1], ["a/a/start a/a/gone 1"])
    result = run_finder(*stale, "a/a/start", "a/a/start")
    check("fixture: edge to unknown node exits 1", result.returncode == 1)
    check(
        "fixture: out-of-sync graph advises a rebuild",
        "just build" in result.stderr,
        result.stderr,
    )


# --------------------------------------------------------------------------
# Real-library tests — semantic invariants over the committed graph
# --------------------------------------------------------------------------


def test_real_library() -> None:
    source = "video/download/from_youtube"

    result = run_finder(REAL_NODES, REAL_EDGES, f"skill:{source}", "type:TEXT_FILE_TXT")
    check("real: video download to transcript text exits 0", result.returncode == 0, result.stderr.strip())
    check(
        "real: transcript chain goes through whisper_mlx",
        "audio/transcription/whisper_mlx" in result.stdout,
        result.stdout,
    )

    nodes = parse_real_nodes()
    image_producers = [
        n for n, (_, outs) in nodes.items()
        if any("IMAGE_FILE" in t.split("|") for t in outs)
    ]
    result = run_finder(REAL_NODES, REAL_EDGES, source, "images/viewing/phoenix_slides")
    if image_producers:
        check(
            "real: image viewing is reachable via an IMAGE_FILE producer",
            result.returncode == 0,
            result.stdout,
        )
    else:
        check("real: image viewing is unreachable today", result.returncode == 2, result.stdout)
        check(
            "real: the missing image-producing skill is flagged",
            "MISSING SKILL:" in result.stdout and "IMAGE_FILE" in result.stdout,
            result.stdout,
        )

    for target in sorted(nodes):
        result = run_finder(REAL_NODES, REAL_EDGES, source, target)
        ok = result.returncode in (0, 2) and (
            "CHAIN:" in result.stdout or "NO CHAIN:" in result.stdout
        )
        if not ok:
            check(f"real: sweep to {target} yields a verdict", False, result.stdout + result.stderr)
            return
    check("real: every target yields a chain or an explicit gap", True)


def main() -> None:
    if not FINDER.exists():
        print(f"error: finder not found at {FINDER}", file=sys.stderr)
        sys.exit(1)
    if not REAL_NODES.exists() or not REAL_EDGES.exists():
        print("error: committed graph missing — run `just build` first", file=sys.stderr)
        sys.exit(1)

    tmp = Path(tempfile.mkdtemp(prefix="findconnection-test-"))
    try:
        test_chains(tmp)
        test_gaps(tmp)
        test_weights_and_unions(tmp)
        test_errors(tmp)
        test_real_library()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    failures = [(name, detail) for name, detail in _results if detail]
    for name, detail in _results:
        if detail:
            print(f"  {RED}✗ {name}{RESET}\n      {detail}")
        else:
            print(f"  {GREEN}✓ {name}{RESET}")

    print("")
    if failures:
        print(f"{RED}{len(failures)} of {len(_results)} tests failed{RESET}")
        sys.exit(1)
    print(f"{GREEN}all {len(_results)} tests passed{RESET}")


if __name__ == "__main__":
    main()
