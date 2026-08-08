#!/usr/bin/env python3
"""Self-tests for this repo's CI gate scripts.

Two controls, mirroring the standard the CI manifest set for itself: each
checker must pass a known-good fixture AND trip on a deliberately-broken one.
A gate nobody has watched fail is not evidence of anything.

stdlib only (`unittest`, `tempfile`), so it runs on both CI lanes with no
install step. Run from the repo root:

    python3 -m unittest discover -s scripts -p 'test_*.py' -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_frontend_imports  # noqa: E402
import check_no_coord_import  # noqa: E402


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class CoordBoundaryTests(unittest.TestCase):
    """`check_no_coord_import.find_violations`."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_clean_tree_has_no_violations(self) -> None:
        write(self.root, "backend/pkg/service.py", "from app.models import User\n")
        write(self.root, "frontend/src/a.ts", 'import { x } from "@qontinui/web";\n')
        self.assertEqual(check_no_coord_import.find_violations(self.root), [])

    def test_python_source_import_is_caught(self) -> None:
        write(self.root, "backend/pkg/x.py", "from qontinui_coord.db import pool\n")
        self.assertEqual(len(check_no_coord_import.find_violations(self.root)), 1)

    def test_typescript_source_import_is_caught(self) -> None:
        write(self.root, "frontend/src/x.ts", 'import c from "@qontinui/coord";\n')
        self.assertTrue(check_no_coord_import.find_violations(self.root))

    # --- the manifest cases: the gap this file's companion change closed -----

    def test_package_json_path_dep_is_caught(self) -> None:
        write(
            self.root,
            "package.json",
            '{"dependencies": {"@qontinui/coord": "file:../qontinui-coord"}}',
        )
        violations = check_no_coord_import.find_violations(self.root)
        self.assertTrue(violations, "a package.json coord path-dep must be a violation")
        self.assertIn("package.json", violations[0])

    def test_pyproject_path_dep_is_caught(self) -> None:
        write(
            self.root,
            "pyproject.toml",
            '[project]\nname = "x"\n'
            'dependencies = ["qontinui-coord @ file:///../qontinui-coord"]\n',
        )
        self.assertTrue(check_no_coord_import.find_violations(self.root))

    def test_poetry_path_dep_is_caught(self) -> None:
        write(
            self.root,
            "pyproject.toml",
            "[tool.poetry.dependencies]\n"
            'qontinui-coord = { path = "../qontinui-coord" }\n',
        )
        self.assertTrue(check_no_coord_import.find_violations(self.root))

    def test_peer_dependency_is_caught(self) -> None:
        write(
            self.root,
            "package.json",
            '{"peerDependencies": {"@qontinui/coord": "*"}}',
        )
        self.assertTrue(check_no_coord_import.find_violations(self.root))

    def test_prose_mentioning_coord_is_not_a_violation(self) -> None:
        """Documenting the boundary must not trip the guard that enforces it."""
        write(
            self.root,
            "package.json",
            '{"description": "must never import qontinui-coord source",'
            ' "dependencies": {"@stripe/stripe-js": "^4"}}',
        )
        write(
            self.root,
            "pyproject.toml",
            "# we deliberately do not depend on qontinui-coord\n"
            '[project]\nname = "x"\ndependencies = ["stripe>=8"]\n',
        )
        self.assertEqual(check_no_coord_import.find_violations(self.root), [])

    def test_unparseable_manifest_is_reported(self) -> None:
        write(self.root, "package.json", "{ not json")
        self.assertTrue(check_no_coord_import.find_violations(self.root))


