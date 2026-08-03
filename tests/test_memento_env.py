#!/usr/bin/env python3
"""Assertion tests for MEMENTO_ENV resolution.

Usage:
    tests/test_memento_env.py

Checks that memento_env.sh and memento_env.py agree on the same three
rules, and that the tools which depend on them (build_skill_graph.sh,
find_connection.py, compute_edge_weights.py, run_logged.sh) follow the
resolved library rather than their own location:

    1. an already-set MEMENTO_ENV wins
    2. else a project-local `.memento/` in the current directory
    3. else $HOME/.memento

Every case runs against throwaway directories with a fake HOME, so the
real ~/.memento is never read or written.

Exits 0 if every assertion holds, 1 otherwise, printing one line per test.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMENTO = REPO_ROOT / ".memento"
ENV_SH = MEMENTO / "scripts" / "memento_env.sh"
ENV_PY = MEMENTO / "scripts" / "memento_env.py"

GREEN = "\033[0;32m"
RED = "\033[0;31m"
RESET = "\033[0m"

_results: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    _results.append((name, "" if condition else detail or "assertion failed"))


def run(cmd: list[str], cwd: Path, home: Path, override: Optional[str] = None) -> str:
    """Run cmd with a fake HOME, returning stripped stdout."""
    env = dict(os.environ)
    env["HOME"] = str(home)
    env.pop("MEMENTO_ENV", None)
    if override is not None:
        env["MEMENTO_ENV"] = override
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, env=env)
    if proc.returncode != 0:
        return f"<exit {proc.returncode}: {proc.stderr.strip()}>"
    return proc.stdout.strip()


def resolved_from(cwd: Path, output: str) -> Path:
    """Absolute form of a resolver's output, which may be relative to cwd.

    The shell resolver deliberately prints `./.memento` for the local case,
    so it must be anchored to the directory the resolver ran in, not to this
    test process's own working directory. Path(cwd, output) keeps an
    absolute output unchanged.
    """
    return Path(cwd, output).resolve()


def install_library(dest_parent: Path) -> Path:
    """Copy the repo's .memento into dest_parent, as `just install` does."""
    dest = dest_parent / ".memento"
    shutil.copytree(MEMENTO, dest)
    return dest


def test_resolution_rules(tmp: Path) -> None:
    home = tmp / "home"
    home.mkdir()
    library = install_library(home)
    elsewhere = tmp / "elsewhere"          # a directory with no .memento
    elsewhere.mkdir()
    local_project = tmp / "project"        # a directory that has its own
    local_project.mkdir()
    (local_project / ".memento").mkdir()

    sh, py = [str(ENV_SH)], [sys.executable, str(ENV_PY)]

    # Rule 3: no local .memento anywhere -> the personal library.
    check(
        "resolve: shell falls back to $HOME/.memento",
        run(sh, elsewhere, home) == str(library),
        f"got {run(sh, elsewhere, home)!r}, want {str(library)!r}",
    )
    check(
        "resolve: python falls back to $HOME/.memento",
        run(py, elsewhere, home) == str(library),
        f"got {run(py, elsewhere, home)!r}, want {str(library)!r}",
    )

    # Rule 2: a project-local .memento shadows the personal library.
    local_sh, local_py = run(sh, local_project, home), run(py, local_project, home)
    want_local = (local_project / ".memento").resolve()
    check(
        "resolve: shell prefers a project-local .memento",
        resolved_from(local_project, local_sh) == want_local,
        f"got {local_sh!r} -> {resolved_from(local_project, local_sh)}, want {want_local}",
    )
    check(
        "resolve: python prefers a project-local .memento",
        resolved_from(local_project, local_py) == want_local,
        f"got {local_py!r} -> {resolved_from(local_project, local_py)}, want {want_local}",
    )
    check(
        "resolve: local wins even when $HOME/.memento exists",
        resolved_from(local_project, local_sh) != library.resolve(),
        f"local resolution returned the home library: {local_sh!r}",
    )

    # Rule 1: an explicit MEMENTO_ENV beats both.
    override = str(tmp / "explicit")
    check(
        "resolve: shell honours an explicit MEMENTO_ENV",
        run(sh, local_project, home, override=override) == override,
        f"got {run(sh, local_project, home, override=override)!r}",
    )
    check(
        "resolve: python honours an explicit MEMENTO_ENV",
        run(py, local_project, home, override=override) == override,
        f"got {run(py, local_project, home, override=override)!r}",
    )

    # The two implementations must never disagree.
    check(
        "resolve: shell and python agree outside a project",
        resolved_from(elsewhere, run(sh, elsewhere, home))
        == resolved_from(elsewhere, run(py, elsewhere, home)),
    )
    check(
        "resolve: shell and python agree inside a project",
        resolved_from(local_project, local_sh) == resolved_from(local_project, local_py),
    )


def test_tools_follow_the_resolved_library(tmp: Path) -> None:
    """The tools must act on $MEMENTO_ENV, not on their own location."""
    home = tmp / "home2"
    home.mkdir()
    library = install_library(home)
    elsewhere = tmp / "elsewhere2"
    elsewhere.mkdir()

    graph_dir = library / "graph"
    shutil.rmtree(graph_dir, ignore_errors=True)

    # The builder, invoked from a directory with no .memento, must write
    # into the home library rather than into the repo it was copied from.
    out = run([str(library / "scripts" / "build_skill_graph.sh")], elsewhere, home)
    nodes, edges = graph_dir / "skills_nodes.txt", graph_dir / "skills_edges.txt"
    check(
        "tools: builder writes into the resolved library",
        nodes.is_file() and edges.is_file(),
        f"no graph at {graph_dir}: {out!r}",
    )
    repo_nodes = (MEMENTO / "graph" / "skills_nodes.txt").read_text(encoding="utf-8")
    check(
        "tools: builder produced the same nodes as the repo library",
        nodes.is_file() and nodes.read_text(encoding="utf-8") == repo_nodes,
        "home-resolved build differs from the repo build",
    )

    # The finder must default --nodes/--edges to the same resolved library,
    # so it works with no path flags from anywhere.
    found = run(
        [
            str(library / "scripts" / "find_connection.py"),
            "--from", "skill:video/download/from_youtube",
            "--to", "type:TEXT_FILE_TXT",
        ],
        elsewhere,
        home,
    )
    check(
        "tools: finder resolves its graph with no path flags",
        "CHAIN:" in found,
        f"got {found!r}",
    )

    # run_logged.sh must append to the resolved library's log, not to the
    # tree it happens to live in.
    logs = library / "logs"
    before = set(logs.glob("skill_runs-*.log")) if logs.is_dir() else set()
    run(
        [str(library / "resources" / "run_logged.sh"), "demo/test/probe", "/bin/echo", "hi"],
        elsewhere,
        home,
    )
    after = set(logs.glob("skill_runs-*.log")) if logs.is_dir() else set()
    logged = any("demo/test/probe" in p.read_text(encoding="utf-8") for p in after)
    check(
        "tools: run_logged writes into the resolved library's log",
        bool(after) and logged,
        f"no probe line under {logs} (before={len(before)}, after={len(after)})",
    )


def main() -> None:
    for path in (ENV_SH, ENV_PY):
        if not path.exists():
            print(f"error: resolver not found at {path}", file=sys.stderr)
            sys.exit(1)

    tmp = Path(tempfile.mkdtemp(prefix="mementoenv-test-"))
    try:
        test_resolution_rules(tmp)
        test_tools_follow_the_resolved_library(tmp)
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
