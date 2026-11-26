#!/usr/bin/env python3
"""Per-backend default model and effort from the user-level configuration (spec/default-model.md)."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import delegate_defaults
from delegate_defaults import ConfigError, config_path, load, resolve

CODEX = {'model': 'gpt-6.2-sol', 'effort': 'high'}
CLAUDE = {'model': 'claude-opus-5-5', 'effort': None}


class ResolveTests(unittest.TestCase):
    """DM-01: explicit > configuration > host default, for model and effort separately."""

    def test_every_combination(self):
        config = {'codex': CODEX, 'claude-code': CLAUDE}
        cases = [
            (('codex', None, None, config), ('gpt-6.2-sol', 'config', 'high', 'config')),
            (('codex', 'gpt-5.4-mini', None, config), ('gpt-5.4-mini', 'explicit', 'high', 'config')),
            (('codex', None, 'low', config), ('gpt-6.2-sol', 'config', 'low', 'explicit')),
            (('codex', 'gpt-5.4-mini', 'low', config), ('gpt-5.4-mini', 'explicit', 'low', 'explicit')),
            (('codex', None, None, {}), (None, 'host_default', None, 'host_default')),
            (('codex', 'gpt-5.4-mini', None, {}), ('gpt-5.4-mini', 'explicit', None, 'host_default')),
            (('codex', None, None, {'codex': {'model': None, 'effort': 'xhigh'}}),
             (None, 'host_default', 'xhigh', 'config')),
            (('claude-code', None, None, config), ('claude-opus-5-5', 'config', None, 'host_default')),
            (('claude-code', 'sonnet', None, config), ('sonnet', 'explicit', None, 'host_default')),
            (('claude-code', None, None, {'codex': CODEX}), (None, 'host_default', None, 'host_default')),
        ]
        for arguments, expected in cases:
            with self.subTest(arguments=arguments):
                self.assertEqual(resolve(*arguments), expected)

    def test_sources_and_efforts_are_the_published_sets(self):
        self.assertEqual(delegate_defaults.SOURCES, ('explicit', 'config', 'host_default', 'resumed'))
        self.assertEqual(delegate_defaults.EFFORTS, ('none', 'minimal', 'low', 'medium', 'high', 'xhigh'))


class PathTests(unittest.TestCase):
    """DM-02: XDG_CONFIG_HOME when absolute, otherwise ~/.config."""

    def test_absolute_unset_and_relative(self):
        cases = [({'XDG_CONFIG_HOME': '/x/cfg', 'HOME': '/h'}, '/x/cfg/delegate/config.json'),
                 ({'HOME': '/h'}, '/h/.config/delegate/config.json'),
                 ({'XDG_CONFIG_HOME': 'cfg', 'HOME': '/h'}, '/h/.config/delegate/config.json'),
                 ({'XDG_CONFIG_HOME': '', 'HOME': '/h'}, '/h/.config/delegate/config.json')]
        for environ, expected in cases:
            with self.subTest(environ=environ):
                self.assertEqual(str(config_path(environ)), expected)

    def test_relative_or_missing_home_uses_the_account_home(self):
        # A repository must not be able to supply "user-level" configuration through HOME=. (review finding 3).
        import pwd
        account = pwd.getpwuid(os.getuid()).pw_dir
        for environ in ({'HOME': '.'}, {'HOME': 'repo'}, {}):
            with self.subTest(environ=environ):
                self.assertEqual(str(config_path(environ)), os.path.join(account, '.config/delegate/config.json'))


class LoadTests(unittest.TestCase):
    """DM-03 at the function level: every error code, key paths, and no echoed values."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / 'config.json'

    def tearDown(self):
        self.directory.cleanup()

    def write(self, document):
        text = document if isinstance(document, str) else json.dumps(document)
        self.path.write_text(text, encoding='utf-8')

    def failure(self):
        with self.assertRaises(ConfigError) as caught:
            load(self.path)
        return caught.exception

    def test_missing_file_is_no_configuration(self):
        self.assertEqual(load(self.path), {})

    def test_valid_configuration(self):
        self.write({'schema': 'delegate.config/v1',
                    'defaults': {'codex': {'model': 'gpt-6.2-sol', 'effort': 'high'},
                                 'claude-code': {'model': 'claude-opus-5-5'}}})
        self.assertEqual(load(self.path), {'codex': CODEX, 'claude-code': CLAUDE})

    def test_backends_and_fields_are_optional(self):
        self.write({'schema': 'delegate.config/v1', 'defaults': {'codex': {'effort': 'low'}}})
        self.assertEqual(load(self.path), {'codex': {'model': None, 'effort': 'low'}})
        self.write({'schema': 'delegate.config/v1', 'defaults': {}})
        self.assertEqual(load(self.path), {})

    def test_field_errors_name_the_key(self):
        base = {'schema': 'delegate.config/v1'}
        cases = [
            ({'defaults': {}}, 'invalid_schema', 'schema'),
            ({**base, 'schema': 'delegate.config/v2', 'defaults': {}}, 'invalid_schema', 'schema'),
            (base, 'invalid_schema', 'defaults'),
            ({**base, 'defaults': []}, 'invalid_schema', 'defaults'),
            ({**base, 'defaults': {'codex': 'gpt-6.2-sol'}}, 'invalid_schema', 'defaults.codex'),
            ({**base, 'defaults': {'codex': {'model': 5}}}, 'invalid_schema', 'defaults.codex.model'),
            ({**base, 'defaults': {}, 'extra': 1}, 'unknown_key', 'extra'),
            ({**base, 'defaults': {'claude': {}}}, 'unknown_key', 'defaults.claude'),
            ({**base, 'defaults': {'codex': {'modle': 'gpt-6.2-sol'}}}, 'unknown_key', 'defaults.codex.modle'),
            ({**base, 'defaults': {'codex': {'model': 'bad model'}}}, 'invalid_model', 'defaults.codex.model'),
            ({**base, 'defaults': {'codex': {'model': ''}}}, 'invalid_model', 'defaults.codex.model'),
            ({**base, 'defaults': {'claude-code': {'model': 'opusplan'}}}, 'invalid_model',
             'defaults.claude-code.model'),
            ({**base, 'defaults': {'codex': {'model': 'claude-opus-5-5'}}}, 'model_belongs_to_other_backend',
             'defaults.codex.model'),
            ({**base, 'defaults': {'claude-code': {'model': 'gpt-6.2-sol'}}}, 'model_belongs_to_other_backend',
             'defaults.claude-code.model'),
            ({**base, 'defaults': {'codex': {'effort': 'maximum'}}}, 'invalid_effort', 'defaults.codex.effort'),
            ({**base, 'defaults': {'claude-code': {'effort': 'high'}}}, 'effort_not_supported',
             'defaults.claude-code.effort'),
        ]
        for document, code, key in cases:
            with self.subTest(code=code, key=key):
                self.write(document)
                error = self.failure()
                self.assertEqual((error.code, error.key), (code, key))
                self.assertEqual(error.line(self.path),
                                 'delegate: invalid config %s: %s at %s' % (self.path, code, key))

    def test_whole_file_errors_have_no_key(self):
        cases = [('{not json', 'invalid_json'), ('[]', 'invalid_schema'),
                 ('{"schema": "delegate.config/v1", "schema": "x", "defaults": {}}', 'invalid_json')]
        for text, code in cases:
            with self.subTest(code=code):
                self.write(text)
                error = self.failure()
                self.assertEqual((error.code, error.key), (code, None))
                self.assertEqual(error.line(self.path), 'delegate: invalid config %s: %s' % (self.path, code))
        self.path.write_bytes(b'\xff\xfe{}')
        self.assertEqual(self.failure().code, 'invalid_json')
        self.path.write_bytes(b' ' * (64 * 1024 + 1))
        self.assertEqual(self.failure().code, 'too_large')
        # Deep nesting below the size limit must still be a configuration error, not a crash (review finding 1).
        self.path.write_bytes(b'[' * 60000)
        self.assertEqual(self.failure().code, 'invalid_json')

    def test_error_line_stays_one_line_for_odd_paths(self):
        error = ConfigError('invalid_json')
        line = error.line(Path('/tmp/a\nb\rc/config.json'))
        self.assertNotIn('\n', line)
        self.assertNotIn('\r', line)
        self.assertEqual(line, 'delegate: invalid config /tmp/a\\nb\\rc/config.json: invalid_json')

    def test_symlinks_and_directories_are_not_regular_files(self):
        target = Path(self.directory.name) / 'real.json'
        target.write_text('{"schema": "delegate.config/v1", "defaults": {}}', encoding='utf-8')
        self.path.symlink_to(target)
        self.assertEqual(self.failure().code, 'not_regular_file')
        self.path.unlink()
        self.path.mkdir()
        self.assertEqual(self.failure().code, 'not_regular_file')

    @unittest.skipIf(os.geteuid() == 0, 'root can read mode 000 files')
    def test_unreadable_file(self):
        self.write({'schema': 'delegate.config/v1', 'defaults': {}})
        self.path.chmod(0)
        try:
            self.assertEqual(self.failure().code, 'unreadable')
        finally:
            self.path.chmod(0o600)

    def test_values_are_never_echoed(self):
        secret = 'sk-do-not-print'
        self.write({'schema': 'delegate.config/v1', 'defaults': {'codex': {'model': secret + ' x'}}})
        self.assertNotIn(secret, self.failure().line(self.path))
        self.write({'schema': 'delegate.config/v1', 'defaults': {}, secret + ' \n': 1})
        line = self.failure().line(self.path)
        self.assertNotIn(secret, line)
        self.assertNotIn('\n', line)




