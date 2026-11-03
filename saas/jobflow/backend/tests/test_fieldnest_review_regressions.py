"""Focused regression checks; no live database is used by these test bodies."""
import ast
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import shutil
import subprocess

import unittest
from pydantic import ValidationError

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
SCHEMAS = BACKEND / "app/products/fieldnest/schemas.py"


def update_model():
    spec = importlib.util.spec_from_file_location("fieldnest_review_schemas", SCHEMAS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.WorkOrderUpdate


def call_handler(payload, row):
    # Execute the actual handler body, with only framework/DB dependencies replaced.
    tree = ast.parse((BACKEND / "app/products/fieldnest/api.py").read_text())
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "update_work_order")
    fn.decorator_list = []
    fn.args.defaults = []
    fn.returns = None
    for arg in fn.args.args:
        arg.annotation = None
    class Expr:
        def __eq__(self, other):
            return self
        def where(self, *args):
            return self
    db = Mock()
    db.scalar.return_value = row
    validate = Mock()
    namespace = {
        "select": lambda *args: Expr(),
        "FieldNestWorkOrder": SimpleNamespace(id=Expr(), tenant_id=Expr()),
        "_validate_update_links": validate,
    }
    module = ast.Module(body=[fn], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(BACKEND / "app/products/fieldnest/api.py"), "exec"), namespace)
    result = namespace["update_work_order"](1, payload, db, SimpleNamespace(id=7))
    validate.assert_called_once_with(db, 7, row, payload)
    db.commit.assert_called_once()
    return result


def existing_order():
    return SimpleNamespace(title="Leak", unit="3B", description="Keep description",
                           priority="high", status="completed", vendor_id=10,
                           resident_id=11, target_date="2026-11-10")


class FieldNestReviewRegressions(unittest.TestCase):
    def test_title_patch_preserves_all_other_fields(self):
        row = existing_order()
        before = vars(row).copy()
        call_handler(update_model()(title="New title"), row)
        assert vars(row) == {**before, "title": "New title"}


    def test_status_only_patch_preserves_assignment_and_details(self):
        row = existing_order()
        before = vars(row).copy()
        call_handler(update_model()(status="scheduled"), row)
        assert vars(row) == {**before, "status": "scheduled"}


    def test_explicit_null_clears_nullable_fields_only(self):
        row = existing_order()
        call_handler(update_model()(vendor_id=None, resident_id=None, description=None, target_date=None), row)
        assert row.vendor_id is row.resident_id is row.description is row.target_date is None
        assert (row.title, row.unit, row.priority, row.status) == ("Leak", "3B", "high", "completed")


    def test_null_required_fields_are_rejected(self):
        for field in ["title", "unit", "priority", "status"]:
            with self.subTest(field=field), self.assertRaises(ValidationError):
                update_model()(**{field: None})


    def test_workspace_switch_regressions(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node is required for the workspace race regression checks")
        subprocess.run([node, str(ROOT / "scripts/tests/test_fieldnest_workspace_races.cjs")], check=True)

if __name__ == "__main__":
    unittest.main()
