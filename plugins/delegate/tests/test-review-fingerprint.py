#!/usr/bin/env python3
"""blob-pairs-v1: canonical text and sha256 from fixed tree entries (no git)."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_fingerprint

Z40, Z64 = '0' * 40, '0' * 64
VECTOR = {
    'a.txt': ('000000', Z40, '100644', '2' * 40),
    '中/x': ('100644', '3' * 40, '000000', Z40),
    'A.txt': ('100644', '1' * 40, '100755', '1' * 40),
}
VECTOR_TEXT = (b'delegate-blob-pairs-v1\n'
               b'A.txt\x00100644 ' + b'1' * 40 + b' 100755 ' + b'1' * 40 + b'\n'
               b'a.txt\x00000000 ' + Z40.encode() + b' 100644 ' + b'2' * 40 + b'\n'
               + '中/x'.encode() + b'\x00100644 ' + b'3' * 40 + b' 000000 ' + Z40.encode() + b'\n')
VECTOR_SHA256 = 'dede2917c99c45a202ac65140d7caa37dcec45ebabb49d0e8487a2be269181bc'
EMPTY_SHA256 = 'e1355a48d0e0e8601e999cc259e20ce7bc03b2392848915e770ee558e95df974'


class FingerprintTests(unittest.TestCase):
    def test_fixed_vector_canonical_text_and_sha256(self):
        self.assertEqual(review_fingerprint.canonical(VECTOR), VECTOR_TEXT)
        self.assertEqual(review_fingerprint.fingerprint(VECTOR), {
            'algorithm': 'blob-pairs-v1', 'sha256': VECTOR_SHA256, 'paths': ['A.txt', 'a.txt', '中/x']})
        self.assertEqual(review_fingerprint.ALGORITHM, 'blob-pairs-v1')

    def test_empty_set_is_the_header_only(self):
        self.assertEqual(review_fingerprint.canonical({}), b'delegate-blob-pairs-v1\n')
        self.assertEqual(review_fingerprint.fingerprint({}),
                         {'algorithm': 'blob-pairs-v1', 'sha256': EMPTY_SHA256, 'paths': []})

    def test_order_is_utf8_bytes_not_insertion_or_locale(self):
        entries = {name: ('100644', '1' * 40, '100644', '2' * 40) for name in ('b', 'é', 'B', 'a/b', 'a-b', '中')}
        expected = sorted(entries, key=lambda name: name.encode('utf-8'))
        self.assertEqual(review_fingerprint.fingerprint(entries)['paths'], expected)
        self.assertEqual(expected, ['B', 'a-b', 'a/b', 'b', 'é', '中'])

    def test_sha256_repository_ids_are_used_as_is(self):
        entries = {'f': ('000000', Z64, '100644', 'a' * 64)}
        self.assertEqual(review_fingerprint.canonical(entries),
                         b'delegate-blob-pairs-v1\nf\x00000000 ' + Z64.encode() + b' 100644 ' + b'a' * 64 + b'\n')


if __name__ == '__main__':
    unittest.main()
