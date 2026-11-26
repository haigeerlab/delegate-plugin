#!/usr/bin/env python3
"""Run suites in parallel and replay their byte streams in input order.

Stdin contains NUL-terminated fields for each suite: label, failure message,
argument count, then that many argv fields. Empty arguments are preserved.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(64, '%s: error: %s\n' % (self.prog, message))


def positive_integer(value):
    if not value.isascii() or not value.isdecimal() or int(value) < 1:
        raise ValueError('expected a positive integer')
    return int(value)


def read_suites(data):
    if not data:
        return []
    if not data.endswith(b'\0'):
        raise ValueError('suite fields must be NUL-terminated')
    fields = [os.fsdecode(field) for field in data[:-1].split(b'\0')]
    suites = []
    position = 0
    while position < len(fields):
        if len(fields) - position < 3:
            raise ValueError('incomplete suite header')
        label, failure, count = fields[position:position + 3]
        count = positive_integer(count)
        position += 3
        if not label or not failure or len(fields) - position < count:
            raise ValueError('incomplete suite entry')
        suites.append((label, failure, fields[position:position + count]))
        position += count
    return suites


def word_pattern(name):
    return re.compile(r'(?<![A-Za-z0-9_])' + re.escape(name) + r'(?![A-Za-z0-9_])')


def select_suites(changed_paths, suites, read_source):
    """Select labels from a label -> root-relative script path mapping.

    read_source(path) supplies source text. Return None for all suites, or an
    ordered list of labels, together with human-readable selection reasons.
    """
    paths = sorted(set(changed_paths))
    if not paths:
        return [], ['no changes against origin/main']
    selected = {label: [] for label in suites}
    sources = {}
    for path in paths:
        if path in ('scripts/validate.sh', 'scripts/run_suites.py') or path.startswith('.github/'):
            return None, [path]
        matches = [label for label, script in suites.items() if script == path]
        if not matches and (path.startswith(('docs/', 'spec/', 'tasks/'))
                            or ('/' not in path and path.endswith('.md'))):
            continue
        # Suite files are loaded by other suites too, so name matching applies to them as well.
        basename = os.path.basename(path)
        stem, suffix = os.path.splitext(basename)
        patterns = [word_pattern(name) for name in {stem, basename}]
        directory = os.path.basename(os.path.dirname(path))
        # Suites that read a whole directory, e.g. (PLUGIN / 'scripts').glob('*.py').
        globs = []
        if directory and suffix:
            globs = [re.compile(r"\.glob\(\s*['\"]\*" + re.escape(suffix) + r"['\"]"),
                     re.compile(word_pattern(directory).pattern, re.I)]
        for label, script in suites.items():
            if label in matches:
                continue
            if script not in sources:
                sources[script] = read_source(script)
            source = sources[script]
            if any(pattern.search(source) for pattern in patterns) or \
                    (globs and all(pattern.search(source) for pattern in globs)):
                matches.append(label)
        if not matches:
            return None, ['no suite matches ' + path]
        for label in matches:
            selected[label].append(path)
    labels = [label for label, paths in selected.items() if paths]
    return labels, [label + ': ' + ', '.join(selected[label]) for label in labels]


def expand_dependents(changed_paths, product_sources):
    """Add product files that use a changed product file, transitively.

    product_sources maps root-relative product script paths to their text.
    Suites often import a module that imports the changed one, so matching
    the changed name alone would miss them. Return the sorted expanded paths
    and notes naming the file each addition uses.
    """
    expanded = set(changed_paths)
    notes = []
    # Deleted files are not in product_sources but still break the files that use them.
    product_dirs = {os.path.dirname(path) for path in product_sources}
    pending = sorted(path for path in expanded if os.path.dirname(path) in product_dirs)
    while pending:
        used = pending.pop(0)
        pattern = word_pattern(os.path.splitext(os.path.basename(used))[0])
        for path in sorted(product_sources):
            if path not in expanded and pattern.search(product_sources[path]):
                expanded.add(path)
                notes.append('%s (uses %s)' % (path, used))
                pending.append(path)
    return sorted(expanded), notes


def git_changed_paths(root):
    """Return tracked and untracked changes, or None when Git cannot compare."""
    def git(*args):
        return subprocess.run(['git', '-C', str(root), *args], check=True,
                              capture_output=True).stdout

    try:
        base = git('merge-base', 'HEAD', 'origin/main').strip()
        if not base:
            return None
        changed = git('diff', '--name-only', '--no-renames', '-z', os.fsdecode(base), '--')
        untracked = git('ls-files', '--others', '--exclude-standard', '-z')
    except (OSError, subprocess.CalledProcessError):
        return None
    return [os.fsdecode(path) for path in (changed + untracked).split(b'\0') if path]


def quick_selection(root, suites):
    paths = git_changed_paths(root)
    if paths is None:
        return None, ['no merge base with origin/main']
    scripts = {}
    for label, _, argv in suites:
        script = next((arg for arg in argv if arg.endswith(('.py', '.sh'))), None)
        if script is None:
            return None, ['cannot identify suite script: ' + label]
        scripts[label] = os.path.relpath(script, root)
    try:
        product = {}
        for script_dir in sorted(Path(root).glob('plugins/*/scripts')):
            for script in sorted(script_dir.iterdir()):
                if script.suffix in ('.py', '.sh') and script.is_file():
                    product[os.path.relpath(script, root)] = script.read_text(encoding='utf-8')
        paths, notes = expand_dependents(paths, product)
        selected, reasons = select_suites(paths, scripts,
                                          lambda path: (Path(root) / path).read_text(encoding='utf-8'))
    except (OSError, UnicodeError) as error:
        return None, ['cannot read suite source: ' + str(error)]
    if selected is None:
        return None, reasons
    return selected, ['counts ' + note for note in notes] + reasons


def run_suite(suite):
    started = time.monotonic()
    directory = tempfile.mkdtemp(prefix='delegate-suite.')
    try:
        # An empty private config home keeps suites away from the user's ~/.config/delegate.
        config_home = os.path.join(directory, 'config-home')
        os.mkdir(config_home)
        environment = dict(os.environ, TMPDIR=directory, XDG_CONFIG_HOME=config_home)
        try:
            result = subprocess.run(suite[2], stdin=subprocess.DEVNULL,
                                    capture_output=True, env=environment)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except OSError as error:
            code, stdout, stderr = 1, b'', (str(error) + '\n').encode('utf-8', 'replace')
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    return code, stdout, stderr, time.monotonic() - started


def main():
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument('--jobs', type=positive_integer, default=os.cpu_count() or 1,
                        metavar='N', help='maximum concurrent suites (default: CPU count)')
    parser.add_argument('--quick', action='store_true', help='run suites related to changed files')
    parser.add_argument('--root', default=os.getcwd(), help='repository root for quick selection')
    options = parser.parse_args()
    try:
        suites = read_suites(sys.stdin.buffer.read())
    except ValueError as error:
        parser.error(str(error))

    if options.quick:
        selected, reasons = quick_selection(options.root, suites)
        if selected is None:
            report = ['running all suites (%s)' % '; '.join(reasons)]
        else:
            report = ['%d of %d suites' % (len(selected), len(suites)), *reasons]
            suites = [suite for suite in suites if suite[0] in selected]
        for line in report:
            sys.stderr.buffer.write(('validate: quick: ' + line + '\n').encode('utf-8', 'replace'))
        sys.stderr.buffer.flush()

    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=options.jobs) as pool:
        results = list(pool.map(run_suite, suites))
    elapsed = time.monotonic() - started

    failed = False
    for suite, (code, stdout, stderr, _) in zip(suites, results):
        sys.stdout.buffer.write(stdout)
        sys.stderr.buffer.write(stderr)
        if code != 0:
            failed = True
            sys.stderr.buffer.write(('validate: %s\n' % suite[1]).encode('utf-8'))
        # Flush per suite so a merged log (2>&1) keeps each suite's lines together.
        sys.stdout.buffer.flush()
        sys.stderr.buffer.flush()
    sys.stderr.buffer.write(b'validate: slowest suites:\n')
    slowest = sorted(zip(suites, results), key=lambda item: item[1][3], reverse=True)[:5]
    for suite, result in slowest:
        sys.stderr.buffer.write(('validate:   %s: %.1fs\n' % (suite[0], result[3])).encode('utf-8'))
    sys.stderr.buffer.write(('validate: pool wall-clock: %.1fs\n' % elapsed).encode('ascii'))
    sys.stderr.buffer.flush()
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
