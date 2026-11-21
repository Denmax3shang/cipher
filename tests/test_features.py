import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cipher.core import scheduler
from cipher.core.memory import add_scope, in_scope, load_json, save_json
from cipher.skills.cve import _score
from cipher.skills.recon import ssl_check, subdomain_lookup, whois_lookup
from cipher.skills.security import hash_text
from cipher.telegram_bot import plain


class TempData(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = patch("cipher.core.memory.DATA_DIR", Path(tmp.name))
        p.start()
        self.addCleanup(p.stop)


class SchedulerTests(TempData):
    def test_add_list_cancel(self):
        post = scheduler.add_post("hello", "2999-01-01 10:00")
        self.assertEqual(len(scheduler.list_posts()), 1)
        self.assertTrue(scheduler.cancel_post(post["id"]))
        self.assertEqual(scheduler.list_posts(), [])

    def test_past_time_rejected(self):
        with self.assertRaises(ValueError):
            scheduler.add_post("late", "2000-01-01 10:00")

    def test_due_and_mark_sent(self):
        save_json("posts.json", [{"id": "ab12", "text": "x",
                                  "when": "2000-01-01 00:00", "sent": False}])
        self.assertEqual(len(scheduler.due_posts()), 1)
        scheduler.mark_sent("ab12")
        self.assertEqual(scheduler.due_posts(), [])


class ScopeTests(TempData):
    def test_scope_guard(self):
        self.assertTrue(in_scope("localhost"))
        self.assertFalse(in_scope("example.org"))
        add_scope("example.org")
        self.assertTrue(in_scope("example.org"))

    def test_ssl_check_blocked_out_of_scope(self):
        self.assertIn("BLOCKED", ssl_check("not-in-scope.invalid"))

    def test_json_default(self):
        self.assertEqual(load_json("missing.json", [1]), [1])


class ReconTests(unittest.TestCase):
    def test_invalid_domain_rejected(self):
        self.assertIn("valid domain", whois_lookup("not a domain"))
        self.assertIn("valid domain", subdomain_lookup("???"))


class HelperTests(unittest.TestCase):
    def test_cvss_score(self):
        cve = {"metrics": {"cvssMetricV31": [
            {"cvssData": {"baseScore": 9.8, "baseSeverity": "CRITICAL"}}]}}
        self.assertEqual(_score(cve), (9.8, "CRITICAL"))
        self.assertEqual(_score({}), (0.0, "N/A"))

    def test_hash_text(self):
        self.assertEqual(hash_text("password", "md5"),
                         "5f4dcc3b5aa765d61d8327deb882cf99")

    def test_plain_strips_markdown(self):
        out = plain("### Title\n**bold**\n| a | b |\n|---|---|\n| 1 | 2 |")
        self.assertIn("Title", out)
        self.assertIn("- a - b", out)
        self.assertNotIn("|", out)
        self.assertNotIn("**", out)


if __name__ == "__main__":
    unittest.main()
