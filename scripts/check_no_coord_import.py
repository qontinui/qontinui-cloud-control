#!/usr/bin/env python3
"""Boundary guard: cloud-control must not import the closed qontinui-coord source.

cloud-control is the OSS cloud extension to qontinui-web. The monetizable
concurrent-coordination layer lives in the closed `qontinui-coord` service and
must stay behind that wall. cloud-control may talk to coord over coord's network
API, but it must never import coord's *source* (a path-dep, a published coord
crate/package, or a relative `../qontinui-coord` import) — doing so would entangle
the open repo with the closed engine and re-introduce the leak risk the license
split exists to prevent.

This check scans the tracked source tree for coord-source-import signatures and
exits non-zero if any are found. It is intentionally dependency-free (stdlib only)
so it runs anywhere. Run from the repo root:

    python3 scripts/check_no_coord_import.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Directories that hold first-party source we care about.
SOURCE_DIRS = ("backend", "frontend/src")

# Files to skip even under SOURCE_DIRS.
SKIP_DIR_PARTS = {"node_modules", "dist", "build", ".next", "__pycache__", ".git", "venv", ".venv"}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

# Signatures that indicate importing coord *source* (not merely mentioning it).
#   - Python:  import qontinui_coord / from qontinui_coord import ...
#   - JS/TS:   from "...qontinui-coord..." / require("...qontinui-coord...") / "@qontinui/coord"
#   - path dep / relative import into a sibling coord checkout
PATTERNS = [
    re.compile(r"^\s*(?:from|import)\s+qontinui_coord(?:\b|\.)", re.MULTILINE),
    re.compile(r"""(?:from|require\()\s*['"][^'"]*qontinui-coord[^'"]*['"]""", re.MULTILINE),
    re.compile(r"""['"]@qontinui/coord['"]"""),
    re.compile(r"""['"]\.\.?/(?:\.\./)*qontinui-coord/"""),
]


def iter_source_files(root: Path):
    for base in SOURCE_DIRS:
        d = root / base
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if not p.is_file() or p.suffix not in SOURCE_SUFFIXES:
                continue
            if SKIP_DIR_PARTS & set(p.parts):
                continue
            yield p


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations: list[str] = []
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in PATTERNS:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                rel = path.relative_to(root)
                violations.append(f"{rel}:{line_no}: {m.group(0).strip()}")

    if violations:
        print("BOUNDARY VIOLATION: cloud-control must not import qontinui-coord source.", file=sys.stderr)
        print("cloud-control is open (AGPL); coord is the closed coordination engine.", file=sys.stderr)
        print("Talk to coord over its network API instead of importing its source.\n", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("OK: no qontinui-coord source imports found in cloud-control.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
