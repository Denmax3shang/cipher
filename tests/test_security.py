import unittest

from cipher.skills.security import hash_identify, password_check, port_scan


class SecurityTests(unittest.TestCase):
    def test_md5(self):
        self.assertIn("MD5", hash_identify("5f4dcc3b5aa765d61d8327deb882cf99"))

    def test_sha256(self):
        self.assertEqual(hash_identify("a" * 64), "SHA-256")

    def test_common_password(self):
        self.assertIn("common", password_check("password"))

    def test_scope_blocks_unknown_host(self):
        self.assertIn("BLOCKED", port_scan("scope-test.invalid", "80"))


if __name__ == "__main__":
    unittest.main()
