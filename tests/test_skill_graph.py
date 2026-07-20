#!/usr/bin/env python3
"""Assertion tests for the skill graph generator.

Usage:
    tests/test_skill_graph.py

Runs .memento/scripts/build_skill_graph.sh against synthetic fixture skill
trees with known expected output, then against the real .memento/skills
library to check structural invariants. Nothing under .memento/graph/ is
modified — every generated graph goes to a temporary directory.

Exits 0 if every assertion holds, 1 otherwise, printing one line per test.
"""

import math
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILDER = REPO_ROOT / ".memento" / "scripts" / "build_skill_graph.sh"
WEIGHTER = REPO_ROOT / ".memento" / "scripts" / "compute_edge_weights.py"
REAL_SKILLS = REPO_ROOT / ".memento" / "skills"
REAL_GRAPH = REPO_ROOT / ".memento" / "graph"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
RESET = "\033[0m"

_results: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    _results.append((name, "" if condition else detail or "assertion failed"))


def run_builder(skills_dir: Path, out_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(BUILDER), str(skills_dir), str(out_dir)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def run_reweight(edges: Path, logs_dir: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(WEIGHTER), "--edges", str(edges), "--logs-dir", str(logs_dir), *extra],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def write_skill(
    skills_dir: Path,
    category: str,
    subcategory: str,
    name: str,
    inputs: list[str],
    outputs: list[str],
) -> None:
    """Create a minimal fixture SKILL.md with the given typed frontmatter."""
    skill_dir = skills_dir / category / subcategory / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    lines = ["---", f"name: {name}", f"category: {category}", f"subcategory: {subcategory}"]
    lines.append("inputs:")
    lines.extend(f"  - {entry}" for entry in inputs)
    lines.append("outputs:")
    lines.extend(f"  - {entry}" for entry in outputs)
    lines += ["---", "", f"# {name}", ""]
    (skill_dir / "SKILL.md").write_text("\n".join(lines), encoding="utf-8")


def write_logs(
    logs_dir: Path,
    rows: list[tuple[str, str, str]],
    extra: tuple[str, ...] = (),
) -> None:
    """Write fixture run-log lines for the current month into logs_dir.

    Each row is (skill_id, duration, exit_field) -- e.g.
    ("a/b/c", "2000ms", "exit=0"). The leading ISO-timestamp column is a
    placeholder because compute_edge_weights.py never reads it. `extra` lines
    are written verbatim to exercise malformed-line tolerance. The file is
    named for the current month so the default 3-month window always spans it.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    month = date.today().strftime("%Y-%m")
    stamp = f"{month}-01T00:00:00+0000"
    lines = [f"{stamp}\t{skill}\t{dur}\t{code}" for skill, dur, code in rows]
    lines.extend(extra)
    (logs_dir / f"skill_runs-{month}.log").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_nodes(path: Path) -> dict[str, tuple[list[str], list[str]]]:
    nodes: dict[str, tuple[list[str], list[str]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        node_id, raw_inputs, raw_outputs = line.split("\t")
        nodes[node_id] = (
            raw_inputs.removeprefix("inputs=").split(","),
            raw_outputs.removeprefix("outputs=").split(","),
        )
    return nodes


def parse_edges(path: Path) -> list[tuple[str, str, str]]:
    edges = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        source, target, weight = line.split()
        edges.append((source, target, weight))
    return edges


def types_match(a: str, b: str) -> bool:
    """A union type matches when the two share at least one alternative."""
    return bool(set(a.split("|")) & set(b.split("|")))


def expected_edges(nodes: dict[str, tuple[list[str], list[str]]]) -> set[tuple[str, str]]:
    """Independent reimplementation of the generator's edge rule."""
    edges = set()
    for source, (_, outputs) in nodes.items():
        for target, (inputs, _) in nodes.items():
            if source == target:
                continue
            for out_type in outputs:
                if out_type in ("-", "UNKNOWN"):
                    continue
                for in_type in inputs:
                    if in_type in ("-", "UNKNOWN"):
                        continue
                    if types_match(out_type.lstrip("~"), in_type.lstrip("~")):
                        edges.add((source, target))
    return edges


# --------------------------------------------------------------------------
# Fixture tests — synthetic skill trees with exactly known expected output
# --------------------------------------------------------------------------


def test_fixtures(tmp: Path) -> None:
    skills = tmp / "skills"
    out = tmp / "out"

    write_skill(skills, "alpha", "make", "producer", ["SRC::TEXT"], ["RESULT::AUDIO_FILE"])
    write_skill(skills, "alpha", "use", "consumer", ["IN::AUDIO_FILE"], ["OUT::TEXT_FILE_TXT"])
    write_skill(skills, "beta", "use", "unrelated", ["IN::FOLDER"], ["OUT::NUMBER"])
    write_skill(skills, "beta", "use", "optional_in", ["~IN::AUDIO_FILE"], [])
    write_skill(skills, "beta", "use", "union_in", ["IN::[AUDIO_FILE | VIDEO_FILE]"], [])
    write_skill(skills, "beta", "use", "generic_in", ["IN::FILE"], [])
    # Same skill name in a different category must stay a distinct node.
    write_skill(skills, "gamma", "make", "producer", ["SRC::TEXT"], ["RESULT::IMAGE_FILE"])
    # Output type equals its own input type — must not create a self-edge.
    write_skill(skills, "gamma", "loop", "selfish", ["IN::NUMBER"], ["OUT::NUMBER"])

    result = run_builder(skills, out)
    check("fixture: builder exits 0", result.returncode == 0, result.stderr.strip())

    nodes = parse_nodes(out / "skills_nodes.txt")
    edges = {(s, t) for s, t, _ in parse_edges(out / "skills_edges.txt")}
    weights = {w for _, _, w in parse_edges(out / "skills_edges.txt")}

    check("fixture: all 8 skills become nodes", len(nodes) == 8, f"got {len(nodes)}")
    check(
        "fixture: node id is category/subcategory/name",
        "alpha/make/producer" in nodes,
        f"ids: {sorted(nodes)}",
    )
    check(
        "fixture: same name in two categories stays distinct",
        "alpha/make/producer" in nodes and "gamma/make/producer" in nodes,
    )
    check(
        "fixture: matching type creates an edge",
        ("alpha/make/producer", "alpha/use/consumer") in edges,
    )
    check(
        "fixture: edge is directional, not reversed",
        ("alpha/use/consumer", "alpha/make/producer") not in edges,
    )
    check(
        "fixture: non-matching types create no edge",
        ("alpha/make/producer", "beta/use/unrelated") not in edges,
    )
    check(
        "fixture: optional ~ input is still satisfied",
        ("alpha/make/producer", "beta/use/optional_in") in edges,
    )
    check(
        "fixture: union input matches one alternative",
        ("alpha/make/producer", "beta/use/union_in") in edges,
    )
    check(
        "fixture: union type is normalized in the node line",
        nodes["beta/use/union_in"][0] == ["AUDIO_FILE|VIDEO_FILE"],
        f"got {nodes['beta/use/union_in'][0]}",
    )
    check(
        "fixture: FILE is not a supertype of AUDIO_FILE",
        ("alpha/make/producer", "beta/use/generic_in") not in edges,
    )
    check(
        "fixture: empty outputs render as '-'",
        nodes["beta/use/union_in"][1] == ["-"],
        f"got {nodes['beta/use/union_in'][1]}",
    )
    check(
        "fixture: optional marker is preserved in the node line",
        nodes["beta/use/optional_in"][0] == ["~AUDIO_FILE"],
        f"got {nodes['beta/use/optional_in'][0]}",
    )
    check(
        "fixture: no self-edge when output type equals own input type",
        ("gamma/loop/selfish", "gamma/loop/selfish") not in edges,
    )
    check("fixture: every edge has weight 1", weights <= {"1"}, f"got {weights}")


def test_one_edge_per_pair(tmp: Path) -> None:
    """Two matching type pairs between the same skills must emit one edge."""
    skills = tmp / "skills2"
    out = tmp / "out2"
    write_skill(skills, "x", "a", "multi_out", ["S::TEXT"], ["A::AUDIO_FILE", "B::IMAGE_FILE"])
    write_skill(skills, "x", "b", "multi_in", ["A::AUDIO_FILE", "B::IMAGE_FILE"], [])

    run_builder(skills, out)
    raw = parse_edges(out / "skills_edges.txt")
    check(
        "fixture: two matching types still emit exactly one edge",
        len(raw) == 1,
        f"got {len(raw)} edges: {raw}",
    )


def test_comment_and_blank_tolerance(tmp: Path) -> None:
    """A SKILL.md with no outputs key at all must still parse."""
    skills = tmp / "skills3"
    out = tmp / "out3"
    skill_dir = skills / "y" / "b" / "no_outputs"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: no_outputs\ncategory: y\nsubcategory: b\n"
        "inputs:\n  - IN::TEXT\noutputs:\n---\n\n# no outputs\n",
        encoding="utf-8",
    )

    result = run_builder(skills, out)
    nodes = parse_nodes(out / "skills_nodes.txt")
    check("fixture: skill with empty outputs key parses", result.returncode == 0)
    check(
        "fixture: empty outputs key yields '-'",
        nodes.get("y/b/no_outputs", ([], []))[1] == ["-"],
        f"got {nodes.get('y/b/no_outputs')}",
    )


