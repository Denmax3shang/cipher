import time
import unittest
from unittest.mock import patch

from cipher.core import approvals


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        approvals._pending.clear()
        approvals._new.clear()

    def test_create_and_drain(self):
        aid = approvals.create("security", "port_scan", {"host": "x"}, 123)
        self.assertEqual(approvals.drain(), [aid])
        self.assertEqual(approvals.drain(), [])

    def test_take_removes_entry(self):
        aid = approvals.create("security", "crack_hash", {"hash": "abc"}, 123)
        got = approvals.take(aid)
        self.assertEqual(got["tool"], "crack_hash")
        self.assertIsNone(approvals.take(aid))

    def test_get_is_nondestructive(self):
        aid = approvals.create("security", "port_scan", {"host": "x"}, 1)
        approvals.get(aid)
        self.assertIsNotNone(approvals.take(aid))

    def test_expired_entries_purged(self):
        with patch("cipher.core.approvals.TTL", 0):
            aid = approvals.create("security", "port_scan", {}, 1)
            time.sleep(0.01)
            approvals.create("security", "port_scan", {}, 1)  # triggers a purge
            self.assertIsNone(approvals.take(aid))


if __name__ == "__main__":
    unittest.main()
