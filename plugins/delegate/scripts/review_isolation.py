"""Fixed srt policy shared by native Mac review and explicit OS fixtures.

Policy unit tests alone do not establish OS enforcement, CLI authentication
compatibility or process cleanup; each has separate actual acceptance.
"""
from pathlib import Path
import re
import sys


def canonical_path(value, directory=False):
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError('isolation paths must be absolute, existing and free of symlink aliases')
    if directory and not path.is_dir():
        raise ValueError('isolation root must be a directory')
    return path


def overlaps(left, right):
    return left == right or left in right.parents or right in left.parents


def literal(path):
    return {'path': str(path), 'literal': True}


def build_policy(*, snapshot, writable, home, protected, readable, allowed_domains):
    """Build fixed restrictions; callers supply trusted runtime reads/endpoints.

    No user settings, policy merging, arbitrary exemptions or credential masks.
    The child must not inherit writable descriptors beyond its standard pipes.
    """
    snapshot = canonical_path(snapshot, directory=True)
    writable = canonical_path(writable, directory=True)
    home = canonical_path(home, directory=True)
    protected = [canonical_path(path) for path in protected]
    readable = [canonical_path(path) for path in readable]
    if any(overlaps(writable, path) for path in [snapshot, home] + protected):
        raise ValueError('writable directory overlaps a protected root')
    if any(overlaps(path, root) for path in readable for root in protected):
        raise ValueError('runtime read grants overlap protected source')
    domains = []
    for domain in allowed_domains:
        if not isinstance(domain, str) or not re.fullmatch(
                r'[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?', domain):
            raise ValueError('network policy requires exact hostnames, optionally with a port')
        host, separator, port = domain.partition(':')
        if '..' in host or (separator and not 1 <= int(port) <= 65535):
            raise ValueError('invalid network endpoint')
        domains.append(domain.lower())
    # srt adds its own write paths. Explicitly deny non-stdio additions rather
    # than assuming that an empty allowWrite list removes those defaults.
    denied_writes = [snapshot, home] + protected + [
        Path('/tmp/claude'), Path('/private/tmp/claude'),
        Path('/dev/tty'), Path('/dev/dtracehelper'), Path('/dev/autofs_nowait'),
    ]
    return {
        'filesystem': {
            'denyRead': [literal('/')],
            'allowRead': [literal(path) for path in [snapshot, writable] + readable],
            'allowWrite': [literal(writable)],
            'denyWrite': [literal(path) for path in denied_writes],
            'allowGitConfig': False,
        },
        'network': {
            'allowedDomains': domains,
            'deniedDomains': [],
            'strictAllowlist': True,
            'allowUnixSockets': [],
            'allowAllUnixSockets': False,
            'allowLocalBinding': False,
            'allowMachLookup': [],
        },
        'enableWeakerNestedSandbox': False,
        'enableWeakerNetworkIsolation': False,
        'allowAppleEvents': False,
    }


def build_linux_policy(**options):
    """Root denial alone excludes srt's kernel top-level directories.

    Fresh namespace /proc remains available; host cgroup/sys and runtime sockets
    must also be masked explicitly. Linux private binding needs the separate
    review_network entry wrapper; allowLocalBinding is not that syscall filter.
    """
    if sys.platform != 'linux':
        raise ValueError('Linux policy requires Linux')
    policy = build_policy(**options)
    policy['filesystem']['denyRead'] += [literal(Path('/sys')), literal(Path('/run'))]
    return policy
