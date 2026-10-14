#!/usr/bin/env python3
"""Offline manager faults; these do not establish Linux kernel enforcement."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('review_service', SCRIPTS / 'review_service.py')
service = importlib.util.module_from_spec(spec)
spec.loader.exec_module(service)

FAKE = '''#!/usr/bin/env python3
import json, subprocess, sys, time
from pathlib import Path
root = Path(__file__).parent
args = sys.argv[1:]
with (root / 'calls').open('a') as output:
    output.write(json.dumps(args) + '\\n')
settings = json.loads((root / 'settings').read_text())
if settings.get('helper'):
    child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(10)'])
    with (root / 'helpers').open('a') as output: output.write(str(child.pid) + '\\n')
if settings.get('hang'): time.sleep(2)
if settings.get('error'):
    print('TEST_SECRET manager rejected', file=sys.stderr)
    sys.exit(1)
if args[1] == 'stop':
    if settings.get('stop_error'): sys.exit(1)
    if not settings.get('survivor'):
        Path(settings['events']).write_text('populated 0\\n')
    sys.exit(0)
if settings.get('malformed'):
    print('TEST_SECRET unstructured output')
else:
    for key, value in settings['state'].items(): print(key + '=' + value)
'''


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='delegate-service.')
        self.root = Path(self.temp.name).resolve()
        self.manager = self.root / 'systemctl'
        self.manager.write_text(FAKE)
        self.manager.chmod(0o700)
        self.boundary = service.ReviewService(manager=self.manager, cgroup_root=self.root / 'cgroups')
        self.boundary.cgroup_root.mkdir()
        self.group = self.boundary.cgroup_root / 'user.slice' / self.boundary.unit
        self.group.mkdir(parents=True)
        self.events = self.group / 'cgroup.events'
        self.events.write_text('populated 1\n')
        self.settings = {'events': str(self.events), 'state': {
            'Id': self.boundary.unit, 'LoadState': 'loaded', 'ActiveState': 'inactive',
            'SubState': 'dead', 'ControlGroup': '/user.slice/' + self.boundary.unit,
            'Result': 'success', 'ExecMainCode': '1', 'ExecMainStatus': '0'}}
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        (self.root / 'settings').write_text(json.dumps(self.settings))

    def calls(self):
        return [json.loads(line) for line in (self.root / 'calls').read_text().splitlines()]

    def test_success_requires_empty_owned_cgroup(self):
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['execution_status'], 'completed')
        self.assertEqual(result['cleanup'], 'confirmed')
        self.assertEqual(self.events.read_text(), 'populated 0\n')

    def test_survivor_prevents_success_even_when_main_exits_zero(self):
        self.settings['survivor'] = True
        self.save()
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['cleanup'], 'unverified')

    def test_wrapper_timeout_and_cancel_override_manager_success(self):
        for reason, expected in [('timeout', 'timed_out'), ('cancelled', 'cancelled')]:
            with self.subTest(reason=reason):
                result = self.boundary.finish(exit_code=0, reason=reason)
                self.assertEqual(result['execution_status'], expected)
                self.assertEqual(result['cleanup'], 'confirmed')

    def test_manager_runtime_timeout_is_not_a_clean_review(self):
        self.settings['state'].update(Result='timeout', ExecMainCode='2', ExecMainStatus='15')
        self.save()
        self.assertEqual(self.boundary.finish(exit_code=1)['execution_status'], 'timed_out')

    def test_nonzero_or_signal_exit_remains_failed(self):
        for code, status in [('1', '7'), ('2', '9')]:
            self.settings['state'].update(Result='exit-code', ExecMainCode=code, ExecMainStatus=status)
            self.save()
            self.assertEqual(self.boundary.finish(exit_code=0)['execution_status'], 'failed')

    def test_missing_or_malformed_manager_output_never_passes_or_leaks(self):
        for key in ('error', 'malformed'):
            self.settings[key] = True
            self.save()
            result = self.boundary.finish(exit_code=0)
            self.assertEqual(result['execution_status'], 'failed')
            self.assertEqual(result['cleanup'], 'unverified')
            self.assertNotIn('TEST_SECRET', json.dumps(result))
            self.settings.pop(key)

    def test_foreign_identity_and_traversal_cgroup_are_rejected(self):
        for updates in [{'Id': 'other.service'}, {'ControlGroup': '/../' + self.boundary.unit},
                        {'ControlGroup': '/user.slice/other.service'}]:
            original = self.settings['state'].copy()
            self.settings['state'].update(updates)
            self.save()
            self.assertEqual(self.boundary.finish(exit_code=0)['cleanup'], 'unverified')
            self.settings['state'] = original
        for args in self.calls():
            self.assertIn(self.boundary.unit, args)
            self.assertNotIn('other.service', args)

    def test_stop_failure_is_reported_and_not_retried(self):
        self.settings['stop_error'] = True
        self.save()
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['cleanup'], 'unverified')
        self.assertEqual(sum(args[1] == 'stop' for args in self.calls()), 1)

    def test_collected_unit_cannot_be_invented_as_success(self):
        self.settings['state'].update(LoadState='not-found', ControlGroup='')
        self.save()
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['cleanup'], 'unverified')

    def test_running_unit_cannot_confirm_termination(self):
        self.settings['state'].update(ActiveState='active', SubState='running')
        self.save()
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['execution_status'], 'failed')
        self.assertEqual(result['cleanup'], 'unverified')

    def test_manager_helper_cleanup_preserves_an_unrelated_session(self):
        self.settings['helper'] = True
        self.save()
        sentinel = subprocess.Popen([sys.executable, '-B', '-c', 'import time; time.sleep(10)'],
                                    start_new_session=True)
        try:
            self.boundary.finish(exit_code=0)
            for pid in (self.root / 'helpers').read_text().splitlines():
                deadline = time.monotonic() + 2
                while True:
                    state = subprocess.run(['/bin/ps', '-p', pid, '-o', 'stat='],
                                           capture_output=True, text=True, timeout=2).stdout.strip()
                    if not state or state.startswith('Z') or time.monotonic() >= deadline:
                        break
                    time.sleep(.025)
                self.assertTrue(not state or state.startswith('Z'), 'manager helper survived')
            self.assertIsNone(sentinel.poll(), 'unrelated session was killed')
        finally:
            sentinel.kill()
            sentinel.wait(timeout=2)

    def test_symlink_cgroup_events_cannot_prove_cleanup(self):
        target = self.root / 'forged.events'
        target.write_text('populated 0\n')
        self.events.unlink()
        self.events.symlink_to(target)
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['cleanup'], 'unverified')

    def test_manager_timeout_is_bounded_and_sanitized(self):
        self.settings['hang'] = True
        self.save()
        self.boundary.probe_timeout = .05
        result = self.boundary.finish(exit_code=0)
        self.assertEqual(result['cleanup'], 'unverified')
        self.assertIn('manager_timeout', result['diagnostics'])

    def test_command_fixes_lifetime_without_shell_or_parameter_expansion(self):
        args = self.boundary.command('/usr/bin/systemd-run', ['/usr/bin/true'], 10)
        self.assertIn('--property=RuntimeMaxSec=10s', args)
        self.assertIn('--property=KillMode=control-group', args)
        self.assertIn('--property=SendSIGKILL=yes', args)
        self.assertIn('--property=TimeoutStopSec=2s', args)
        self.assertIn('--expand-environment=no', args)
        self.assertEqual(args[-2:], ['--', '/usr/bin/true'])
        self.assertNotIn('--scope', args)
        for deadline in (0, True, 541):
            with self.assertRaises(ValueError):
                self.boundary.command('/usr/bin/systemd-run', ['/usr/bin/true'], deadline)
        with self.assertRaises(ValueError):
            self.boundary.command('/usr/bin/systemd-run', '/usr/bin/true', 10)

    def test_service_accepts_bounded_review_input_and_rejects_unsafe_init(self):
        launcher = self.root / 'systemd-run'
        control = self.root / 'control'; control.mkdir(mode=0o700)
        launcher.write_text('#!' + sys.executable + '\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n')
        launcher.chmod(0o700)
        wire = b'{"type":"system","subtype":"init","tools":["Read"],"mcp_servers":[]}\n'
        result = self.boundary.run(str(launcher), ['/usr/bin/true'], deadline=1,
            environment={'PATH': '/usr/bin:/bin'}, cwd=self.root, control=control,
            stdin=wire, expected_tools=['Read'])
        self.assertEqual(result['stdout'], wire)
        self.assertEqual(result['execution_status'], 'completed')
        result = self.boundary.run(str(launcher), ['/usr/bin/true'], deadline=1,
            environment={'PATH': '/usr/bin:/bin'}, cwd=self.root, control=control,
            stdin=wire.replace(b'Read', b'Bash'), expected_tools=['Read'])
        self.assertEqual(result['execution_status'], 'failed')
        self.assertIn('tool_boundary_unverified', result['diagnostics'])
        with self.assertRaises(ValueError):
            self.boundary.run(str(launcher), ['/usr/bin/true'], deadline=1,
                environment={'PATH': '/usr/bin:/bin'}, cwd=self.root, control=control,
                stdin=b'a' * (2 * 1024 * 1024 + 1))

    def test_cancel_before_init_keeps_cancelled_status(self):
        launcher = self.root / 'systemd-run'
        control = self.root / 'control'; control.mkdir(mode=0o700)
        marker = control / 'cancel'; marker.touch(mode=0o600)
        launcher.write_text('#!' + sys.executable + '\nimport time\ntime.sleep(10)\n')
        launcher.chmod(0o700)
        result = self.boundary.run(str(launcher), ['/usr/bin/true'], deadline=1,
            environment={'PATH': '/usr/bin:/bin'}, cwd=self.root, control=control,
            expected_tools=['Read'], cancel_marker=marker)
        self.assertEqual(result['execution_status'], 'cancelled')
        self.assertEqual(result['cleanup'], 'confirmed')
        self.assertIn('tool_boundary_unverified', result['diagnostics'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
