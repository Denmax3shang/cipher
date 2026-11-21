import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cipher.core import audit, memory
from cipher.core.report import make_export


class TempData(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = patch("cipher.core.memory.DATA_DIR", Path(tmp.name))
        p.start()
        self.addCleanup(p.stop)


class AuditTests(TempData):
    def test_redacts_unsafe_args(self):
        audit.record("security", "password_check", {"password": "hunter2"}, "ok")
        raw = (memory.DATA_DIR / "audit.log").read_text()
        self.assertNotIn("hunter2", raw)
        self.assertIn("<redacted>", raw)

    def test_blocked_status(self):
        audit.record("security", "port_scan", {"host": "x.invalid"}, "BLOCKED: no")
        self.assertIn("🚫", audit.tail(1))
        self.assertEqual(audit.count(), 1)


class ExportTests(TempData):
    def test_export_contains_notes(self):
        memory.save_json("notes.json", ["buy milk"])
        self.assertIn("buy milk", make_export().read_text())


if __name__ == "__main__":
    unittest.main()
