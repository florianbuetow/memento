#!/usr/bin/env python3
"""Find a chain of atomic skills, or the closest missing link, in the skill graph.

Runs Dijkstra forward from the start endpoint and backward from the goal
endpoint (bidirectional) over the generated graph files. If the two
frontiers meet, the shortest skill chain is printed with the value type
linking each consecutive pair. If they never meet, the closest connection
between the forward-reachable and backward-reachable regions is computed
and the missing atomic skill that would bridge the gap is flagged
explicitly, together with the input/output types it must have.

Usage:
    find_connection.py --from ENDPOINT --to ENDPOINT
                       [--nodes PATH] [--edges PATH] [--max-bridges N]

ENDPOINT forms:
    skill:<category/subcategory/name>   a specific skill node
    type:<TYPE>                         a value type from the skill guide
    bare value                          auto-detected: a known skill id,
                                        else a TYPE when written like one
                                        (A-Z, 0-9, _ and |)

Endpoint semantics:
    --from skill:S   chains start with skill S.
    --from type:T    a value of type T is available; chains may start at
                     any skill with an input matching T, or at a missing
                     skill consuming T directly.
    --to skill:G     chains end with skill G.
    --to type:T      a value of type T is wanted; chains may end at any
                     skill with an output matching T, or at a missing
                     skill producing T directly.

Output markers (one per line, greppable):
    FROM: / TO:            resolved endpoints
    CHAIN: / STEP:         shortest chain and its typed steps
    NO CHAIN:              no chain exists
    FORWARD REACHABLE: / BACKWARD REACHABLE:
                           explored regions with Dijkstra distances
    CLOSEST CONNECTION:    best pair of anchor points across the gap
    MISSING SKILL:         explicit flag: the input/output types a new
                           atomic skill needs in order to close the gap
    GAP CHAIN:             full chain with the missing skill inlined
    UNBRIDGEABLE:          no anchor point exists on that side

Exit codes: 0 chain found, 2 no chain (gap report printed), 1 error.
"""

import argparse
import heapq
import re
import sys
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_NODES = SCRIPT_DIR.parent / "graph" / "skills_nodes.txt"
DEFAULT_EDGES = SCRIPT_DIR.parent / "graph" / "skills_edges.txt"

INFINITE = float("inf")
TYPE_RE = re.compile(r"^[A-Z0-9_|]+$")


def die(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def fmt(value: float) -> str:
    """Render a distance the way the graph files do: integers stay integral."""
    if value == int(value):
        return str(int(value))
    return f"{value:.6g}"


def parse_type_list(raw: str) -> list[str]:
    """`AUDIO_FILE|VIDEO_FILE,~TEXT` -> ['AUDIO_FILE|VIDEO_FILE', 'TEXT']; '-' -> []."""
    if raw == "-":
        return []
    types = []
    for entry in raw.split(","):
        entry = entry.lstrip("~")
        if entry and entry != "UNKNOWN":
            types.append(entry)
    return types


def read_nodes(path: Path) -> dict[str, tuple[list[str], list[str]]]:
    """Node id -> (input types, output types), optional markers stripped."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        die(f"cannot read nodes file {path}: {exc}")
    nodes: dict[str, tuple[list[str], list[str]]] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not parts[1].startswith("inputs=") or not parts[2].startswith("outputs="):
            die(f"{path}:{line_no}: malformed node line: {line!r}")
        nodes[parts[0]] = (
            parse_type_list(parts[1].removeprefix("inputs=")),
            parse_type_list(parts[2].removeprefix("outputs=")),
        )
    if not nodes:
        die(f"no nodes found in {path} — run `just build` first")
    return nodes


def read_edges(
    path: Path, nodes: dict[str, tuple[list[str], list[str]]]
) -> tuple[dict[str, list[tuple[str, float]]], dict[str, list[tuple[str, float]]]]:
    """Forward and reversed adjacency lists, neighbors sorted for determinism."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        die(f"cannot read edges file {path}: {exc}")
    fwd: dict[str, list[tuple[str, float]]] = {}
    rev: dict[str, list[tuple[str, float]]] = {}
    for line_no, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) != 3:
            die(f"{path}:{line_no}: malformed edge line: {line!r}")
        source, target, raw_weight = fields
        try:
            weight = float(raw_weight)
        except ValueError:
            die(f"{path}:{line_no}: non-numeric weight {raw_weight!r}")
        if source not in nodes or target not in nodes:
            die(f"{path}:{line_no}: edge references unknown node {source!r} or {target!r} — graph files out of sync, run `just build`")
        fwd.setdefault(source, []).append((target, weight))
        rev.setdefault(target, []).append((source, weight))
    for adjacency in (fwd, rev):
        for neighbors in adjacency.values():
            neighbors.sort()
    return fwd, rev


