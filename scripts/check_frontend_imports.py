#!/usr/bin/env python3
"""Frontend guard: every RELATIVE import in frontend/src must resolve to a file.

cloud-control's frontend is not built in this repo. It has no tsconfig, no
bundler and no test runner — it is consumed as a `file:` dependency by
qontinui-web, which compiles it inside the host app. That shape has a blind
spot this check exists to close:

* `@/...` imports are **host-resolved**. They are the established convention
  here and are deliberately NOT checked — `@/components/ui/button` resolves
  against the *consuming* app's tsconfig path alias, so it cannot be validated
  from inside this repo.
* **Relative** imports (`./x`, `../y`) resolve inside this repo and nowhere
  else. If one points at a file that does not exist, nothing in the composed
  build can fix it — the import is simply broken, and stays broken silently
  because no gate in either repo compiles this tree on its own.

That is not hypothetical. The carve-out that created this repo moved
`routes/organizations/[id]/members/page.tsx` across while leaving its
`_components/` and `_hooks/` behind in qontinui-web, and moved three service
modules across while leaving `http-client` / `api-config` behind — ten dangling
relative imports that no check anywhere would have reported.

Intentionally dependency-free (stdlib only), matching
`check_no_coord_import.py`. Run from the repo root:

    python3 scripts/check_frontend_imports.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = "frontend/src"

SKIP_DIR_PARTS = {"node_modules", "dist", "build", ".next", ".git"}

SCANNED_SUFFIXES = {".ts", ".tsx"}

# Suffixes/!index forms a TypeScript resolver will try for an extensionless
# specifier, in the order it tries them.
CANDIDATE_SUFFIXES = ("", ".ts", ".tsx", ".d.ts", ".js", ".jsx", ".json")
CANDIDATE_INDEXES = ("index.ts", "index.tsx", "index.js", "index.jsx")

# `from "./x"`, `import "./x"`, and dynamic `import("./x")`. Only relative
# specifiers are captured — a leading `.` is required by the pattern.
IMPORT_RE = re.compile(
    r"""(?:\bfrom|\bimport|\brequire)\s*\(?\s*["'](\.[^"']*)["']""",
)


def resolves(importer: Path, specifier: str) -> bool:
    """True if `specifier`, written inside `importer`, points at a real file."""
    target = (importer.parent / specifier).resolve()
    for suffix in CANDIDATE_SUFFIXES:
        candidate = target.with_name(target.name + suffix) if suffix else target
        if candidate.is_file():
            return True
    for index in CANDIDATE_INDEXES:
        if (target / index).is_file():
            return True
    return False


def iter_source_files(root: Path):
    base = root / ROOT_DIR
    if not base.exists():
        return
    for path in sorted(base.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        if SKIP_DIR_PARTS & set(path.parts):
            continue
        yield path


def find_violations(root: Path) -> list[str]:
    violations: list[str] = []
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in IMPORT_RE.finditer(text):
            specifier = match.group(1)
            if resolves(path, specifier):
                continue
            line_no = text.count("\n", 0, match.start()) + 1
            rel = path.relative_to(root).as_posix()
            violations.append(
                f"{rel}:{line_no}: unresolved relative import {specifier!r}"
            )
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = find_violations(root)

    if violations:
        print(
            "BROKEN IMPORT: a relative import in frontend/src does not resolve.",
            file=sys.stderr,
        )
        print(
            "Relative imports resolve inside THIS repo — the host app cannot supply them.\n"
            "Either add the missing module here, or import it from the host via '@/...'.\n",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print("OK: every relative import in frontend/src resolves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
