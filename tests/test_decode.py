import base64
import json
import unittest

from cipher.skills.decode import auto_decode, caesar_brute, encode_decode, jwt_decode


def _token(header, payload):
    def enc(d):
        return base64.urlsafe_b64encode(json.dumps(d).encode()).rstrip(b"=").decode()
    return f"{enc(header)}.{enc(payload)}."


class DecodeTests(unittest.TestCase):
    def test_base64_round_trip(self):
        self.assertEqual(encode_decode("Hello", "base64", "encode"), "SGVsbG8=")
        self.assertEqual(encode_decode("SGVsbG8=", "base64"), "Hello")

    def test_hex_and_binary(self):
        self.assertEqual(encode_decode("48656c6c6f", "hex"), "Hello")
        self.assertEqual(encode_decode("01001000 01101001", "binary"), "Hi")

    def test_auto_decode_finds_base64(self):
        self.assertIn("Hack the planet", auto_decode("SGFjayB0aGUgcGxhbmV0"))

    def test_auto_decode_ignores_plain_text(self):
        self.assertNotIn("rot13", auto_decode("hello world"))

    def test_caesar_brute(self):
        self.assertIn("This is a test", caesar_brute("Wklv lv d whvw"))

    def test_jwt_flags_unsigned_and_no_exp(self):
        out = jwt_decode(_token({"alg": "none"}, {"sub": "1"}))
        self.assertIn("unsigned", out)
        self.assertIn("never expires", out)

    def test_jwt_rejects_garbage(self):
        self.assertIn("Not a JWT", jwt_decode("hello"))


if __name__ == "__main__":
    unittest.main()
