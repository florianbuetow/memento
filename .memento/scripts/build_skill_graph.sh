#!/usr/bin/env bash
# Build a chainable-skill graph from SKILL.md files.
#
# Scans SKILLS_DIR for SKILL.md files, parses the YAML frontmatter
# (name, inputs, outputs) using the `[~]PARAM::TYPE` convention --
# a leading `~` marks the parameter as optional -- and emits two files:
#
#   skills_nodes.txt  one line per skill with parsed inputs and outputs
#   skills_edges.txt  `source target weight` lines compatible with the
#                     Dijkstra script in .memento/scripts/dijkstra.py.
#                     Weights default to 1 and are recomputed from the run
#                     logs by compute_edge_weights.py (see below).
#
# An edge A -> B is emitted when any output TYPE of A matches any input
# TYPE of B (the `~` optional marker is stripped before matching, so an
# upstream output can satisfy a required or optional input alike).
# A TYPE may be a union written `[AUDIO_FILE | VIDEO_FILE]`; it is
# normalized to `AUDIO_FILE|VIDEO_FILE` and matches when any alternative
# on one side equals any alternative on the other.
#
# Usage: build_skill_graph.sh [SKILLS_DIR] [OUT_DIR]
#   SKILLS_DIR  defaults to .memento/skills
#   OUT_DIR     defaults to .memento/graph

set -euo pipefail

SKILLS_DIR="${1:-.memento/skills}"
OUT_DIR="${2:-.memento/graph}"

if [[ ! -d "$SKILLS_DIR" ]]; then
    echo "error: skills directory not found: $SKILLS_DIR" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
NODES_FILE="$OUT_DIR/skills_nodes.txt"
EDGES_FILE="$OUT_DIR/skills_edges.txt"

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

# Parse one SKILL.md file. Emits a single space-separated line:
#   <category/subcategory/name> <inputs_csv> <outputs_csv>
# The node id is qualified with category and subcategory so that skills
# sharing a name (e.g. audio/download/from_youtube and
# video/download/from_youtube) stay distinct in the graph.
# Each csv entry is `[~]TYPE`, preserving the optional marker. An empty
# inputs or outputs list is emitted as `-`.
parse_skill() {
    awk '
    BEGIN { in_fm = 0; section = "" }
    /^---[[:space:]]*$/ {
        if (!in_fm) { in_fm = 1; next }
        exit
    }
    !in_fm { next }
    /^name:[[:space:]]/ {
        v = $0
        sub(/^name:[[:space:]]+/, "", v)
        sub(/[[:space:]]+$/, "", v)
        name = v
        section = ""
        next
    }
    /^category:[[:space:]]/ {
        v = $0
        sub(/^category:[[:space:]]+/, "", v)
        sub(/[[:space:]]+$/, "", v)
        category = v
        section = ""
        next
    }
    /^subcategory:[[:space:]]/ {
        v = $0
        sub(/^subcategory:[[:space:]]+/, "", v)
        sub(/[[:space:]]+$/, "", v)
        subcategory = v
        section = ""
        next
    }
    /^inputs:[[:space:]]*$/  { section = "in";  next }
    /^outputs:[[:space:]]*$/ { section = "out"; next }
    /^[a-zA-Z_][a-zA-Z0-9_]*:/ { section = ""; next }
    /^[[:space:]]+-[[:space:]]/ {
        if (section != "in" && section != "out") next
        v = $0
        sub(/^[[:space:]]+-[[:space:]]+/, "", v)
        sub(/[[:space:]]+$/, "", v)
        opt = ""
        if (substr(v, 1, 1) == "~") { opt = "~"; v = substr(v, 2) }
        i = index(v, "::")
        t = (i > 0) ? substr(v, i + 2) : "UNKNOWN"
        gsub(/[][ ]/, "", t)    # `[A | B]` -> `A|B`
        entry = opt t
        if (section == "in") ins  = (ins  == "" ? entry : ins  "," entry)
        else                 outs = (outs == "" ? entry : outs "," entry)
    }
    END {
        if (name == "") exit
        id = name
        if (category != "" && subcategory != "")
            id = category "/" subcategory "/" name
        print id, (ins  == "" ? "-" : ins), (outs == "" ? "-" : outs)
    }
    ' "$1"
}

while IFS= read -r -d '' f; do
    parse_skill "$f"
done < <(find "$SKILLS_DIR" -type f -iname 'SKILL.md' -print0) > "$tmp"

awk '{ printf "%s\tinputs=%s\toutputs=%s\n", $1, $2, $3 }' "$tmp" > "$NODES_FILE"

awk '
# True when the union types a and b share at least one alternative.
function types_match(a, b,    na, nb, A, B, x, y) {
    na = split(a, A, "|")
    nb = split(b, B, "|")
    for (x = 1; x <= na; x++)
        for (y = 1; y <= nb; y++)
            if (A[x] == B[y]) return 1
    return 0
}
{
    n++
    name[n] = $1
    ins[n]  = $2
    outs[n] = $3
}
END {
    for (i = 1; i <= n; i++) {
        n_o = split(outs[i], O, ",")
        for (j = 1; j <= n; j++) {
            if (i == j) continue
            n_i = split(ins[j], I, ",")
            for (oi = 1; oi <= n_o; oi++) {
                o = O[oi]
                if (o == "-" || o == "UNKNOWN") continue
                sub(/^~/, "", o)
                for (ii = 1; ii <= n_i; ii++) {
                    p = I[ii]
                    if (p == "-" || p == "UNKNOWN") continue
                    sub(/^~/, "", p)
                    if (types_match(o, p)) {
                        print name[i], name[j], 1
                        oi = n_o; break    # one edge per (source, target)
                    }
                }
            }
        }
    }
}
' "$tmp" > "$EDGES_FILE"

# Reweight edges from run-log durations. The default weight stays 1; with
# log data an edge A -> B becomes max(1, ln(1 + avg_secs(A) + avg_secs(B))),
# where avg_secs is each skill's mean successful-run duration over the past
# 3 months of .memento/logs/skill_runs-<YYYY-MM>.log files.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SCRIPT_DIR/compute_edge_weights.py" ]]; then
    python3 "$SCRIPT_DIR/compute_edge_weights.py"         --edges "$EDGES_FILE" --logs-dir "$SCRIPT_DIR/../logs" --months 3
fi

n_nodes=$(wc -l < "$NODES_FILE" | tr -d ' ')
n_edges=$(wc -l < "$EDGES_FILE" | tr -d ' ')
echo "wrote $NODES_FILE ($n_nodes nodes) and $EDGES_FILE ($n_edges edges)" >&2
