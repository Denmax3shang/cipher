import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from cipher.core import briefing, memory


class BriefingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = patch("cipher.core.memory.DATA_DIR", Path(tmp.name))
        p.start()
        self.addCleanup(p.stop)

    def test_build_sections(self):
        memory.save_json("notes.json", ["buy milk"])
        out = briefing.build()
        self.assertIn("buy milk", out)
        self.assertIn("Tip:", out)
        self.assertIn("Last 24h", out)

    def test_commands(self):
        self.assertIn("07:30", briefing.handle(["on"]))
        self.assertTrue(briefing.load()["on"])
        self.assertIn("07:45", briefing.handle(["time", "7:45"]))
        self.assertIn("24-hour", briefing.handle(["time", "99:99"]))
        briefing.handle(["city", "New", "York"])
        self.assertEqual(briefing.load()["city"], "New York")

    def test_due_logic(self):
        briefing.handle(["on"])
        briefing.handle(["time", "07:30"])
        self.assertFalse(briefing.due(datetime(2026, 11, 22, 7, 0)))
        self.assertTrue(briefing.due(datetime(2026, 11, 22, 8, 0)))
        self.assertFalse(briefing.due(datetime(2026, 11, 22, 12, 0)))
        briefing.mark_sent(datetime(2026, 11, 22, 8, 0))
        self.assertFalse(briefing.due(datetime(2026, 11, 22, 8, 5)))


if __name__ == "__main__":
    unittest.main()
