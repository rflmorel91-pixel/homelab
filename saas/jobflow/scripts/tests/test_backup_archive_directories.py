import hashlib
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]

def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / name
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

snapshot = load("create-jobflow-backup.py")
restore = load("validate-jobflow-backup.py")

KEY = "2/1/11111111-1111-4111-8111-111111111111.png"
PAYLOAD = b"synthetic document"
RECORD = {
    "file_key": KEY,
    "byte_size": len(PAYLOAD),
    "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
}

class ArchiveDirectoryTests(unittest.TestCase):
    def check_archive(self, entries, records, accepted):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "documents.tar"
            with tarfile.open(path, "w") as archive:
                for name, kind, payload in entries:
                    info = tarfile.TarInfo(name)
                    info.type = kind
                    if kind == tarfile.REGTYPE:
                        info.size = len(payload)
                        archive.addfile(info, io.BytesIO(payload))
                    else:
                        if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE):
                            info.linkname = KEY
                        archive.addfile(info)
            metadata = {
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "documents": records,
            }
            def validate_restore():
                with path.open("rb") as stream:
                    restore.validate_private_archive(stream, metadata)
            for name, validate in (
                ("capture", lambda: snapshot.validate_private_archive(path, records)),
                ("restore", validate_restore),
            ):
                with self.subTest(validator=name):
                    if accepted:
                        validate()
                    else:
                        with self.assertRaises(ValueError):
                            validate()

    def test_unrelated_empty_directories_with_and_without_documents(self):
        directories = [
            (name, tarfile.DIRTYPE, b"")
            for name in (".", "./2", "./2/1", "./999999", "./999999/999999")
        ]
        self.check_archive(directories, [], True)
        self.check_archive(
            directories + [(KEY, tarfile.REGTYPE, PAYLOAD)], [RECORD], True
        )

    def test_unsafe_directory_paths_are_rejected(self):
        for name in ("/escape", "../escape", "./../escape", "2/../escape"):
            with self.subTest(path=name):
                self.check_archive([(name, tarfile.DIRTYPE, b"")], [], False)

    def test_unexpected_files_and_links_are_rejected(self):
        for kind in (tarfile.REGTYPE, tarfile.SYMTYPE, tarfile.LNKTYPE):
            with self.subTest(kind=kind):
                self.check_archive(
                    [("999999/unexpected", kind, b"x")], [], False
                )

    def test_missing_duplicate_and_corrupt_documents_are_rejected(self):
        entry = (KEY, tarfile.REGTYPE, PAYLOAD)
        self.check_archive([], [RECORD], False)
        self.check_archive([entry, entry], [RECORD], False)
        self.check_archive(
            [(KEY, tarfile.REGTYPE, b"x" * len(PAYLOAD))], [RECORD], False
        )
        self.check_archive(
            [(KEY, tarfile.REGTYPE, b"x")], [RECORD], False
        )

if __name__ == "__main__":
    unittest.main()
