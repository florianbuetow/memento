#!/usr/bin/env python3
"""Assertion tests for the plugin's bundled machinery payload.

Usage:
    tests/test_plugin_payload.py

A plugin is installed on its own: Claude Code unpacks only plugins/memento/
into the plugin cache, so the repository justfile and the repository .memento/
are absent at install time. Everything /memento-install needs must therefore
live inside plugins/memento/.

The load-bearing rule these tests defend:

    ATOMIC SKILLS ARE NEVER SHIPPED.

Everything under .memento/skills/<category>/ is the user's own procedural
memory -- private, deliberately untracked, and not the plugin's to distribute.
The payload carries machinery only: index.md, scripts/, resources/ and the
category registry. `just sync-plugin` regenerates it from an allowlist.

Exits 0 if every assertion holds, 1 otherwise, printing one line per test.
"""

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMENTO = REPO_ROOT / ".memento"
PLUGIN = REPO_ROOT / "plugins" / "memento"
PAYLOAD = PLUGIN / "memento"

# Exactly what the payload may contain, relative to the library root.
ALLOWED_ROOTS = {"index.md", "scripts", "resources", "skills"}

GREEN = "\033[0;32m"
RED = "\033[0;31m"
RESET = "\033[0m"

_results: list[tuple[str, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    _results.append((name, "" if condition else detail or "assertion failed"))


def files_under(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p.name != ".DS_Store"
    }


def test_no_atomic_skills_are_shipped() -> None:
    """The rule that must never regress."""
    leaked = sorted(
        str(p.relative_to(PAYLOAD)) for p in PAYLOAD.rglob("SKILL.md")
        if "resources" not in p.relative_to(PAYLOAD).parts
    )
    check(
        "payload: ships ZERO atomic skills",
        not leaked,
        f"{len(leaked)} atomic skill(s) leaked into the plugin: {leaked[:3]} — run `just sync-plugin`",
    )

    skills_dir = PAYLOAD / "skills"
    stray = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.is_dir() else []
    check(
        "payload: skills/ holds only the category registry",
        stray == ["categories.md"],
        f"skills/ contains {stray} — only categories.md may ship",
    )

    check(
        "payload: no category directory was copied",
        not any((PAYLOAD / "skills" / d.name).exists()
                for d in (MEMENTO / "skills").iterdir() if d.is_dir()),
        "a .memento/skills/<category>/ directory reached the plugin",
    )


def test_payload_is_machinery_and_current() -> None:
    check(
        "payload: exists",
        PAYLOAD.is_dir(),
        f"{PAYLOAD} is missing — run `just sync-plugin`",
    )
    if not PAYLOAD.is_dir():
        return

    roots = {p.name for p in PAYLOAD.iterdir()}
    check(
        "payload: contains only allowed top-level entries",
        roots <= ALLOWED_ROOTS,
        f"unexpected entries: {sorted(roots - ALLOWED_ROOTS)}",
    )

    # Machinery must match the repository copy, or an install ships stale code.
    for sub in ("scripts", "resources"):
        source, shipped = files_under(MEMENTO / sub), files_under(PAYLOAD / sub)
        check(
            f"payload: {sub}/ matches .memento/{sub}/",
            source == shipped,
            f"differs: missing {sorted(source - shipped)[:2]}, extra {sorted(shipped - source)[:2]} — run `just sync-plugin`",
        )
        differing = [
            rel for rel in sorted(source & shipped)
            if (MEMENTO / sub / rel).read_bytes() != (PAYLOAD / sub / rel).read_bytes()
        ]
        check(
            f"payload: {sub}/ is byte-identical",
            not differing,
            f"{len(differing)} file(s) differ, e.g. {differing[:2]} — run `just sync-plugin`",
        )

    check(
        "payload: excludes the generated graph and logs",
        not (PAYLOAD / "graph").exists() and not (PAYLOAD / "logs").exists(),
        "graph/ or logs/ leaked into the payload; both are rebuilt on install",
    )

    # Everything shipped must be git-tracked. Untracked means personal.
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", ".memento"],
        capture_output=True, text=True, cwd=REPO_ROOT,
    ).stdout.split()
    shipped_sources = {f".memento/{p}" for p in files_under(PAYLOAD)}
    overlap = sorted(shipped_sources & set(untracked))
    check(
        "payload: ships nothing that is untracked in git",
        not overlap,
        f"{len(overlap)} untracked file(s) would be published: {overlap[:3]}",
    )


def test_plugin_is_self_contained() -> None:
    justfile = PLUGIN / "justfile"
    check("plugin: ships its own justfile", justfile.is_file(), f"{justfile} is missing")
    if justfile.is_file():
        check(
            "plugin: justfile defines an install recipe",
            re.search(r"^install:", justfile.read_text(encoding="utf-8"), re.MULTILINE) is not None,
            "no `install:` recipe found",
        )
        check(
            "plugin: justfile parses",
            subprocess.run(
                ["just", "--justfile", str(justfile), "--summary"],
                capture_output=True, text=True,
            ).returncode == 0,
            "`just --summary` rejected the plugin justfile",
        )

    check(
        "plugin: the install skill exists",
        (PLUGIN / "skills" / "memento-install" / "SKILL.md").is_file(),
        "plugins/memento/skills/memento-install/SKILL.md is missing",
    )

    # A skill runs from the plugin cache, where the repository is absent, so a
    # literal repo path would break. Prose naming `.memento/` as a concept is
    # fine; a path with a subdirectory component is not.
    repo_only = re.compile(
        r"(?<![\w/])\.memento/(?:scripts|graph|resources|skills|logs)\b"
        r"|(?<![\w/])(?:tests|docs)/"
    )
    for skill in sorted((PLUGIN / "skills").rglob("SKILL.md")):
        offenders = [
            line.strip()
            for line in skill.read_text(encoding="utf-8").splitlines()
            if repo_only.search(line) and "CLAUDE_PLUGIN_ROOT" not in line
        ]
        check(
            f"plugin: {skill.parent.name} names no repository-only path",
            not offenders,
            f"{len(offenders)} line(s) reference a path absent from the plugin cache: {offenders[:2]}",
        )


def main() -> None:
    test_no_atomic_skills_are_shipped()
    test_payload_is_machinery_and_current()
    test_plugin_is_self_contained()

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
