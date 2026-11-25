#!/usr/bin/env python3
"""Choose the second reviewer (spec/reviewer-selection.md).

The choice is a pure function of the author host and model-free availability
checks passed in by the caller; it never starts a model or reads files.
A check returns None when its backend is usable, else a fixed diagnostic code,
or a tuple of fixed codes with the main code first (e.g. a probe failure and its stage).
"""

VENDORS = {'codex': 'openai', 'claude-code': 'anthropic'}


def order(author):
    """Candidate backends: the other vendor first, then a fresh same-vendor session."""
    if author not in VENDORS:
        raise ValueError('unknown author host')
    return [name for name in VENDORS if name != author] + [author]


def choose(author, checks):
    """Return (backend or None, selection, diagnostics of the vendors found unusable)."""
    diagnostics = []
    for position, name in enumerate(order(author)):
        problem = checks[name]()
        if problem is None:
            return name, 'cross_vendor' if position == 0 else 'same_vendor_fallback', diagnostics
        diagnostics.extend(problem if isinstance(problem, (tuple, list)) else [problem])
    return None, 'none', diagnostics


def describe(backend, author, selection):
    """The report's top-level `reviewer` object."""
    vendor = VENDORS.get(backend)
    same = None if vendor is None or author not in VENDORS else vendor == VENDORS[author]
    return {'vendor': vendor, 'backend': backend, 'same_vendor': same, 'selection': selection}


FIXTURE = 'DELEGATE_FIXTURE_REVIEWERS'
CODE = __import__('re').compile(r'[a-z][a-z0-9_]{0,79}\Z')


def codex_check():
    import backend
    status, _, diagnostic = backend.check_detailed()
    return None if status == 0 else (diagnostic if CODE.match(diagnostic or '') else 'codex_preflight_failed')


def claude_check():
    """Same model-free local checks as `review_doctor.py --backend claude-code`; only a fixed code leaves."""
    import shutil
    from pathlib import Path
    from claude_review import PreflightError, preflight
    from review_macos import BoundaryError
    from review_native import NativeRunner, native_temporary
    temporary = None
    retained = False
    try:
        context = {'repository': str(Path.cwd().resolve()), 'files': {}, 'file_sha256': {}, 'allowed_tools': ['Read']}
        temporary = native_temporary(context, 'delegate-reviewers.')
        runner = NativeRunner(temporary, context)
        runner.runtime_preflight()
        preflight(str(runner.claude), runner.invoke)
        return None
    except (BoundaryError, PreflightError) as error:
        code = str(error)
        retained = code in ('runtime_cleanup_unverified', 'probe_cleanup_unverified')
        if not CODE.match(code):
            return 'claude_preflight_failed'
        # Probe failures name the probe, as in the claude-code report (spec/claude-review.md CR-23).
        stage = getattr(error, 'stage', None)
        return (code, stage) if stage and CODE.match(stage) else code
    except (ValueError, OSError):
        return 'native_environment_unavailable'
    finally:
        if temporary is not None and not retained:
            shutil.rmtree(temporary, ignore_errors=True)


def real_checks():
    """Model-free availability checks; tests may pin results with DELEGATE_FIXTURE_REVIEWERS (JSON)."""
    import json
    import os
    pinned = os.environ.get(FIXTURE)
    if pinned is not None:
        values = json.loads(pinned)
        return {name: (lambda value=values.get(name, 'fixture_unavailable'): value) for name in VENDORS}
    return {'codex': codex_check, 'claude-code': claude_check}
