import unittest
from unittest.mock import patch

from cipher.core import recon_pipeline


class PipelineTests(unittest.TestCase):
    def test_rejects_bad_domain(self):
        self.assertIn("valid domain", recon_pipeline.run("not a domain"))

    @patch("cipher.core.recon_pipeline.ssl_check", return_value="BLOCKED: not in scope")
    @patch("cipher.skills.security.port_scan", return_value="BLOCKED: not in scope")
    @patch("cipher.core.recon_pipeline.subdomain_lookup", return_value="www.example.com")
    @patch("cipher.core.recon_pipeline.whois_lookup", return_value="Registrar: Example Inc")
    def test_builds_full_report(self, whois, subs, scan, ssl):
        out = recon_pipeline.run("example.com")
        self.assertIn("Recon dossier for example.com", out)
        self.assertIn("Registrar: Example Inc", out)
        self.assertIn("www.example.com", out)
        self.assertIn("BLOCKED", out)


if __name__ == "__main__":
    unittest.main()