class FrontendImportTests(unittest.TestCase):
    """`check_frontend_imports.find_violations`."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_resolving_relative_import_is_clean(self) -> None:
        write(self.root, "frontend/src/services/http.ts", "export const x = 1;\n")
        write(
            self.root,
            "frontend/src/services/billing.ts",
            'import { x } from "./http";\n',
        )
        self.assertEqual(check_frontend_imports.find_violations(self.root), [])

    def test_dangling_relative_import_is_caught(self) -> None:
        write(
            self.root,
            "frontend/src/services/billing.ts",
            'import { HttpClient } from "./http-client";\n',
        )
        violations = check_frontend_imports.find_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("http-client", violations[0])

    def test_host_resolved_alias_import_is_ignored(self) -> None:
        """`@/...` is the host app's alias — unresolvable here BY DESIGN.

        Third-party specifiers are equally out of scope: they resolve from the
        host app's node_modules, which this repo does not have. (This case
        deliberately no longer uses `@qontinui/web/...` as its example: no
        package by that name exists, and holding it up as a *valid* host import
        is what let `index.ts` import a specifier that could never resolve.)
        """
        write(
            self.root,
            "frontend/src/x.tsx",
            'import { Button } from "@/components/ui/button";\n'
            'import { toast } from "sonner";\n',
        )
        self.assertEqual(check_frontend_imports.find_violations(self.root), [])

    def test_directory_index_import_resolves(self) -> None:
        write(self.root, "frontend/src/health/index.ts", "export const h = 1;\n")
        write(self.root, "frontend/src/a.ts", 'import { h } from "./health";\n')
        self.assertEqual(check_frontend_imports.find_violations(self.root), [])

    def test_parent_relative_import_is_checked(self) -> None:
        write(
            self.root,
            "frontend/src/services/admin/health.ts",
            'import { ApiConfig } from "../api-config";\n',
        )
        self.assertEqual(len(check_frontend_imports.find_violations(self.root)), 1)

    def test_dynamic_import_is_checked(self) -> None:
        write(
            self.root,
            "frontend/src/a.ts",
            'const p = import("./does-not-exist");\n',
        )
        self.assertEqual(len(check_frontend_imports.find_violations(self.root)), 1)

    # --- the self-reference cases: the gap this file's companion change closed -

    def test_self_referential_subpath_import_is_caught(self) -> None:
        """The carve-out's second defect class: importing this package by name.

        Looks host-resolved like `@/...`, but is not — without an `exports`
        map it resolves against the package ROOT, where `hooks/use-admin`
        does not exist (the file is `frontend/src/hooks/use-admin.ts`).
        """
        write(self.root, "package.json", '{"name": "@qontinui/cloud-control"}')
        write(self.root, "frontend/src/hooks/use-admin.ts", "export const u = 1;\n")
        write(
            self.root,
            "frontend/src/routes/admin/page.tsx",
            'import { u } from "@qontinui/cloud-control/hooks/use-admin";\n',
        )
        violations = check_frontend_imports.find_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("self-referential", violations[0])

    def test_self_referential_bare_import_is_caught(self) -> None:
        write(self.root, "package.json", '{"name": "@qontinui/cloud-control"}')
        write(
            self.root,
            "frontend/src/a.ts",
            'import "@qontinui/cloud-control";\n',
        )
        self.assertEqual(len(check_frontend_imports.find_violations(self.root)), 1)

    def test_relative_rewrite_of_a_self_reference_is_clean(self) -> None:
        """The prescribed fix must actually pass the gate."""
        write(self.root, "package.json", '{"name": "@qontinui/cloud-control"}')
        write(self.root, "frontend/src/hooks/use-admin.ts", "export const u = 1;\n")
        write(
            self.root,
            "frontend/src/routes/admin/page.tsx",
            'import { u } from "../../hooks/use-admin";\n',
        )
        self.assertEqual(check_frontend_imports.find_violations(self.root), [])

    def test_package_sharing_a_name_prefix_is_not_a_self_reference(self) -> None:
        """`@qontinui/cloud-control-extras` is a different package."""
        write(self.root, "package.json", '{"name": "@qontinui/cloud-control"}')
        write(
            self.root,
            "frontend/src/a.ts",
            'import { z } from "@qontinui/cloud-control-extras/thing";\n',
        )
        self.assertEqual(check_frontend_imports.find_violations(self.root), [])

    def test_package_name_is_read_from_package_json(self) -> None:
        """The rule follows package.json, so the two can never drift."""
        write(self.root, "package.json", '{"name": "@acme/renamed"}')
        write(self.root, "frontend/src/a.ts", 'import "@acme/renamed/sub";\n')
        violations = check_frontend_imports.find_violations(self.root)
        self.assertEqual(len(violations), 1)
        self.assertIn("@acme/renamed", violations[0])

    def test_missing_package_json_falls_back_to_the_known_name(self) -> None:
        write(
            self.root,
            "frontend/src/a.ts",
            'import "@qontinui/cloud-control/services/billing-service";\n',
        )
        self.assertEqual(len(check_frontend_imports.find_violations(self.root)), 1)

    def test_this_repo_passes_its_own_gate(self) -> None:
        """The live tree, not a fixture — the assertion package.json now makes."""
        repo_root = Path(__file__).resolve().parent.parent
        self.assertEqual(check_frontend_imports.find_violations(repo_root), [])


if __name__ == "__main__":
    unittest.main()