def test_edge_weights_from_logs(tmp: Path) -> None:
    """Edge weights are reweighted from the run logs during a build.

    When log data exists, an edge A -> B must carry the weight

        max(1, ln(1 + avg_secs(A) + avg_secs(B)))

    where avg_secs(X) is the mean duration in seconds of X's successful
    (exit=0) runs. This pins the log-driven rule that build_skill_graph.sh
    applies via compute_edge_weights.py.
    """
    skills = tmp / "wskills"
    out = tmp / "wout"
    logs = tmp / "wlogs"

    # Five skills whose types chain into exactly three edges:
    #   producer -> consumer -> sink   and   lo_src -> lo_dst
    write_skill(skills, "alpha", "make", "producer", ["SRC::TEXT"], ["RESULT::AUDIO_FILE"])
    write_skill(skills, "alpha", "use", "consumer", ["IN::AUDIO_FILE"], ["OUT::IMAGE_FILE"])
    write_skill(skills, "alpha", "use", "sink", ["IN::IMAGE_FILE"], [])
    write_skill(skills, "beta", "lo", "lo_src", ["S::TEXT"], ["O::NUMBER"])
    write_skill(skills, "beta", "lo", "lo_dst", ["I::NUMBER"], [])

    build = run_builder(skills, out)
    check("weights: builder exits 0", build.returncode == 0, build.stderr.strip())

    # producer: mean of the two exit=0 'ms' runs = (2000+4000)/2 = 3000ms = 3.0s.
    # The exit=1 run and the unit-less "7000" run must be ignored; if either
    # leaked, the producer mean (and every weight below) would change.
    write_logs(
        logs,
        [
            ("alpha/make/producer", "2000ms", "exit=0"),
            ("alpha/make/producer", "4000ms", "exit=0"),
            ("alpha/make/producer", "999000ms", "exit=1"),  # failed run: ignored
            ("alpha/make/producer", "7000", "exit=0"),       # no 'ms' unit: ignored
            ("alpha/use/consumer", "5000ms", "exit=0"),      # 5.0s
            ("beta/lo/lo_src", "200ms", "exit=0"),           # 0.2s
            ("beta/lo/lo_dst", "300ms", "exit=0"),           # 0.3s
        ],
        extra=("this\tline\thas\tfive\tfields", "malformed-without-tabs", ""),
    )

    edges_file = out / "skills_edges.txt"
    rw = run_reweight(edges_file, logs)
    check("weights: reweighter exits 0", rw.returncode == 0, rw.stderr.strip())

    weights = {(s, t): w for s, t, w in parse_edges(edges_file)}

    # Independent reimplementation of the documented weight rule. sink has no
    # logged run, so it is absent here and contributes 0 seconds.
    avg_secs = {
        "alpha/make/producer": 3.0,
        "alpha/use/consumer": 5.0,
        "beta/lo/lo_src": 0.2,
        "beta/lo/lo_dst": 0.3,
    }

    def expected(src: str, dst: str) -> float:
        return max(1.0, math.log1p(avg_secs.get(src, 0.0) + avg_secs.get(dst, 0.0)))

    check(
        "weights: exactly the three chained edges exist",
        len(weights) == 3,
        f"got {sorted(weights)}",
    )
    check(
        "weights: every edge = max(1, ln(1 + src_secs + dst_secs))",
        all(abs(float(w) - expected(s, t)) < 1e-4 for (s, t), w in weights.items()),
        f"got {weights}",
    )
    # producer(3.0s) + consumer(5.0s) = 8.0 -> ln(9) ~= 2.1972 > 1: proves the
    # logs moved this edge off the default weight of 1, and that averaging plus
    # the exit=0 / 'ms' filtering all landed on 3.0s for the producer.
    pc = weights.get(("alpha/make/producer", "alpha/use/consumer"))
    check(
        "weights: averaging + exit=0/ms filtering (producer->consumer = ln 9)",
        pc is not None and abs(float(pc) - math.log1p(8.0)) < 1e-4 and float(pc) > 1.0,
        f"got {pc}",
    )
    # consumer(5.0s) + sink(no logs -> 0s) = 5.0 -> ln(6) ~= 1.7918.
    cs = weights.get(("alpha/use/consumer", "alpha/use/sink"))
    check(
        "weights: unlogged endpoint contributes 0s (consumer->sink = ln 6)",
        cs is not None and abs(float(cs) - math.log1p(5.0)) < 1e-4,
        f"got {cs}",
    )
    # lo_src(0.2s) + lo_dst(0.3s) = 0.5 -> ln(1.5) ~= 0.405 < 1, so max(1, .)
    # clamps the weight to exactly 1.
    ll = weights.get(("beta/lo/lo_src", "beta/lo/lo_dst"))
    check(
        "weights: max(1, .) floor holds for small durations (lo_src->lo_dst = 1)",
        ll is not None and float(ll) == 1.0,
        f"got {ll}",
    )