class EntryErrorTests(unittest.TestCase):
    """DM-03 end to end: every error code stops both review and run with exactly one stderr line."""

    def setUp(self):
        import subprocess
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.repo = root / 'repo'
        self.repo.mkdir()
        for command in (['init', '-q'], ['config', 'user.email', 't@example.invalid'], ['config', 'user.name', 't']):
            subprocess.run(['git', *command], cwd=self.repo, check=True)
        (self.repo / 'a.txt').write_text('a\n')
        subprocess.run(['git', 'add', 'a.txt'], cwd=self.repo, check=True)
        subprocess.run(['git', 'commit', '-qm', 'init'], cwd=self.repo, check=True)
        self.config = root / 'config-home' / 'delegate' / 'config.json'
        self.config.parent.mkdir(parents=True)
        # No codex on PATH: a configuration error must stop before any executor is looked up.
        self.env = {'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin', 'HOME': str(root),
                    'TMPDIR': str(root), 'XDG_CONFIG_HOME': str(root / 'config-home'), 'PYTHONDONTWRITEBYTECODE': '1'}

    def tearDown(self):
        if self.config.exists() and not self.config.is_symlink():
            self.config.chmod(0o600)
        self.directory.cleanup()

    def entry(self, *arguments):
        import subprocess
        return subprocess.run(['/bin/bash', str(Path(delegate_defaults.__file__).with_name('delegate-exec.sh')),
                               *arguments], cwd=self.repo, env=self.env, capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL)

    def cases(self):
        base = '{"schema": "delegate.config/v1", "defaults": %s}'
        texts = [('invalid_json', None, '{'), ('invalid_schema', 'schema', '{"defaults": {}}'),
                 ('unknown_key', 'defaults.claude', base % '{"claude": {}}'),
                 ('invalid_model', 'defaults.codex.model', base % '{"codex": {"model": "a b"}}'),
                 ('model_belongs_to_other_backend', 'defaults.codex.model', base % '{"codex": {"model": "opus"}}'),
                 ('invalid_effort', 'defaults.codex.effort', base % '{"codex": {"effort": "max"}}'),
                 ('effort_not_supported', 'defaults.claude-code.effort', base % '{"claude-code": {"effort": "low"}}')]
        for code, key, text in texts:
            yield code, key, lambda text=text: self.config.write_text(text)
        yield 'too_large', None, lambda: self.config.write_bytes(b' ' * (64 * 1024 + 1))

        def symlink():
            target = self.config.with_name('real.json')
            target.write_text(base % '{}')
            self.config.symlink_to(target)
        yield 'not_regular_file', None, symlink
        if os.geteuid() != 0:
            def unreadable():
                self.config.write_text(base % '{}')
                self.config.chmod(0)
            yield 'unreadable', None, unreadable

    def test_every_code_through_review_and_run(self):
        seen = set()
        for code, key, prepare in self.cases():
            if self.config.is_symlink() or self.config.exists():
                self.config.chmod(0o600) if not self.config.is_symlink() else None
                self.config.unlink()
            prepare()
            expected = 'delegate: invalid config %s: %s%s\n' % (self.config, code, ' at ' + key if key else '')
            for arguments in (('review', '--paths', 'a.txt', '--', 'x'), ('run', '--', 'x')):
                with self.subTest(code=code, command=arguments[0]):
                    result = self.entry(*arguments)
                    self.assertEqual((result.returncode, result.stderr, result.stdout), (64, expected, ''))
            seen.add(code)
        self.assertGreaterEqual(seen, {'invalid_json', 'invalid_schema', 'unknown_key', 'invalid_model',
                                       'model_belongs_to_other_backend', 'invalid_effort', 'effort_not_supported',
                                       'too_large', 'not_regular_file'})

