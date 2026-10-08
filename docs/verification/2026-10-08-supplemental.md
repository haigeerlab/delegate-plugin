# 免费离线定向补验

日期：2026-10-08；源码基准：`56c3ba76f1059f929bc908c0e45469abc623859a`。

只执行临时夹具中的受控桩，无真实 Codex/Claude 模型调用；HOME/CODEX_HOME/TMPDIR 隔离，产品源码/测试/清单不改。机器记录见 [results JSON](2026-10-08-supplemental-results.json)，工具原文见 [supplemental-check.py.txt](supplemental-check.py.txt)。工具原文是本次证据，不是新增永久回归套。

## 运行和结果

`python3 -B <LOCAL_TMP>/delegate-supplemental-check.py` 最终退出 0：26 通过、0 失败。需要重现时先将工具原文复制到临时 `.py`，从仓库根用 Python 3 的 `-B` 执行；不运行付费样本。工具会创建并清理自己的临时夹具。

首轮 23 通过、3 项未取得结论：INT 夹具在 3 秒启动窗口内未就绪；HUP/正常退出观察使用的 `/bin/ps` 被沙箱拒绝。之后将启动窗口改为 8 秒，用后代 15 秒后的延迟写入标记和 16 秒观察窗口代替 ps，三项均通过。原产品未改，这不是修复了三个产品缺陷。

| 检查 | 结果 | 样本范围 |
|---|---|---|
| SUP-01-wrapper-INT | 通过 | 同组后代延迟写标记未出现；16 秒观察，非所有调度/竞态证明 |
| SUP-02-wrapper-HUP | 通过 | 同组后代延迟写标记未出现；16 秒观察，非所有调度/竞态证明 |
| SUP-03-normal-exit-cleanup | 通过 | 同组后代延迟写标记未出现；16 秒观察，非所有调度/竞态证明 |
| SUP-04-log-permissions | 通过 | 受控单次样本 |
| SUP-05-log-symlink | 通过 | 受控单次样本 |
| SUP-06-git-without-HEAD | 通过 | 受控单次样本 |
| SUP-07-cache-permissions | 通过 | 受控单次样本 |
| SUP-08-cache-symlink | 通过 | 受控单次样本 |
| SUP-09-available-integer | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-10-available-string | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-11-reason-integer | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-12-time-boolean | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-13-time-null | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-14-time-string | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-15-time-nan | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-16-time-future | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-17-time-expired | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-18-missing-identity | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-19-identity-type | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-20-identity-codex | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-21-identity-codexHome | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-22-identity-pluginRoot | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-23-identity-pluginVersion | 通过 | 单个字段/身份分量反例，不穷举所有合法或非法值 |
| SUP-24-concurrent-cache | 通过 | 4 写线程、120 次写入、145 次读取；有限单进程线程样本 |
| SUP-25-propose-not-auto-scaffold | 通过 | 仅 --scaffold-only 验证 route JSON；不是 Claude Code 宿主加载或模型行为 |
| SUP-26-routing-fitness-scaffold | 通过 | 仅 --scaffold-only 验证 route JSON；不是 Claude Code 宿主加载或模型行为 |

## 能够收束和仍未验证的内容

- CH-03：新增当前快照的 INT/HUP 和正常结束同组残余的受控样本；永久回归仍没有这些独立用例，所有竞态和脱组进程不在本次结论中。
- CH-04/05：无 HEAD 的写模式概览、0700/0600 和日志软链接拒绝已在受控夹具验证。
- DET-02：字段类型、身份各分量、缓存权限/软链接及有限并发原子 JSON 观察已验证；不是跨进程压力或全部时间/文件系统故障覆盖。
- RT-04：两个免费 scaffold 实际退出 0；不据此宣称宿主/真实模型/互动提议验收完成。
- CH-02、RT-02/03：真实沙箱边界与完整宿主交互仍未验证。

当前源码、测试、eval 与清单对基准比较无差异；已有总测试结果继续引用首轮真实运行，本次只增加上述一次性证据。
