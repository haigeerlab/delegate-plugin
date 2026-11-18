#!/usr/bin/env python3
"""Export certificates explicitly trusted on this Mac for the sandboxed Claude CLI.

Only admin/user trust settings that the user already applies outside the sandbox
are honored; certificates are matched by a locally recomputed SHA-1. Failures
are fixed codes, never security output, names, hashes or paths.
"""
import base64
import binascii
import hashlib
import os
from pathlib import Path
import plistlib
import pwd
import re
import shutil
import subprocess
import tempfile

SECURITY = '/usr/bin/security'
FILE_NAME = 'trusted.pem'
MAX_CERTIFICATES = 64
MAX_BYTES = 1024 * 1024
OUTPUT_LIMIT = 32 * 1024 * 1024
SSL_POLICIES = (None, 'sslServer', 'basicX509')
TRUSTED_RESULTS = (1, 2)  # TrustRoot, TrustAsRoot
DENY_RESULT = 3
PEM = re.compile(rb'-----BEGIN CERTIFICATE-----(.+?)-----END CERTIFICATE-----', re.S)


class TrustExportError(Exception):
    pass


def default_keychains():
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    return ['/Library/Keychains/System.keychain', str(home / 'Library/Keychains/login.keychain-db')]


def selected_hashes(documents):
    selected = set()
    for document in documents:
        entries = document.get('trustList') if isinstance(document, dict) else None
        if not isinstance(entries, dict):
            continue
        for key, record in entries.items():
            if not isinstance(key, str) or not isinstance(record, dict):
                continue
            settings = record.get('trustSettings', [])
            if not isinstance(settings, list) or not all(isinstance(item, dict) for item in settings):
                continue
            # An absent result means TrustRoot; trust for other policies does not apply to TLS.
            relevant = [item for item in settings if item.get('kSecTrustSettingsPolicyName') in SSL_POLICIES]
            results = [item.get('kSecTrustSettingsResult', 1) for item in relevant]
            if DENY_RESULT in results:
                continue
            if not settings or any(result in TRUSTED_RESULTS for result in results):
                selected.add(key.upper())
    return selected


def _run(argv, timeout):
    try:
        result = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise TrustExportError('system_trust_export_unavailable') from None
    if result.returncode != 0 or len(result.stdout) > OUTPUT_LIMIT:
        raise TrustExportError('system_trust_export_unavailable')
    return result.stdout


def export_trusted(directory, *, security=SECURITY, keychains=None, timeout=5):
    """Write explicitly trusted certificates to directory/FILE_NAME (0400).

    Returns {'count', 'path'}; path is None when nothing is selected.
    """
    directory = Path(directory)
    keychains = default_keychains() if keychains is None else keychains
    scratch = Path(tempfile.mkdtemp(prefix='delegate-trust-settings.', dir=directory.parent))
    try:
        documents = []
        for name, flags in (('admin.plist', ['-d']), ('user.plist', [])):
            target = scratch / name
            _run([security, 'trust-settings-export', *flags, str(target)], timeout)
            try:
                documents.append(plistlib.loads(target.read_bytes()))
            except (OSError, ValueError, plistlib.InvalidFileException):
                raise TrustExportError('system_trust_export_unavailable') from None
        wanted = selected_hashes(documents)
        found = {}
        if wanted:
            for keychain in keychains:
                if not Path(keychain).exists():
                    continue
                for block in PEM.findall(_run([security, 'find-certificate', '-a', '-Z', '-p', keychain], timeout)):
                    try:
                        der = base64.b64decode(b''.join(block.split()), validate=True)
                    except (binascii.Error, ValueError):
                        continue
                    digest = hashlib.sha1(der).hexdigest().upper()
                    if digest in wanted:
                        found.setdefault(digest, der)
        if not found:
            return {'count': 0, 'path': None}
        if len(found) > MAX_CERTIFICATES:
            raise TrustExportError('system_trust_export_unavailable')
        text = ''.join('-----BEGIN CERTIFICATE-----\n%s-----END CERTIFICATE-----\n'
                       % base64.encodebytes(found[digest]).decode() for digest in sorted(found))
        if len(text.encode()) > MAX_BYTES:
            raise TrustExportError('system_trust_export_unavailable')
        directory.mkdir(mode=0o700)
        path = directory / FILE_NAME
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o400), 'w') as output:
            output.write(text)
        return {'count': len(found), 'path': str(path)}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
