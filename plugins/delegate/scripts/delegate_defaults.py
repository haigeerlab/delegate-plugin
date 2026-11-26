#!/usr/bin/env python3
"""User-level per-backend default model and effort (spec/default-model.md).

delegate only reads this file; it never creates or changes it, nor any host configuration.
"""
import json
import os
from pathlib import Path
import pwd
import re
import stat

from delegate_model import model_error

SCHEMA = 'delegate.config/v1'
SOURCES = ('explicit', 'config', 'host_default', 'resumed')
EFFORTS = ('none', 'minimal', 'low', 'medium', 'high', 'xhigh')
MAX_BYTES = 64 * 1024
FIELDS = {'codex': ('model', 'effort'), 'claude-code': ('model',)}
_KEY_NAME = re.compile(r'[A-Za-z0-9_-]{1,64}')


class ConfigError(ValueError):
    def __init__(self, code, key=None):
        super().__init__(code)
        self.code = code
        self.key = key

    def line(self, path):
        # Names only: the offending value is never echoed.
        # One line whatever the path holds, so callers can relay it as is.
        shown = str(path).replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
        return 'delegate: invalid config %s: %s%s' % (shown, self.code, ' at ' + self.key if self.key else '')


def config_path(environ=None):
    environ = os.environ if environ is None else environ
    base = environ.get('XDG_CONFIG_HOME') or ''
    if not os.path.isabs(base):
        home = environ.get('HOME') or ''
        if not os.path.isabs(home):
            # A relative HOME would let the current repository supply "user-level" configuration.
            home = pwd.getpwuid(os.getuid()).pw_dir
        base = os.path.join(home, '.config')
    return Path(base) / 'delegate' / 'config.json'


def _key(prefix, name):
    name = name if isinstance(name, str) and _KEY_NAME.fullmatch(name) else '?'
    return prefix + '.' + name if prefix else name


def _unique(pairs):
    seen = {}
    for name, value in pairs:
        if name in seen:
            raise ConfigError('invalid_json')
        seen[name] = value
    return seen


def _unknown(document, allowed, prefix):
    for name in sorted(document, key=str):
        if name not in allowed:
            raise ConfigError('unknown_key', _key(prefix, name))


def _read(path):
    try:
        descriptor = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0))
    except FileNotFoundError:
        return None
    except OSError as error:
        if os.path.islink(str(path)) or os.path.isdir(str(path)):
            raise ConfigError('not_regular_file') from None
        raise ConfigError('unreadable') from error
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ConfigError('not_regular_file')
        with os.fdopen(descriptor, 'rb') as handle:
            descriptor = None
            data = handle.read(MAX_BYTES + 1)
    except OSError as error:
        raise ConfigError('unreadable') from error
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(data) > MAX_BYTES:
        raise ConfigError('too_large')
    return data


def load(path):
    """Return {backend: {'model', 'effort'}}; {} when the file does not exist."""
    data = _read(path)
    if data is None:
        return {}
    try:
        document = json.loads(data.decode('utf-8'), object_pairs_hook=_unique)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        if isinstance(error, ConfigError):
            raise
        raise ConfigError('invalid_json') from None
    if not isinstance(document, dict):
        raise ConfigError('invalid_schema')
    _unknown(document, ('schema', 'defaults'), '')
    if document.get('schema') != SCHEMA:
        raise ConfigError('invalid_schema', 'schema')
    defaults = document.get('defaults')
    if not isinstance(defaults, dict):
        raise ConfigError('invalid_schema', 'defaults')
    _unknown(defaults, tuple(FIELDS), 'defaults')
    config = {}
    for backend in FIELDS:
        if backend not in defaults:
            continue
        prefix = 'defaults.' + backend
        entry = defaults[backend]
        if not isinstance(entry, dict):
            raise ConfigError('invalid_schema', prefix)
        if backend == 'claude-code' and 'effort' in entry:
            raise ConfigError('effort_not_supported', prefix + '.effort')
        _unknown(entry, FIELDS[backend], prefix)
        for field in FIELDS[backend]:
            if field in entry and not isinstance(entry[field], str):
                raise ConfigError('invalid_schema', prefix + '.' + field)
        model = entry.get('model')
        if model is not None:
            problem = model_error(backend, model) if model else 'invalid --model'
            if problem:
                code = 'model_belongs_to_other_backend' if 'other backend' in problem else 'invalid_model'
                raise ConfigError(code, prefix + '.model')
        effort = entry.get('effort')
        if effort is not None and effort not in EFFORTS:
            raise ConfigError('invalid_effort', prefix + '.effort')
        if model is not None or effort is not None:
            config[backend] = {'model': model, 'effort': effort}
    return config


def resolve(backend, model, effort, config):
    """Return (model, model_source, effort, effort_source): explicit > configuration > host default."""
    entry = config.get(backend) or {}
    chosen = []
    for explicit, configured in ((model, entry.get('model')), (effort, entry.get('effort'))):
        if explicit is not None:
            chosen += [explicit, 'explicit']
        elif configured is not None:
            chosen += [configured, 'config']
        else:
            chosen += [None, 'host_default']
    return tuple(chosen)
