#!/usr/bin/env python3
"""Frontend guard: imports in frontend/src must be resolvable, not just plausible.

cloud-control's frontend is not built in this repo. It has no tsconfig, no
bundler and no test runner — it is consumed as a `file:` dependency by
qontinui-web, which compiles it inside the host app. That shape has a blind
spot this check exists to close, and it closes it along two axes:

1. **Relative imports must resolve here.** `./x` / `../y` resolve inside this
   repo and nowhere else. If one points at a file that does not exist, nothing
   in the composed build can fix it — the import is simply broken, and stays
   broken silently because no gate in either repo compiles this tree on its own.

2. **This package must never import itself by name.** A `@qontinui/cloud-control/…`
   specifier inside this package is always a defect, and a peculiarly invisible
   one: it *looks* host-resolved like `@/…`, but it is not. Node only supports
   self-reference by package name when the package declares an `exports` map,
   and this one deliberately does not (see package.json `//exports`). Absent
   that, the specifier resolves through `node_modules/@qontinui/cloud-control/…`
   — i.e. against the package ROOT, where `hooks/use-admin` does not exist
   because the real file is `frontend/src/hooks/use-admin.ts`. Intra-package
   imports must be relative.

`@/...` imports remain deliberately UNCHECKED: they are host-resolved against
the *consuming* app's tsconfig path alias (`@/*` → `./src/*`), so they cannot
be validated from inside this repo.

Neither rule is hypothetical. The carve-out that created this repo moved
`routes/organizations/[id]/members/page.tsx` across while leaving its
`_components/` and `_hooks/` behind in qontinui-web, and moved three service
modules across while leaving `http-client` / `api-config` behind — ten dangling
relative imports. It also left 19 self-referential `@qontinui/cloud-control/…`
imports across 8 live modules (the admin dashboard, the health section, the
pricing page, the org dialogs), none of which could ever have resolved.

Intentionally dependency-free (stdlib only), matching
`check_no_coord_import.py`. Run from the repo root:

    python3 scripts/check_frontend_imports.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT_DIR = "frontend/src"

# Fallback only. The real name is read from package.json so the two can never
# drift; this is what the check falls back to if package.json is unreadable.
PACKAGE_NAME_FALLBACK = "@qontinui/cloud-control"

SKIP_DIR_PARTS = {"node_modules", "dist", "build", ".next", ".git"}

SCANNED_SUFFIXES = {".ts", ".tsx"}

# Suffixes/!index forms a TypeScript resolver will try for an extensionless
# specifier, in the order it tries them.
CANDIDATE_SUFFIXES = ("", ".ts", ".tsx", ".d.ts", ".js", ".jsx", ".json")
CANDIDATE_INDEXES = ("index.ts", "index.tsx", "index.js", "index.jsx")

# `from "x"`, `import "x"`, and dynamic `import("x")`. Captures EVERY
# specifier, not just relative ones — `classify_specifier` below decides which
# rule each falls under.
IMPORT_RE = re.compile(
    r"""(?:\bfrom|\bimport|\brequire)\s*\(?\s*["']([^"']+)["']""",
)


def read_package_name(root: Path) -> str:
    """This package's own name, per package.json."""
    try:
        data = json.loads((root / "package.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return PACKAGE_NAME_FALLBACK
    name = data.get("name")
    return name if isinstance(name, str) and name else PACKAGE_NAME_FALLBACK


def is_self_reference(specifier: str, package_name: str) -> bool:
    """True if `specifier` imports this package by its own name.

    Matches the bare name and any subpath of it, but not a different package
    that merely shares the prefix (`@qontinui/cloud-control-extras`).
    """
    return specifier == package_name or specifier.startswith(package_name + "/")


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
    package_name = read_package_name(root)
    violations: list[str] = []
    for path in iter_source_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for match in IMPORT_RE.finditer(text):
            specifier = match.group(1)
            rel = path.relative_to(root).as_posix()
            line_no = text.count("\n", 0, match.start()) + 1

            if is_self_reference(specifier, package_name):
                violations.append(
                    f"{rel}:{line_no}: self-referential import {specifier!r} "
                    f"— {package_name} declares no 'exports' map, so importing "
                    f"itself by name cannot resolve; use a relative path"
                )
                continue

            # Everything non-relative that is not a self-reference is either a
            # host `@/...` alias or a third-party package: host-resolved, and
            # unverifiable from inside this repo by construction.
            if not specifier.startswith("."):
                continue

            if not resolves(path, specifier):
                violations.append(
                    f"{rel}:{line_no}: unresolved relative import {specifier!r}"
                )
    return violations


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    violations = find_violations(root)

    if violations:
        print(
            "BROKEN IMPORT: an import in frontend/src cannot resolve.",
            file=sys.stderr,
        )
        print(
            "Relative imports resolve inside THIS repo — the host app cannot supply them.\n"
            "Either add the missing module here, or import it from the host via '@/...'.\n"
            "An import of this package's OWN name never resolves either; make it relative.\n",
            file=sys.stderr,
        )
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print(
        "OK: every relative import in frontend/src resolves, "
        "and nothing imports this package by its own name."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
