import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cipher.skills import crack


class CrackTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        (self.dir / "test.txt").write_text("foo\nbar\nbaz\n")
        p = patch("cipher.skills.crack.WORDLIST_DIR", self.dir)
        p.start()
        self.addCleanup(p.stop)

    def test_cracks_known_word(self):
        h = hashlib.md5(b"bar").hexdigest()
        out = crack.crack_hash(h, "md5", "test.txt")
        self.assertIn("Cracked", out)
        self.assertIn("bar", out)

    def test_not_found(self):
        h = hashlib.md5(b"nope-not-in-list").hexdigest()
        self.assertIn("Not found", crack.crack_hash(h, "md5", "test.txt"))

    def test_bad_length_rejected(self):
        self.assertIn("doesn't look like", crack.crack_hash("abc123", "sha256", "test.txt"))

    def test_path_traversal_blocked(self):
        self.assertIn("not found", crack.crack_hash("a" * 32, "md5", "../../etc/passwd").lower())


if __name__ == "__main__":
    unittest.main()
