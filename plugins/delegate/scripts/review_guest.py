"""Candidate guest snapshot/configuration boundaries, without a VM launcher.

Only explicit regular files are transported. Configuration validation does not
prove that a VM actually runs with those settings; actual guest checks are a gate.
"""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import uuid

MAX_BYTES = 8 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_WIRE_BYTES = 16 * 1024 * 1024


def _root(value):
    path = Path(value)
    if not path.is_absolute() or path.resolve(strict=True) != path or not path.is_dir():
        raise ValueError('snapshot root must be an existing canonical directory')
    return path


def _paths(paths):
    if not isinstance(paths, list) or not 1 <= len(paths) <= 256:
        raise ValueError('snapshot requires a bounded explicit file list')
    for name in paths:
        if (not isinstance(name, str) or not name or len(name) > 1024
                or name.startswith('/') or '\\' in name
                or any(ord(char) < 32 or ord(char) == 127 for char in name)
                or any(part in ('', '.', '..', '.git') for part in name.split('/'))):
            raise ValueError('invalid snapshot relative path')
    if len(set(paths)) != len(paths):
        raise ValueError('duplicate snapshot path')
    names = set(paths)
    if any('/'.join(name.split('/')[:end]) in names for name in paths
           for end in range(1, len(name.split('/')))):
        raise ValueError('snapshot file/directory collision')


def _open_file(root_fd, name, create=False):
    parent = os.dup(root_fd)
    try:
        parts = name.split('/')
        for part in parts[:-1]:
            if create:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=parent)
                except FileExistsError:
                    pass
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = next_fd
        flags = os.O_NOFOLLOW | (os.O_WRONLY | os.O_CREAT | os.O_EXCL if create
                                else os.O_RDONLY | os.O_NONBLOCK)
        return os.open(parts[-1], flags, 0o600, dir_fd=parent)
    finally:
        os.close(parent)


def pack_snapshot(root, paths, *, max_bytes=MAX_BYTES):
    _paths(paths)
    if type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES:
        raise ValueError('invalid snapshot byte limit')
    files, total = [], 0
    root_fd = os.open(_root(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in paths:
            try:
                with os.fdopen(_open_file(root_fd, name), 'rb') as source:
                    before = os.fstat(source.fileno())
                    if (not stat.S_ISREG(before.st_mode) or before.st_nlink != 1
                            or before.st_size > MAX_FILE_BYTES):
                        raise ValueError('snapshot requires bounded regular files without links')
                    data = source.read(MAX_FILE_BYTES + 1)
                    after = os.fstat(source.fileno())
                    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns', 'st_nlink')
                    if any(getattr(before, key) != getattr(after, key) for key in fields):
                        raise ValueError('snapshot source changed during capture')
                total += len(data)
                if len(data) > MAX_FILE_BYTES or total > max_bytes:
                    raise ValueError('snapshot byte limit exceeded')
                files.append({'path': name, 'sha256': hashlib.sha256(data).hexdigest(),
                              'data': base64.b64encode(data).decode('ascii')})
            except OSError:
                raise ValueError('snapshot source unavailable or linked') from None
    finally:
        os.close(root_fd)
    return json.dumps({'schema_version': 1, 'files': files}, separators=(',', ':')).encode('utf-8')


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate snapshot JSON field')
        result[key] = value
    return result


def unpack_snapshot(wire, target):
    if not isinstance(wire, bytes) or len(wire) > MAX_WIRE_BYTES:
        raise ValueError('invalid snapshot wire size')
    try:
        document = json.loads(wire, object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError):
        raise ValueError('invalid snapshot JSON') from None
    if (not isinstance(document, dict) or set(document) != {'schema_version', 'files'}
            or type(document['schema_version']) is not int or document['schema_version'] != 1
            or not isinstance(document['files'], list)):
        raise ValueError('unsupported snapshot schema')
    records = document['files']
    if any(not isinstance(record, dict) or set(record) != {'path', 'sha256', 'data'}
           for record in records):
        raise ValueError('invalid snapshot record')
    paths = [record['path'] for record in records]
    _paths(paths)
    decoded, total = [], 0
    for record in records:
        if (not isinstance(record['sha256'], str)
                or not re.fullmatch(r'[0-9a-f]{64}', record['sha256'])
                or not isinstance(record['data'], str)):
            raise ValueError('invalid snapshot data')
        try:
            data = base64.b64decode(record['data'], validate=True)
        except (ValueError, binascii.Error):
            raise ValueError('invalid snapshot encoding') from None
        total += len(data)
        if (len(data) > MAX_FILE_BYTES or total > MAX_BYTES
                or hashlib.sha256(data).hexdigest() != record['sha256']):
            raise ValueError('snapshot integrity or size mismatch')
        decoded.append(data)
    target = _root(target)
    if any(target.iterdir()):
        raise ValueError('snapshot target must be empty')
    root_fd = os.open(target, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name, data in zip(paths, decoded):
            with os.fdopen(_open_file(root_fd, name, create=True), 'wb') as output:
                output.write(data)
    finally:
        os.close(root_fd)
    return paths


def validate_configuration(configuration):
    if not isinstance(configuration, dict) or configuration.get('plain') is not True:
        raise ValueError('dedicated guest requires plain mode')
    if any(configuration.get(key) != [] for key in ('mounts', 'portForwards', 'provision')):
        raise ValueError('guest shares, forwarding and provisioning must be explicitly empty')
    for key, flags in [('ssh', ('forwardAgent',)), ('containerd', ('system', 'user')),
                       ('rosetta', ('enabled',))]:
        section = configuration.get(key)
        if not isinstance(section, dict) or any(section.get(flag) is not False for flag in flags):
            raise ValueError('guest convenience capability is enabled or unknown')


class GuestLease:
    """Exclusive local control record; never reclaim another/stale owner."""
    def __init__(self, directory, guest):
        if not isinstance(guest, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', guest):
            raise ValueError('invalid dedicated guest name')
        self.path = _root(directory) / ('guest-' + hashlib.sha256(guest.encode()).hexdigest() + '.lock')
        self.fd = None

    def __enter__(self):
        self.fd = os.open(self.path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            os.write(self.fd, uuid.uuid4().hex.encode('ascii'))
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def __exit__(self, *_):
        try:
            owned = os.fstat(self.fd)
            current = self.path.lstat()
            if (current.st_dev, current.st_ino) != (owned.st_dev, owned.st_ino):
                raise ValueError('guest ownership record changed; refusing removal')
            self.path.unlink()
        finally:
            os.close(self.fd)
            self.fd = None
