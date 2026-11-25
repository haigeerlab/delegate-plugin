#!/usr/bin/env python3
"""Validate bounded startup events for the trusted supervisor."""
import json
import re

from claude_review import unique_object


class ResultError(Exception):
    pass


def init_error(event, tools):
    # Fixed codes only: startup events can contain paths, credentials or data.
    if not isinstance(event, dict) or event.get('type') != 'system' or event.get('subtype') != 'init':
        return 'initial_event_not_init'
    actual = event.get('tools')
    if (not isinstance(actual, list) or not all(isinstance(tool, str) for tool in actual)
            or len(actual) != len(set(actual))):
        return 'initial_tools_invalid'
    # --tools cannot remove EndConversation. It only ends the session, while
    # StructuredOutput supplies the requested schema; neither grants IO access.
    if set(actual) - {'StructuredOutput', 'EndConversation'} != set(tools):
        return 'initial_tools_mismatch'
    if event.get('mcp_servers') != []:
        return 'initial_mcp_unverified'
    return None


def init_valid(event, tools):
    return init_error(event, tools) is None


def read_init(stream, tools, *, complete=False):
    """Bound startup metadata without trusting arbitrary pre-init events."""
    consumed, redraws = 0, 0
    for line in stream[:65537].splitlines(keepends=True):
        consumed += len(line)
        if consumed > 65536:
            raise ResultError('initial_output_oversized')
        if not line.endswith(b'\n') and not complete:
            return None
        try:
            event = json.loads(line, object_pairs_hook=unique_object)
        except (ValueError, UnicodeError):
            raise ResultError('initial_output_invalid') from None
        if isinstance(event, dict) and event.get('type') == 'system' and event.get('subtype') == 'init':
            error = init_error(event, tools)
            if error:
                raise ResultError(error)
            return event
        # Original 2.1.296 emits this passive repaint before init. No hook,
        # plugin, model, control request or unknown payload gets this exception.
        if (not isinstance(event, dict) or event.get('type') != 'system'
                or event.get('subtype') != 'ui_invalidate' or event.get('event') != 'ui.render'
                or set(event) - {'type', 'subtype', 'event', 'uuid', 'session_id'}
                or any(not isinstance(event[key], str) or not re.fullmatch(
                    r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', event[key])
                    for key in ('uuid', 'session_id') if key in event)):
            raise ResultError('initial_event_not_init')
        redraws += 1
        if redraws > 8:
            raise ResultError('initial_prefix_limit')
    if complete:
        raise ResultError('initial_event_not_init' if redraws else 'initial_output_empty')
    return None
