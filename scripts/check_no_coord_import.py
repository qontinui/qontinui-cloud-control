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

Two surfaces are scanned, because a coord dependency can be declared in either:

1. **Source files** under ``SOURCE_DIRS`` — an ``import``/``require`` statement.
2. **Dependency manifests** (``package.json``, ``pyproject.toml``) — the
   *path-dep* case named first in the paragraph above. Source scanning alone
   never covered it: a path-dep lives in a ``.json``/``.toml`` file, and those
   suffixes are not in ``SOURCE_SUFFIXES``. Manifests are parsed structurally
   (``json`` / ``tomllib``, both stdlib) rather than regexed, so a coord mention
   inside a *comment* or a prose ``description`` is not a false positive — only
   an actual declared dependency counts.
"""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

# Directories that hold first-party source we care about.
SOURCE_DIRS = ("backend", "frontend/src")

# Files to skip even under SOURCE_DIRS.
SKIP_DIR_PARTS = {
    "node_modules",
    "dist",
    "build",
    ".next",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

# Signatures that indicate importing coord *source* (not merely mentioning it).
#   - Python:  import qontinui_coord / from qontinui_coord import ...
#   - JS/TS:   from "...qontinui-coord..." / require("...qontinui-coord...") / "@qontinui/coord"
#   - path dep / relative import into a sibling coord checkout
PATTERNS = [
    re.compile(r"^\s*(?:from|import)\s+qontinui_coord(?:\b|\.)", re.MULTILINE),
    re.compile(
        r"""(?:from|require\()\s*['"][^'"]*qontinui-coord[^'"]*['"]""", re.MULTILINE
    ),
    re.compile(r"""['"]@qontinui/coord['"]"""),
    re.compile(r"""['"]\.\.?/(?:\.\./)*qontinui-coord/"""),
]


# Dependency manifests, relative to the repo root. A coord entry in any of these
# is a path-dep / package-dep violation regardless of whether source imports it.
MANIFEST_FILES = ("package.json", "pyproject.toml")

# A dependency name or specifier referring to coord in any of its spellings.
COORD_DEP = re.compile(r"(?:^|[^\w-])(?:@qontinui/coord|qontinui[-_]coord)(?:$|[^\w-])")


def _flatten(value) -> list[str]:
    """Yield every string in a nested dict/list, keys included."""
    out: list[str] = []
    if isinstance(value, dict):
        for k, v in value.items():
            out.append(str(k))
            out.extend(_flatten(v))
    elif isinstance(value, list):
        for v in value:
            out.extend(_flatten(v))
    elif isinstance(value, str):
        out.append(value)
    return out


def _dependency_strings(manifest: str, data: dict) -> list[str]:
    """Return the dependency-declaring strings of a parsed manifest.

    Deliberately narrow: only the sections that actually install code. Prose
    fields (``description``, ``comment``) are excluded so that *documenting* the
    coord boundary — as this repo's own manifests do — is never a violation.
    """
    sections: list = []
    if manifest == "package.json":
        for key in (
            "dependencies",
            "devDependencies",
            "peerDependencies",
            "optionalDependencies",
            "bundledDependencies",
        ):
            if key in data:
                sections.append(data[key])
    else:  # pyproject.toml
        project = data.get("project", {})
        sections.append(project.get("dependencies"))
        sections.append(project.get("optional-dependencies"))
        sections.append(data.get("dependency-groups"))
        sections.append(data.get("build-system", {}).get("requires"))
        poetry = data.get("tool", {}).get("poetry", {})
        sections.append(poetry.get("dependencies"))
        sections.append(poetry.get("dev-dependencies"))
        sections.append(poetry.get("group"))
    return [s for section in sections if section is not None for s in _flatten(section)]


def iter_manifest_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for name in MANIFEST_FILES:
        path = root / name
        if not path.exists():
            continue
        try:
            if name.endswith(".json"):
                data = json.loads(path.read_text(encoding="utf-8"))
            else:
                data = tomllib.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, OSError) as exc:
            violations.append(f"{name}: could not parse manifest ({exc})")
            continue
        if not isinstance(data, dict):
            continue
        for text in _dependency_strings(name, data):
            if COORD_DEP.search(text):
                violations.append(
                    f"{name}: declares a qontinui-coord dependency: {text!r}"
                )
    return violations


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


def find_violations(root: Path) -> list[str]:
    """Every coord-source-import and coord-dependency violation under `root`."""
    violations: list[str] = []
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in PATTERNS:
            for m in pat.finditer(text):
                line_no = text.count("\n", 0, m.start()) + 1
                rel = path.relative_to(root).as_posix()
                violations.append(f"{rel}:{line_no}: {m.group(0).strip()}")

    violations.extend(iter_manifest_violations(root))
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = find_violations(root)

    if violations:
        print(
            "BOUNDARY VIOLATION: cloud-control must not import qontinui-coord source.",
            file=sys.stderr,
        )
        print(
            "cloud-control is open (AGPL); coord is the closed coordination engine.",
            file=sys.stderr,
        )
        print(
            "Talk to coord over its network API instead of importing its source.\n",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("OK: no qontinui-coord source imports or dependency declarations found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
