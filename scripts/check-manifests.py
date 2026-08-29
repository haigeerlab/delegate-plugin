#!/usr/bin/env python3
"""清单必填字段校验。

存在的理由：0.1.0 的 marketplace.json JSON 语法完全合法，却因为缺 owner
而装不上（`claude plugin marketplace add` 报 Invalid schema）。
只查语法的校验器放行了一份装不上的清单。
"""
import json
import os
import sys

root = sys.argv[1] if len(sys.argv) > 1 else "."
problems = []


def need(obj, key, where, kind=None):
    if key not in obj:
        problems.append("%s 缺字段 %s" % (where, key))
        return False
    if kind is not None and not isinstance(obj[key], kind):
        problems.append("%s 的 %s 类型不对" % (where, key))
        return False
    return True


mp = os.path.join(root, ".claude-plugin", "marketplace.json")
try:
    with open(mp) as fh:
        m = json.load(fh)
except Exception as exc:
    sys.stderr.write("manifest: 读不到 marketplace.json：%s\n" % exc)
    sys.exit(1)

need(m, "name", "marketplace.json", str)
if need(m, "owner", "marketplace.json", dict):
    need(m["owner"], "name", "marketplace.json owner", str)
if need(m, "plugins", "marketplace.json", list):
    for i, entry in enumerate(m["plugins"]):
        where = "marketplace.json plugins[%d]" % i
        need(entry, "name", where, str)
        if need(entry, "source", where, str):
            src = os.path.join(root, entry["source"], ".claude-plugin", "plugin.json")
            if not os.path.isfile(src):
                problems.append("%s 的 source 指向的 plugin.json 不存在" % where)
            else:
                with open(src) as fh:
                    pj = json.load(fh)
                for key in ("name", "version", "description"):
                    need(pj, key, entry["source"] + "/plugin.json", str)
                if pj.get("name") != entry.get("name"):
                    problems.append("%s 的 name 与 plugin.json 的 name 不一致" % where)

for line in problems:
    sys.stderr.write("manifest: %s\n" % line)
sys.exit(1 if problems else 0)
