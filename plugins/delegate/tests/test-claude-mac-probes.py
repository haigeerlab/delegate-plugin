#!/usr/bin/env python3
"""Opt-in original CLI probes inside the native boundary; never uses -p."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import pwd
import sys
import tempfile
import unittest

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--srt', required=True)
parser.add_argument('--claude', required=True)
parser.add_argument('--claude-sha256', required=True)
arguments, remaining = parser.parse_known_args()
sys.argv = [sys.argv[0]] + remaining
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from review_macos import MacBoundary
from review_isolation import build_policy
from claude_review import SAFE_PREFIX, preflight


class OriginalMacProbes(unittest.TestCase):
    def test_original_interface_and_authentication_in_strict_boundary(self):
        with tempfile.TemporaryDirectory(prefix='delegate-mac-cli.', dir='/private/tmp') as name:
            root = Path(name).resolve()
            snapshot, writable, controls = [root / child for child in ('snapshot', 'writable', 'controls')]
            for path in (snapshot, writable, controls):
                path.mkdir(mode=0o700)
            home = Path(pwd.getpwuid(os.getuid()).pw_dir).resolve(strict=True)
            readable = [Path('/System'), Path('/usr'), Path('/bin').resolve(),
                Path('/sbin').resolve(), Path('/dev'), Path(arguments.claude)]
            # Original CLI/keychain broker needs this runtime read. This is
            # not a reviewer-tool grant; model tool isolation is a separate gate.
            for path in (home / '.claude', home / '.claude.json', home / 'Library/Keychains'):
                if path.exists():
                    readable.append(path.resolve(strict=True))
            config = root / 'policy.json'
            config.write_text(json.dumps(build_policy(snapshot=snapshot, writable=writable,
                home=home, protected=[controls, SCRIPTS.parents[2]], readable=readable,
                allowed_domains=[])))
            username = pwd.getpwuid(os.getuid()).pw_name
            environment = {'HOME': str(home), 'USER': username, 'LOGNAME': username,
                'PATH': '/opt/homebrew/bin:/usr/bin:/bin',
                'SHELL': '/bin/bash', 'TMPDIR': str(writable), 'CLAUDE_CODE_TMPDIR': str(writable),
                'PYTHONDONTWRITEBYTECODE': '1', 'DELEGATE_REVIEW_DEPTH': '1',
                'DISABLE_AUTOUPDATER': '1', 'CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC': '1',
                'DISABLE_TELEMETRY': '1', 'DISABLE_ERROR_REPORTING': '1',
                'ENABLE_CLAUDEAI_MCP_SERVERS': 'false', 'CLAUDE_CODE_DISABLE_ARTIFACT': '1',
                'CLAUDE_CODE_SKIP_PROMPT_HISTORY': '1'}
            probes = []
            def invoke(argv, *, deadline, stdin=None):
                self.assertIsNone(stdin)
                self.assertNotIn('-p', argv)
                self.assertEqual(argv[:len(SAFE_PREFIX) + 1], [arguments.claude, *SAFE_PREFIX])
                control = controls / str(len(probes)); control.mkdir(mode=0o700)
                boundary = MacBoundary(control)
                result = boundary.run([arguments.srt, '--settings', str(config), '--', *argv],
                    cwd=snapshot, environment=environment, deadline=deadline)
                probes.append(result['execution_status'])
                self.assertEqual(result['cleanup'], 'confirmed', result['diagnostics'])
                self.assertFalse(boundary.service_loaded())
                return result
            conditions = preflight(arguments.claude, invoke)
            self.assertEqual(probes, ['completed'] * 3)
            self.assertEqual(conditions['auth_method'], 'claude.ai')
            self.assertEqual(conditions['provider'], 'firstParty')
            # Safe metadata only. Never print the raw auth JSON or stderr.
            print(json.dumps({'original_mac_probes': 3, 'model_calls': 0,
                'cli_version': conditions['version'], 'authentication': conditions['auth_method'],
                'provider': conditions['provider'], 'cleanup': 'confirmed'}), flush=True)


if __name__ == '__main__':
    executable = Path(arguments.claude)
    if (sys.platform != 'darwin' or not executable.is_absolute()
            or executable.resolve(strict=True) != executable
            or hashlib.sha256(executable.read_bytes()).hexdigest() != arguments.claude_sha256
            or not Path(arguments.srt).is_absolute() or not Path(arguments.srt).is_file()):
        parser.error('requires macOS, pinned original CLI and existing srt; no model calls')
    unittest.main(verbosity=2)
