import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "create-jobflow-backup.py"
spec = importlib.util.spec_from_file_location("backup_storage_uuid", SCRIPT)
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)

UUID = "1a0d3faf-731d-4b09-808e-5c24d10ab165"


class StorageIdentityTests(unittest.TestCase):
    def capture(self, configured_uuid, actual_uuid=UUID,
                device="/dev/vdb", source=None):
        calls = []
        source = source or backup.PRIVATE_STORAGE_HOST_PATH

        def run(argv, **kwargs):
            calls.append(argv)
            if argv[:2] == ["docker", "inspect"]:
                output = json.dumps([{
                    "Type": "bind",
                    "Source": source,
                    "Destination": backup.PRIVATE_STORAGE_PATH,
                }])
            elif argv[0] == "findmnt":
                output = device if argv[3] == "SOURCE" else actual_uuid
            elif argv[:2] == ["docker", "run"]:
                kwargs["stdout"].write(b"archive")
                output = ""
            else:
                raise AssertionError(argv)
            return subprocess.CompletedProcess(argv, 0, stdout=output)

        env = {} if configured_uuid is None else {
            "JOBFLOW_PRIVATE_STORAGE_UUID": configured_uuid
        }
        with tempfile.TemporaryDirectory() as folder:
            with patch.dict(os.environ, env, clear=True):
                with patch.object(backup.subprocess, "run", side_effect=run):
                    with patch.object(backup, "validate_private_archive"):
                        backup.create_private_archive(
                            Path(folder) / "documents.tar", [], "test-image"
                        )
        return calls

    def test_matching_cloud_uuid_uses_readonly_bind(self):
        calls = self.capture(UUID)
        command = next(c for c in calls if c[:2] == ["docker", "run"])
        mount = command[command.index("--mount") + 1]
        self.assertEqual(
            mount,
            "type=bind,source=" + backup.PRIVATE_STORAGE_HOST_PATH
            + ",target=/data,readonly",
        )

    def test_wrong_or_missing_uuid_is_rejected_before_archiving(self):
        for actual in ("", "00000000-0000-0000-0000-000000000000"):
            with self.subTest(actual=actual):
                with self.assertRaisesRegex(
                    ValueError, "^private-bind-storage-uuid$"
                ):
                    self.capture(UUID, actual_uuid=actual)

    def test_malformed_configuration_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError, "^private-bind-uuid-format$"
        ):
            self.capture("not-a-uuid")

    def test_default_preserves_homelab_device_check(self):
        self.capture(None, device=backup.PRIVATE_STORAGE_BACKING_DEVICE)
        with self.assertRaisesRegex(ValueError, "^private-bind-storage$"):
            self.capture(None, device="/dev/vdb")

    def test_matching_uuid_does_not_allow_another_source_path(self):
        with self.assertRaisesRegex(ValueError, "^private-bind-source$"):
            self.capture(UUID, source="/srv/unapproved")


if __name__ == "__main__":
    unittest.main()