def types_match(a: str, b: str) -> bool:
    """A union type matches when the two share at least one alternative."""
    return bool(set(a.split("|")) & set(b.split("|")))


def resolve_endpoint(
    raw: str, nodes: dict[str, tuple[list[str], list[str]]], side: str
) -> tuple[str, str, set[str]]:
    """Return (kind, value, node set). kind is 'skill' or 'type'."""
    if raw.startswith("skill:"):
        skill_id = raw.removeprefix("skill:")
        if skill_id not in nodes:
            die(f"unknown skill {skill_id!r} (not in the nodes file)")
        return "skill", skill_id, {skill_id}
    if raw.startswith("type:"):
        value = raw.removeprefix("type:")
    elif raw in nodes:
        return "skill", raw, {raw}
    elif TYPE_RE.match(raw):
        value = raw
    else:
        die(f"unknown skill {raw!r} — use type:<TYPE> if a value type was meant")
    if not TYPE_RE.match(value):
        die(f"invalid type {value!r} — types use A-Z, 0-9, _ and |")
    index = 0 if side == "from" else 1
    matched = {
        node_id
        for node_id, types in nodes.items()
        if any(types_match(value, t) for t in types[index])
    }
    return "type", value, matched


def describe(kind: str, value: str, node_set: set[str], side: str) -> str:
    if kind == "skill":
        return f"skill {value}"
    role = "consumers" if side == "from" else "producers"
    members = ", ".join(sorted(node_set)) if node_set else "none"
    return f"type {value} ({role}: {members})"


def dijkstra(
    adjacency: dict[str, list[tuple[str, float]]], sources: set[str]
) -> tuple[dict[str, float], dict[str, str]]:
    """Multi-source Dijkstra. Returns (distances, predecessors)."""
    dist = {source: 0.0 for source in sources}
    pred: dict[str, str] = {}
    heap = [(0.0, source) for source in sorted(sources)]
    heapq.heapify(heap)
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, INFINITE):
            continue
        for neighbor, weight in adjacency.get(node, []):
            candidate = d + weight
            if candidate < dist.get(neighbor, INFINITE):
                dist[neighbor] = candidate
                pred[neighbor] = node
                heapq.heappush(heap, (candidate, neighbor))
    return dist, pred


def walk_pred(node: str, pred: dict[str, str]) -> list[str]:
    """Chain of predecessor links starting at node: [node, pred[node], ...]."""
    path = [node]
    while path[-1] in pred:
        path.append(pred[path[-1]])
    return path


def link_types(nodes: dict[str, tuple[list[str], list[str]]], a: str, b: str) -> list[str]:
    """Type alternatives shared by a's outputs and b's inputs."""
    out_alts = {alt for t in nodes[a][1] for alt in t.split("|")}
    in_alts = {alt for t in nodes[b][0] for alt in t.split("|")}
    return sorted(out_alts & in_alts)


