#!/usr/bin/env python3
"""Explicit system trust export for the sandboxed Claude CLI, with a fake security."""
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import review_trust

FAKE = '''#!/usr/bin/env python3
import json, os, sys, time
from pathlib import Path
fixture = json.loads(Path(os.environ['FIXTURE_TRUST']).read_text())
args = sys.argv[1:]
mode = fixture.get('mode', 'normal')
if mode == 'hang':
    time.sleep(30)
if mode == 'fail':
    print('PRIVATE_SECURITY_OUTPUT', file=sys.stderr); sys.exit(1)
if args[0] == 'trust-settings-export':
    domain = 'admin' if args[1] == '-d' else 'user'
    Path(args[-1]).write_bytes(bytes.fromhex(fixture[domain]))
    print('...Trust Settings exported successfully.')
elif args[:4] == ['find-certificate', '-a', '-Z', '-p']:
    sys.stdout.write(fixture['keychains'].get(args[4], ''))
else:
    sys.exit(64)
'''


def der(name):
    return ('PRIVATE_CERT_' + name).encode() * 8


def sha1(name):
    return hashlib.sha1(der(name)).hexdigest().upper()


def pem(name, hash_override=None):
    body = base64.encodebytes(der(name)).decode()
    return ('SHA-256 hash: %s\nSHA-1 hash: %s\n-----BEGIN CERTIFICATE-----\n%s-----END CERTIFICATE-----\n'
            % ('0' * 64, hash_override or sha1(name), body))


def trust_list(entries):
    return plistlib.dumps({'trustVersion': 1, 'trustList': {key: ({'issuerName': b'x'} if value is None
        else {'issuerName': b'x', 'trustSettings': value}) for key, value in entries.items()}}).hex()


SSL = {'kSecTrustSettingsPolicy': b'p', 'kSecTrustSettingsPolicyName': 'sslServer', 'kSecTrustSettingsResult': 1}
X509 = {'kSecTrustSettingsPolicy': b'p', 'kSecTrustSettingsPolicyName': 'basicX509', 'kSecTrustSettingsResult': 2}
DENY = {'kSecTrustSettingsPolicy': b'p', 'kSecTrustSettingsPolicyName': 'sslServer', 'kSecTrustSettingsResult': 3}
CODE = {'kSecTrustSettingsPolicy': b'p', 'kSecTrustSettingsPolicyName': 'codeSign', 'kSecTrustSettingsResult': 1}
UNSPECIFIED = {'kSecTrustSettingsPolicy': b'p', 'kSecTrustSettingsPolicyName': 'sslServer', 'kSecTrustSettingsResult': 4}


class TrustSelectionTests(unittest.TestCase):
    def test_only_explicit_ssl_or_unconditional_trust_is_selected(self):
        settings = {'trustList': {
            'AA': {}, 'BB': {'trustSettings': []}, 'CC': {'trustSettings': [SSL]},
            'DD': {'trustSettings': [X509]}, 'EE': {'trustSettings': [DENY]},
            'FF': {'trustSettings': [CODE]}, '11': {'trustSettings': [UNSPECIFIED]},
            '22': {'trustSettings': [SSL, DENY]}, '33': {'trustSettings': [{'kSecTrustSettingsResult': 1}]},
            '44': {'trustSettings': [{'kSecTrustSettingsResult': 3}, X509]}, 'bad': 'PRIVATE'}}
        self.assertEqual(review_trust.selected_hashes([settings]), {'AA', 'BB', 'CC', 'DD', '33'})

    def test_malformed_settings_select_nothing(self):
        for value in (None, [], 'PRIVATE', {'trustList': []}, {'trustList': {'AA': {'trustSettings': 'x'}}}):
            with self.subTest(value=value):
                self.assertEqual(review_trust.selected_hashes([value]), set())


class TrustExportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='delegate-trust.')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.security = self.root / 'security'
        self.security.write_text(FAKE); self.security.chmod(0o755)
        self.fixture = self.root / 'fixture.json'
        self.output = self.root / 'trust'
        self.system, self.login = str(self.root / 'System.keychain'), str(self.root / 'login.keychain-db')
        for keychain in (self.system, self.login):
            Path(keychain).write_bytes(b'')
        self.previous = os.environ.get('FIXTURE_TRUST')
        os.environ['FIXTURE_TRUST'] = str(self.fixture)
        self.addCleanup(self.restore)

    def restore(self):
        if self.previous is None:
            os.environ.pop('FIXTURE_TRUST', None)
        else:
            os.environ['FIXTURE_TRUST'] = self.previous

    def write(self, admin, user, keychains, mode='normal'):
        self.fixture.write_text(json.dumps({'mode': mode, 'admin': trust_list(admin), 'user': trust_list(user),
            'keychains': keychains}))

    def export(self, timeout=5):
        return review_trust.export_trusted(self.output, security=str(self.security),
            keychains=[self.system, self.login], timeout=timeout)

    def test_selected_certificates_are_fetched_by_recomputed_hash_into_a_read_only_file(self):
        self.write({sha1('gateway'): [SSL], sha1('denied'): [DENY]}, {sha1('user'): None},
            {self.system: pem('gateway') + pem('denied') + pem('other'),
             self.login: pem('user') + pem('forged', hash_override=sha1('user'))})
        result = self.export()
        self.assertEqual(result['count'], 2)
        path = Path(result['path'])
        self.assertEqual(path.parent, self.output)
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o700)
        self.assertEqual(path.stat().st_mode & 0o777, 0o400)
        blocks = path.read_text().split('-----END CERTIFICATE-----')
        found = {hashlib.sha1(base64.b64decode(''.join(block.split('-----BEGIN CERTIFICATE-----')[1].split())))
                 .hexdigest().upper() for block in blocks if 'BEGIN' in block}
        self.assertEqual(found, {sha1('gateway'), sha1('user')})
        self.assertNotIn('SHA-1', path.read_text())

    def test_nothing_selected_is_not_a_failure_and_writes_no_file(self):
        self.write({sha1('denied'): [DENY]}, {}, {self.system: pem('denied'), self.login: ''})
        self.assertEqual(self.export(), {'count': 0, 'path': None})
        self.assertFalse(self.output.exists())

    def test_command_failure_timeout_bad_output_and_limits_raise_fixed_code_without_text(self):
        many = {sha1('c%d' % index): [SSL] for index in range(65)}
        cases = [
            ('fail', {}, {}, {}),
            ('hang', {}, {}, {}),
            ('normal', None, {}, {}),
            ('normal', many, {}, {self.system: ''.join(pem('c%d' % index) for index in range(65)), self.login: ''}),
        ]
        for mode, admin, user, keychains in cases:
            with self.subTest(mode=mode, limit=admin is many):
                if admin is None:
                    self.fixture.write_text(json.dumps({'mode': mode, 'admin': b'PRIVATE_NOT_PLIST'.hex(),
                        'user': trust_list({}), 'keychains': {}}))
                else:
                    self.write(admin, user, keychains, mode)
                with self.assertRaises(review_trust.TrustExportError) as caught:
                    self.export(timeout=1)
                self.assertEqual(str(caught.exception), 'system_trust_export_unavailable')
                self.assertFalse((self.output / review_trust.FILE_NAME).exists())

    def test_missing_security_command_is_the_same_fixed_failure(self):
        with self.assertRaisesRegex(review_trust.TrustExportError, '^system_trust_export_unavailable$'):
            review_trust.export_trusted(self.output, security=str(self.root / 'missing'),
                keychains=[self.system], timeout=1)


if __name__ == '__main__':
    unittest.main()
