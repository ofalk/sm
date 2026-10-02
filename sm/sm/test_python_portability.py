"""Regression guards for Python-version-portability defects.

The defect these guard: `sm/sm/models.py` carried a self-referential return
annotation, `-> tuple[ApiKey, str]`, inside `class ApiKey`.  Resolving that
annotation needs PEP 649 lazy evaluation, which only became the default in
Python 3.14.  On 3.13 the name `ApiKey` is not yet bound while the class body
is executing, so importing the module raises

    NameError: name 'ApiKey' is not defined

during *app-registry population* -- meaning every single test in the project
errors out before it runs.  These tests assert the real behaviour that prevents
a recurrence, so the guard stays meaningful on whichever interpreter runs CI.
"""

import ast
import importlib
import pathlib

from django.test import SimpleTestCase

MODELS_PY = pathlib.Path(__file__).resolve().parent / "models.py"


class ModelsModuleIsPortableTest(SimpleTestCase):
    """sm.sm.models must not rely on PEP 649 lazy annotation evaluation."""

    def test_models_module_has_future_annotations_import(self):
        tree = ast.parse(MODELS_PY.read_text(encoding="utf-8"))
        imports_future = any(
            isinstance(node, ast.ImportFrom)
            and node.module == "__future__"
            and any(alias.name == "annotations" for alias in node.names)
            for node in tree.body
        )
        self.assertTrue(
            imports_future,
            "sm/sm/models.py must import `from __future__ import annotations`; "
            "without it the self-referential `-> tuple[ApiKey, str]` annotation "
            "on ApiKey.create_for_user / ApiKey.rotate raises NameError on "
            "Python < 3.14 (PEP 649 is only default-on from 3.14).",
        )

    def test_apikey_self_referential_annotations_stay_unresolved(self):
        """The annotations must remain lazy strings, not eagerly-built aliases.

        Under `from __future__ import annotations` these are plain `str`
        objects that nothing ever resolves, which is exactly what lets Python
        3.13 import the module at all.  Drop the future import and CPython
        builds a real `types.GenericAlias` here on 3.12+, which brings the
        NameError back on 3.13.
        """
        models = importlib.import_module("sm.models")

        for name in ("create_for_user", "rotate"):
            with self.subTest(method=f"ApiKey.{name}"):
                self.assertTrue(
                    callable(getattr(models.ApiKey, name, None)),
                    f"ApiKey.{name} no longer exists; update the portability guard",
                )
                annotation = getattr(models.ApiKey, name).__annotations__["return"]
                self.assertIsInstance(
                    annotation,
                    str,
                    f"ApiKey.{name} return annotation was resolved eagerly as "
                    f"{annotation!r}; that is what breaks Python < 3.14.",
                )
                self.assertIn(
                    "ApiKey",
                    annotation,
                    f"ApiKey.{name} should keep its self-reference in the "
                    f"annotation, got {annotation!r}",
                )