#!/usr/bin/env python3
"""Reweight skill-graph edges from measured run durations.

Every edge starts at the default weight 1. When the run logs contain data,
the weight of an edge A -> B becomes

    max(1, ln(1 + avg_secs(A) + avg_secs(B)))

where avg_secs(X) is the mean duration in seconds of X's successful runs
(exit=0) across the past N months of log files (default 3, current month
included). A skill with no logged runs contributes 0 seconds, so an edge
between two unmeasured skills keeps the default weight 1 exactly - the
committed graph is byte-identical until real data exists.

Log files (written by resources/run_logged.sh, rotated monthly):
    .memento/logs/skill_runs-<YYYY-MM>.log
one tab-separated line per run:
    <ISO8601 timestamp>  <skill id>  <duration ms>  exit=<code>

Usage:
    compute_edge_weights.py --edges PATH [--logs-dir DIR] [--months N] [--dry-run]

Rewrites the weight column of the edge list in place (--dry-run prints the
result to stdout instead) and reports a one-line summary on stderr.

Exit codes: 0 success (including "no log data"), 1 error.
"""

import argparse
import math
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_LOGS = SCRIPT_DIR.parent / "logs"


def die(message: str) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def window_months(count: int, today: date) -> list[str]:
    """The current month and the count-1 months before it, as YYYY-MM."""
    year, month = today.year, today.month
    names = []
    for _ in range(count):
        names.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return names


def load_average_seconds(logs_dir: Path, months: list[str]) -> dict[str, float]:
    """Mean duration in seconds of each skill's successful runs in the window."""
    total_ms: dict[str, float] = {}
    runs: dict[str, int] = {}
    for month in months:
        path = logs_dir / f"skill_runs-{month}.log"
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            parts = line.split("\t")
            if len(parts) != 4:
                continue                       # malformed line: skip
            _, skill_id, duration, exit_field = parts
            if exit_field.strip() != "exit=0":
                continue                       # failed runs say nothing about task duration
            duration = duration.strip()
            if not duration.endswith("ms"):
                continue
            try:
                ms = float(duration[:-2])
            except ValueError:
                continue
            total_ms[skill_id] = total_ms.get(skill_id, 0.0) + ms
            runs[skill_id] = runs.get(skill_id, 0) + 1
    return {skill: total_ms[skill] / runs[skill] / 1000.0 for skill in runs}


def edge_weight(avg_secs: dict[str, float], source: str, target: str) -> float:
    combined = avg_secs.get(source, 0.0) + avg_secs.get(target, 0.0)
    return max(1.0, math.log1p(combined))


def format_weight(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f"{value:.4f}".rstrip("0").rstrip(".")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        prog="compute_edge_weights.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--edges", type=Path, required=True, metavar="PATH")
    parser.add_argument("--logs-dir", type=Path, default=DEFAULT_LOGS, metavar="DIR")
    parser.add_argument("--months", type=int, default=3, metavar="N")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv[1:])
    if args.months < 1:
        die("--months must be at least 1")
    if not args.edges.is_file():
        die(f"edges file not found: {args.edges}")

    months = window_months(args.months, date.today())
    avg_secs = load_average_seconds(args.logs_dir, months)

    out_lines = []
    reweighted = 0
    for line_no, line in enumerate(args.edges.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            out_lines.append(line)
            continue
        fields = line.split()
        if len(fields) != 3:
            die(f"{args.edges}:{line_no}: malformed edge line: {line!r}")
        source, target, _ = fields
        weight = edge_weight(avg_secs, source, target)
        if weight != 1.0:
            reweighted += 1
        out_lines.append(f"{source} {target} {format_weight(weight)}")

    text = "\n".join(out_lines) + ("\n" if out_lines else "")
    if args.dry_run:
        sys.stdout.write(text)
    else:
        args.edges.write_text(text, encoding="utf-8")

    print(
        f"edge weights: {reweighted} of {len(out_lines)} edges reweighted from "
        f"{len(avg_secs)} skill(s) with log data (window: {', '.join(months)})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
