#!/usr/bin/env python3
"""Read `codex exec --json` event files; lines that are not JSON objects are skipped."""
import json
import re
import sys

UUID = re.compile(r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}')
MAX_COMMANDS = 200
MAX_COMMAND_CHARS = 1000
RECENT_EVENTS = 10
USAGE_FIELDS = (('input_tokens', 'inputTokens'), ('cached_input_tokens', 'cachedInputTokens'),
                ('cache_write_input_tokens', 'cacheWriteInputTokens'), ('output_tokens', 'outputTokens'),
                ('reasoning_output_tokens', 'reasoningOutputTokens'))


def events(path):
    try:
        with open(path, encoding='utf-8', errors='replace') as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if isinstance(event, dict):
                    yield event
    except OSError:
        return


def _item(event, kind):
    item = event.get('item')
    if event.get('type') == 'item.completed' and isinstance(item, dict) and item.get('type') == kind:
        return item
    return None


def session_id(path):
    for event in events(path):
        if event.get('type') == 'thread.started':
            value = event.get('thread_id')
            return value if isinstance(value, str) and UUID.fullmatch(value) else None
    return None


def commands(path):
    """(commands, truncated): completed command items without their output."""
    found, truncated = [], False
    for event in events(path):
        item = _item(event, 'command_execution')
        if item is None:
            continue
        if len(found) == MAX_COMMANDS:
            truncated = True
            continue
        command = str(item.get('command', ''))
        if len(command) > MAX_COMMAND_CHARS:
            command, truncated = command[:MAX_COMMAND_CHARS], True
        found.append({'command': command, 'exitCode': item.get('exit_code'), 'status': item.get('status')})
    return found, truncated


def usage(path):
    """The last turn.completed usage; Codex reports it cumulatively for the whole session."""
    last = None
    for event in events(path):
        if event.get('type') == 'turn.completed' and isinstance(event.get('usage'), dict):
            last = event['usage']
    if last is None:
        return None
    return {name: last.get(key) if isinstance(last.get(key), int) else None for key, name in USAGE_FIELDS}


def render_recent(path, limit=RECENT_EVENTS):
    lines = []
    for event in events(path):
        command = _item(event, 'command_execution')
        error = _item(event, 'error')
        if command is not None:
            lines.append('命令 %s 退出 %s' % (str(command.get('command', ''))[:MAX_COMMAND_CHARS], command.get('exit_code')))
        elif error is not None:
            lines.append('错误 %s' % error.get('message', ''))
        elif event.get('type') == 'error':
            lines.append('错误 %s' % event.get('message', ''))
    return lines[-limit:]


def main(arguments):
    if len(arguments) == 2 and arguments[0] == 'session':
        print(session_id(arguments[1]) or '')
        return 0
    if len(arguments) == 2 and arguments[0] == 'render':
        print('\n'.join(render_recent(arguments[1])))
        return 0
    print('delegate: run_events usage error', file=sys.stderr)
    return 64


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