def alternatives(types: list[str]) -> list[str]:
    return sorted({alt for t in types for alt in t.split("|")})


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="find_connection.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--from", dest="src", required=True, metavar="ENDPOINT")
    parser.add_argument("--to", dest="dst", required=True, metavar="ENDPOINT")
    parser.add_argument("--nodes", type=Path, default=DEFAULT_NODES)
    parser.add_argument("--edges", type=Path, default=DEFAULT_EDGES)
    parser.add_argument("--max-bridges", type=int, default=3, metavar="N")
    args = parser.parse_args(argv[1:])
    if args.max_bridges < 1:
        die("--max-bridges must be at least 1")

    nodes = read_nodes(args.nodes)
    fwd, rev = read_edges(args.edges, nodes)

    from_kind, from_value, starts = resolve_endpoint(args.src, nodes, "from")
    to_kind, to_value, goals = resolve_endpoint(args.dst, nodes, "to")

    print(f"FROM: {describe(from_kind, from_value, starts, 'from')}")
    print(f"TO: {describe(to_kind, to_value, goals, 'to')}")

    dist_f, pred_f = dijkstra(fwd, starts)
    dist_b, pred_b = dijkstra(rev, goals)

    meeting = [n for n in dist_f if n in dist_b]
    if meeting:
        meet = min(meeting, key=lambda n: (dist_f[n] + dist_b[n], n))
        chain = list(reversed(walk_pred(meet, pred_f))) + walk_pred(meet, pred_b)[1:]
        print(f"CHAIN: {' -> '.join(chain)}")
        for a, b in zip(chain, chain[1:]):
            linked = "|".join(link_types(nodes, a, b)) or "?"
            print(f"STEP: {a} -[{linked}]-> {b}")
        return 0

    # No chain: report the gap and the missing skill that would close it.
    print(f"NO CHAIN: {describe(from_kind, from_value, starts, 'from')} -/-> {describe(to_kind, to_value, goals, 'to')}")
    forward = sorted(dist_f, key=lambda n: (dist_f[n], n))
    backward = sorted(dist_b, key=lambda n: (dist_b[n], n))
    print("FORWARD REACHABLE: " + (", ".join(f"{n} ({fmt(dist_f[n])})" for n in forward) or "none"))
    print("BACKWARD REACHABLE: " + (", ".join(f"{n} ({fmt(dist_b[n])})" for n in backward) or "none"))

    # A bridge attaches to a forward-reachable skill with outputs (or to the
    # available start type directly) and to a backward-reachable skill with
    # inputs (or to the wanted goal type directly).
    bridge_sources = [(dist_f[u], u, nodes[u][1]) for u in dist_f if nodes[u][1]]
    if from_kind == "type":
        bridge_sources.append((0.0, f"(available type {from_value})", [from_value]))
    bridge_targets = [(dist_b[v], v, nodes[v][0]) for v in dist_b if nodes[v][0]]
    if to_kind == "type":
        bridge_targets.append((0.0, f"(goal type {to_value})", [to_value]))

    if not bridge_sources:
        print(f"UNBRIDGEABLE: nothing forward-reachable from {describe(from_kind, from_value, starts, 'from')} produces an output — no missing skill can attach there")
    if not bridge_targets:
        print(f"UNBRIDGEABLE: nothing backward-reachable from {describe(to_kind, to_value, goals, 'to')} consumes an input — no missing skill can attach there")
    if not bridge_sources or not bridge_targets:
        return 2

    candidates = sorted(
        (df + db, u, v, outs, ins, df, db)
        for df, u, outs in bridge_sources
        for db, v, ins in bridge_targets
    )
    for _, u, v, outs, ins, df, db in candidates[: args.max_bridges]:
        print(f"CLOSEST CONNECTION: {u} ~~> {v} (existing steps: {fmt(df)} from start, {fmt(db)} to goal)")
        print(f"MISSING SKILL: input one of {{{', '.join(alternatives(outs))}}}; output one of {{{', '.join(alternatives(ins))}}}")
        prefix = list(reversed(walk_pred(u, pred_f))) if u in dist_f else [u]
        suffix = walk_pred(v, pred_b) if v in dist_b else [v]
        print("GAP CHAIN: " + " -> ".join(prefix + ["[MISSING SKILL]"] + suffix))
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