class DoctorTests(unittest.TestCase):
    """DM-11: the default-model section, exit 1 only for a bad configuration, --reviewers unchanged."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.config = root / 'config-home' / 'delegate' / 'config.json'
        self.config.parent.mkdir(parents=True)
        self.env = {'PATH': str(Path(sys.executable).parent) + ':/usr/bin:/bin', 'HOME': str(root),
                    'TMPDIR': str(root), 'XDG_CONFIG_HOME': str(root / 'config-home'), 'PYTHONDONTWRITEBYTECODE': '1',
                    'DELEGATE_FIXTURE_REVIEWERS': json.dumps({'codex': None, 'claude-code': None})}

    def tearDown(self):
        self.directory.cleanup()

    def doctor(self, *options):
        import subprocess
        return subprocess.run([sys.executable, '-B', str(Path(delegate_defaults.__file__).with_name('review_doctor.py')),
                               *options], env=self.env, capture_output=True, text=True, timeout=60,
                              stdin=subprocess.DEVNULL, cwd=self.directory.name)

    def test_without_configuration(self):
        for options in [(), ('--backend', 'codex'), ('--backend', 'claude-code')]:
            with self.subTest(options=options):
                result = self.doctor(*options)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('默认模型：配置文件 %s（不存在）' % self.config, result.stdout)
                self.assertIn('codex：模型 宿主默认；推理档 宿主默认', result.stdout)
                self.assertIn('claude-code：模型 宿主默认；推理档 不支持', result.stdout)

    def test_valid_configuration(self):
        self.config.write_text(json.dumps({'schema': 'delegate.config/v1',
                                           'defaults': {'codex': {'model': 'gpt-6.2-sol'},
                                                        'claude-code': {'model': 'claude-opus-5-5'}}}))
        result = self.doctor()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('默认模型：配置文件 %s（存在）' % self.config, result.stdout)
        self.assertIn('codex：模型 gpt-6.2-sol（delegate 配置）；推理档 宿主默认', result.stdout)
        self.assertIn('claude-code：模型 claude-opus-5-5（delegate 配置）；推理档 不支持', result.stdout)

    def test_bad_configuration_finishes_the_other_checks_and_exits_1(self):
        self.config.write_text('{"schema": "delegate.config/v1", "defaults": {"codex": {"effort": "max"}}}')
        line = 'delegate: invalid config %s: invalid_effort at defaults.codex.effort' % self.config
        for options, later in [((), 'Codex'), (('--backend', 'claude-code'), '诊断完成')]:
            with self.subTest(options=options):
                result = self.doctor(*options)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn('配置无效：' + line, result.stdout)
                self.assertIn(later, result.stdout.split('配置无效：', 1)[1])

    def test_reviewers_listing_is_unchanged(self):
        self.config.write_text('{"schema": "x"}')
        result = self.doctor('--reviewers', '--json')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('默认模型', result.stdout)
        self.assertEqual(json.loads(result.stdout)['schema'], 'delegate.reviewers/v1')

if __name__ == '__main__':
    unittest.main()
