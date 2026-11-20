#!/usr/bin/env python3
"""Patch fingerprint independent of git configuration and version (blob-pairs-v1).

Input maps each reviewed path to (from_mode, from_oid, to_mode, to_oid) as stored
in the two commit trees; a missing side is '000000' with an all-zero id. Only
these tree facts enter the digest, never diff text. The algorithm name always
means exactly this text; any change needs a new name.
"""
import hashlib

ALGORITHM = 'blob-pairs-v1'
HEADER = b'delegate-blob-pairs-v1\n'


def canonical(entries):
    lines = [HEADER]
    for path in sorted(entries, key=lambda name: name.encode('utf-8')):
        lines.append(path.encode('utf-8') + b'\0' + ' '.join(entries[path]).encode('ascii') + b'\n')
    return b''.join(lines)


def fingerprint(entries):
    return {'algorithm': ALGORITHM, 'sha256': hashlib.sha256(canonical(entries)).hexdigest(),
            'paths': sorted(entries, key=lambda name: name.encode('utf-8'))}
