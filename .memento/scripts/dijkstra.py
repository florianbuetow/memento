#!/usr/bin/env python3
"""Calculate shortest path lengths according to Dijkstra's algorithm.

Usage:
    dijkstra.py u=<start> [t=<end>] [dir=<direction>] <file>
    dijkstra.py help

    file       input file containing graph specification, i.e. definition of edges
    start      label of starting vertex
    end        label of ending vertex; if not given, the shortest lengths for
               ALL vertices are calculated
    direction  U|D (default U); file defines an Undirected or Directed graph

Example:

    dijkstra.py u=a t=g dir=D graphdef.txt

Input format is one edge per line, `<from> <to> <weight>`, whitespace
separated. Lines starting with `#` are comments; blank and short (< 3 field)
lines are skipped. Unreachable vertices are reported with the length 999999.
Result lines are sorted by vertex label.
"""

import sys
from typing import NoReturn

INFINITE = 999999


def die(message: str) -> NoReturn:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def show_help() -> None:
    print("")
    print("PURPOSE: Calculates shortest path lengths according to Dijkstra's algorithm.")
    print("")
    print("USAGE:   dijkstra.py u=<start> [t=<end>] [dir=<direction>] <file>")
    print("         dijkstra.py help")
    print("")
    print("         file       input file containing graph specification, i.e. definition of edges")
    print("         start      label of starting vertex")
    print("         end        label of ending vertex; if not given, the shortest lengths for ALL vertices are calculated")
    print("         direction  U|D (default U); file defines an Undirected or Directed graph")
    print("")
    print("EXAMPLE: dijkstra.py u=a t=g dir=D graphdef.txt")
    print("")
    print('         starting (ending) vertex is "a"("g"), file "graphdef.txt" specifies a directed graph')
    print("")


def show_input_params(path: str, direction: str, u: str, t: str) -> None:
    print("----- INPUT PARAMETERS -----")
    print(f"file: {path}")
    print(f"direction type: {'undirected' if direction == 'U' else 'directed'}")
    print(f"starting vertex: {u}")
    print(f"ending vertex: {t if t else '(not specified) - calculation for all vertices'}")


def format_length(value: float) -> str:
    """Render a length: integers print without a decimal point."""
    if value == int(value):
        return str(int(value))
    return f"{value:.6g}"


def read_graph(path: str, direction: str) -> tuple[dict[str, dict[str, float]], set[str]]:
    """Build adjacency lists and the vertex set from an edge-list file."""
    graph: dict[str, dict[str, float]] = {}
    vertices: set[str] = set()

    try:
        with open(path, encoding="utf-8") as handle:
            lines = handle.readlines()
    except OSError as exc:
        die(f"cannot read graph file {path}: {exc}")

    for line in lines:
        if line.startswith("#"):
            continue
        fields = line.split()
        if len(fields) < 3:
            continue

        source, target, raw_weight = fields[0], fields[1], fields[2]
        try:
            weight = float(raw_weight)
        except ValueError:
            die(f"non-numeric weight {raw_weight!r} on edge {source} -> {target}")

        vertices.add(source)
        vertices.add(target)
        graph.setdefault(source, {})[target] = weight
        if direction == "U":
            graph.setdefault(target, {})[source] = weight

    return graph, vertices


def dijkstra(
    graph: dict[str, dict[str, float]], vertices: set[str], u: str, t: str
) -> dict[str, float]:
    """Shortest path lengths from u, over the vertices of graph."""
    calc_all = t == ""

    lengths = {v: (0.0 if v == u else graph.get(u, {}).get(v, INFINITE)) for v in vertices}

    unvisited = set(vertices)
    unvisited.discard(u)

    while unvisited:
        # Pick the unvisited vertex with the smallest known length. Vertices
        # still at INFINITE are unreachable and are never selected.
        current = ""
        smallest = INFINITE
        for v in unvisited:
            if lengths[v] < smallest:
                current = v
                smallest = lengths[v]

        if current == "" or (not calc_all and current == t):
            break

        unvisited.remove(current)

        for v in unvisited:
            weight = graph.get(current, {}).get(v)
            if weight is not None and lengths[v] > lengths[current] + weight:
                lengths[v] = lengths[current] + weight

    return lengths


def show_result(lengths: dict[str, float], t: str) -> None:
    print("----- RESULT -----")
    if t == "":
        for vertex in sorted(lengths):
            print(f"L({vertex})={format_length(lengths[vertex])}")
    else:
        print(f"L({t})={format_length(lengths.get(t, INFINITE))}")


def main(argv: list[str]) -> None:
    options: dict[str, str] = {}
    positional: list[str] = []

    for arg in argv[1:]:
        key, sep, value = arg.partition("=")
        if sep and key in ("u", "t", "dir"):
            options[key] = value
        else:
            positional.append(arg)

    path = positional[0] if positional else ""
    u = options.get("u", "")
    t = options.get("t", "")
    direction = options.get("dir", "") or "U"

    if path == "help" or path == "" or u == "" or direction not in ("U", "D"):
        show_help()
        return

    show_input_params(path, direction, u, t)

    graph, vertices = read_graph(path, direction)
    if u not in vertices:
        die(f"starting vertex {u!r} does not occur in {path}")

    lengths = dijkstra(graph, vertices, u, t)
    show_result(lengths, t)


if __name__ == "__main__":
    main(sys.argv)