# --------------------------------------------------------------------------
# Real-library tests — structural invariants over .memento/skills
# --------------------------------------------------------------------------


def test_real_library(tmp: Path) -> None:
    out = tmp / "real"
    result = run_builder(REAL_SKILLS, out)
    check("real: builder exits 0", result.returncode == 0, result.stderr.strip())

    nodes = parse_nodes(out / "skills_nodes.txt")
    raw_edges = parse_edges(out / "skills_edges.txt")
    edges = {(s, t) for s, t, _ in raw_edges}

    skill_files = list(REAL_SKILLS.rglob("SKILL.md"))
    check(
        "real: one node per SKILL.md",
        len(nodes) == len(skill_files),
        f"{len(nodes)} nodes vs {len(skill_files)} SKILL.md files",
    )
    check(
        "real: example_skill is excluded from the graph",
        not any("example_skill" in node_id for node_id in nodes),
    )
    check(
        "real: every node id has category/subcategory/name",
        all(node_id.count("/") == 2 for node_id in nodes),
        f"bad ids: {[n for n in nodes if n.count('/') != 2]}",
    )
    check(
        "real: no duplicate edges",
        len(raw_edges) == len(edges),
        f"{len(raw_edges)} lines vs {len(edges)} unique",
    )
    check("real: no self-edges", not any(s == t for s, t in edges))
    check(
        "real: every edge endpoint is a known node",
        all(s in nodes and t in nodes for s, t in edges),
    )
    check(
        "real: edges match the type rule exactly",
        edges == expected_edges(nodes),
        f"missing={sorted(expected_edges(nodes) - edges)} extra={sorted(edges - expected_edges(nodes))}",
    )


def test_idempotent_and_not_stale(tmp: Path) -> None:
    first, second = tmp / "run1", tmp / "run2"
    run_builder(REAL_SKILLS, first)
    run_builder(REAL_SKILLS, second)
    for filename in ("skills_nodes.txt", "skills_edges.txt"):
        check(
            f"real: regeneration is idempotent ({filename})",
            (first / filename).read_bytes() == (second / filename).read_bytes(),
        )
        committed = REAL_GRAPH / filename
        check(
            f"real: committed {filename} is up to date",
            committed.exists() and committed.read_bytes() == (first / filename).read_bytes(),
            "run `just build` to refresh it",
        )


def main() -> None:
    if not BUILDER.exists():
        print(f"error: builder not found at {BUILDER}", file=sys.stderr)
        sys.exit(1)

    tmp = Path(tempfile.mkdtemp(prefix="skillgraph-test-"))
    try:
        test_fixtures(tmp)
        test_one_edge_per_pair(tmp)
        test_comment_and_blank_tolerance(tmp)
        test_edge_weights_from_logs(tmp)
        test_real_library(tmp)
        test_idempotent_and_not_stale(tmp)
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
