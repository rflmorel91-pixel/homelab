"""Collect deployment-check regressions in the existing backend CI suite."""
import importlib.util
from pathlib import Path
path = Path(__file__).resolve().parents[2] / 'scripts/tests/test_prestamodesk_release_check.py'
spec = importlib.util.spec_from_file_location('public_release_tests', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
ReleaseCheckTests = module.ReleaseCheckTests
