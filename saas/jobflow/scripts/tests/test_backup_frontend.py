import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import MagicMock, patch

spec = importlib.util.spec_from_file_location('frontend_backup', Path(__file__).resolve().parents[1] / 'backup-jobflow-frontend.py')
backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backup)


class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.app = self.root / 'app'
        self.app.mkdir()
        (self.app / 'fieldnest-workspace.html').write_text('<script src="/assets/test.js"></script>')
        (self.app / 'assets').mkdir()
        (self.app / 'assets/test.js').write_text('/* public frontend */')

    def test_archive_deterministic_and_manifest_matches(self):
        data, hashes = backup.build_archive(self.app)
        self.assertEqual(data, backup.build_archive(self.app)[0])
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            manifest = json.load(archive.extractfile('frontend/manifest.json'))
            self.assertEqual(manifest['files'], hashes)
            self.assertEqual(len(archive.getmembers()), 3)
            self.assertTrue(all(m.isfile() for m in archive))

    def test_symlinks_rejected(self):
        (self.app / 'linked').symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            backup.build_archive(self.app)

    def test_private_files_rejected(self):
        for name in ['.env', 'server.key', 'identity.pem']:
            path = self.app / name
            path.write_text('NEVER_UPLOAD')
            with self.assertRaisesRegex(ValueError, 'private-file'):
                backup.build_archive(self.app)
            path.unlink()

    def test_snapshot_size_bounded(self):
        with patch.object(backup, 'MAX_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'size-limit'):
                backup.build_archive(self.app)

    def test_changed_snapshot_rejected(self):
        with patch.object(backup, 'inventory', side_effect=[{'fieldnest-workspace.html': b'a'}, {'fieldnest-workspace.html': b'b'}]):
            with self.assertRaisesRegex(ValueError, 'changed'):
                backup.build_archive(self.app)

    def helper(self):
        helper = MagicMock()
        helper.PREFIX = 'platform/'
        helper.encrypted_copy.side_effect = lambda path, *args: (b'age-ciphertext', backup.hashlib.sha256(path.read_bytes()).hexdigest())
        helper.B2.return_value.ensure_copy.return_value = {'name': 'verified-object'}
        return helper

    def test_success_separate_receipts_retention_and_ciphertext(self):
        helper = self.helper()
        with patch.object(backup, 'mounted_frontend', return_value=self.app):
            result = backup.run_backup(self.root, self.root, 'web', helper, 1794657600)
        self.assertEqual(result['files'], 2)
        args = helper.B2.return_value.ensure_copy.call_args.args
        self.assertTrue(args[0].startswith('platform/frontend/daily/'))
        self.assertEqual(args[1], b'age-ciphertext')
        self.assertGreaterEqual(args[2], (1794657600 + 35 * 86400) * 1000)
        markers = [str(call.args[0]) for call in helper.atomic_json.call_args_list]
        self.assertTrue(all('frontend-offsite-' in marker for marker in markers))
        self.assertEqual(len(markers), 2)

    def test_remote_failure_never_records_success(self):
        helper = self.helper()
        helper.B2.return_value.ensure_copy.side_effect = ValueError('remote-bytes')
        with patch.object(backup, 'mounted_frontend', return_value=self.app):
            with self.assertRaisesRegex(ValueError, 'remote-bytes'):
                backup.run_backup(self.root, self.root, 'web', helper, 1794657600)
        helper.atomic_json.assert_not_called()

    def test_mount_change_prevents_upload(self):
        helper = self.helper()
        with patch.object(backup, 'mounted_frontend', side_effect=[self.app, self.root]):
            with self.assertRaisesRegex(ValueError, 'mount-changed'):
                backup.run_backup(self.root, self.root, 'web', helper, 1794657600)
        helper.B2.assert_not_called()

    def test_requires_readonly_bind(self):
        for rw in [True, False]:
            payload = [{'Mounts': [{'Destination': '/usr/share/nginx/html', 'Type': 'bind', 'Source': str(self.app), 'RW': rw}]}]
            with patch.object(backup.subprocess, 'run', return_value=MagicMock(stdout=json.dumps(payload))):
                if rw:
                    with self.assertRaisesRegex(ValueError, 'readonly-bind'):
                        backup.mounted_frontend('web')
                else:
                    self.assertEqual(backup.mounted_frontend('web'), self.app)


if __name__ == '__main__':
    unittest.main()
