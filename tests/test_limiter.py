import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from cipher.core import limiter


class LimiterTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        p = patch("cipher.core.memory.DATA_DIR", Path(tmp.name))
        p.start()
        self.addCleanup(p.stop)
        limiter._recent.clear()

    def test_per_minute_limit(self):
        with patch("cipher.core.limiter.PER_MIN", 3):
            for i in range(3):
                limiter.check(now=1000.0 + i)
            with self.assertRaises(limiter.RateLimited):
                limiter.check(now=1003.0)
            limiter.check(now=1061.0)

    def test_daily_limit(self):
        with patch("cipher.core.limiter.PER_DAY", 2):
            limiter.check(now=1000.0)
            limiter.check(now=1100.0)
            with self.assertRaises(limiter.RateLimited):
                limiter.check(now=1200.0)

    def test_summary(self):
        limiter.check(now=time.time())
        self.assertIn("API calls today: 1/", limiter.summary())


if __name__ == "__main__":
    unittest.main()
