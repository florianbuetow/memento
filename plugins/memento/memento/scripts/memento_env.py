#!/usr/bin/env python3
"""Resolve MEMENTO_ENV -- the memento directory every tool reads from.

Python counterpart of memento_env.sh; the two implement the same rules:

  1. An already-set MEMENTO_ENV environment variable wins, so a caller can
     point the whole toolchain at any library.
  2. A project-local `.memento/` in the current working directory. A
     repository that carries its own skills shadows the personal library.
  3. `$HOME/.memento` -- the library installed by `just install`, which is
     what makes the skills work from any directory.

Import it:
    from memento_env import resolve_memento_env
Or run it to print the resolved path:
    memento_env.py
"""

import os
import sys
from pathlib import Path


def resolve_memento_env() -> Path:
    """The memento directory: env override, else local, else $HOME."""
    override = os.environ.get("MEMENTO_ENV")
    if override:
        return Path(override)
    local = Path(".memento")
    if local.is_dir():
        return local
    return Path.home() / ".memento"


if __name__ == "__main__":
    print(resolve_memento_env())
    sys.exit(0)
