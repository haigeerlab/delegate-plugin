# Spec: channel（委托通道）

> 能力图见 [`capability-map.md`](capability-map.md)。本模块是构建顺序的第一个，无依赖。

## Objective

把一个**已经决策完毕**的任务安全地送到 Codex 执行，把结论安全地带回来，
并且**不让过程输出进入调用方的上下文**。

用户是 Claude 额度紧张的个人开发者。成功的样子：Claude 主会话花几百字节，
换到 Codex 那边几十到几百 KB 的读文件、改文件、跑测试。

**本模块刻意不认识「什么活该派」** —— 那是 `routing` 的事。channel 只做搬运和边界。

### 为什么不是一行 `codex exec`

2026-08-29 实测，裸接会以四种方式失败，每种都静默或反效果：

| 失败 | 表现 | 对策 |
|---|---|---|
| 平台二进制缺失 | `command -v codex` **为真**，真跑炸在 Node 栈里 | 用 `codex --version` 实探 |
| 非 TTY 的 stdin | `codex exec` 等输入，**永久挂起**（实测撞 5 分钟超时） | `</dev/null` |
| 过程输出未隔离 | 全进调用方上下文，**价值反转成倒贴**（实测 19,939 B vs 170 B 最终答复） | `-o` + stdout 重定向到日志文件 |
| `~/.codex/AGENTS.md` 的流程编排规则 | 停在「请确认后我执行」，`git status` 是空的 | 前置非交互声明 |

## Tech Stack

- `bash`（必须兼容 macOS 自带的 **3.2**）+ `python3` 兜底
- `codex` CLI（`@openai/codex`，实测基线 0.150.1）
- **不引入** `jq` / `node` / 任何 npm 依赖

## Commands

```bash
# 全量校验（结构 + 语法 + bash 3.2 兼容 + 各校验器自检）
/bin/bash scripts/validate.sh
scripts/check-manifests.py                  ← 清单必填字段（只查 JSON 语法会放行装不上的清单）

# 本模块测试套（默认全部走 codex 桩，免费、确定性）
/bin/bash plugins/delegate/tests/test-channel.sh

# 真跑冒烟（会花 Codex 额度，不进 validate）
/bin/bash plugins/delegate/tests/test-channel.sh --live

# 手动调用
plugins/delegate/scripts/codex-exec.sh [--write] [--model <slug>] [--effort <level>] "<任务>"
```

## Project Structure

```
capability-map.md                        ← 能力图（已批准）
SPEC-channel.md                          ← 本文件
.claude-plugin/marketplace.json          ← 独立 marketplace，不并进 spec-guard
plugins/delegate/
├── .claude-plugin/plugin.json
├── commands/delegate.md                 ← /delegate 斜杠命令
├── scripts/codex-exec.sh                ← 本模块的全部实现
└── tests/
    ├── test-channel.sh                  ← 断言套（正反并重）
    └── stub-codex                       ← codex 桩，测试默认用它
scripts/validate.sh
```

## Code Style

调用形态是本模块的核心，四个元素**一个都不能省**：

```bash
env -u OPENAI_API_KEY codex exec \
  --ephemeral --sandbox "${SANDBOX}" --color never \
  ${EXTRA[@]+"${EXTRA[@]}"} \
  -o "${ANSWER}" -- "${PREAMBLE}

${TASK}" >"${LOG}" 2>&1 </dev/null
```

- `env -u OPENAI_API_KEY` —— 强制走 ChatGPT 订阅额度。留着 API key 就变成按量计费，
  「另一个额度池」这个前提当场消失
- `</dev/null` —— 否则永久挂起
- `-o` + `>"${LOG}"` —— 过程输出落盘，只有最终答复回到调用方
- `${PREAMBLE}` —— 非交互声明。全局 `~/.codex/AGENTS.md` **没有按调用关闭的开关**
  （实测：`-c project_doc_max_bytes=0` 只关项目级；`experimental_instructions_file`
  在 0.150.1 已不存在），只能压

约定：
- 变量一律 `${VAR}`，不写 `$VAR` —— bash 3.2 会把多字节字符首字节吃进变量名
- 空数组展开一律 `${ARR[@]+"${ARR[@]}"}` —— bash 3.2 下空数组配 `set -u` 致命退出
- 不写 `cmd | grep -q` —— `grep -q` 命中即关管道，`pipefail` 把 SIGPIPE(141) 传出来

## Testing Strategy

`bash` 断言套（**必须 `/bin/bash` 跑** —— zsh 的 MULTIOS 会把多个输入重定向拼接而不是后者覆盖，在 zsh 下写断言 2 会得出相反结论），与 spec-guard 同构（PASS/FAIL 计数 + 末行总计）。

**默认全部走 `stub-codex` 桩** —— 免费、确定性、不打网络。桩通过环境变量控制行为：
返回什么最终答复、退出码几、是否在 stdout 吐大量过程文本。

**反向用例和正向一样重要。** 每条判据至少一正一反。

`--live` 那一组真调 Codex，只做冒烟（能通、答复非空、日志/答复体量比合理），
不进 `validate.sh`。

必须覆盖的断言（每条都对应今天实测到的一种失败）：

| # | 用例 | 期望 |
|---|---|---|
| 1 | 桩在 stdout 吐 100KB | 调用方拿到的 stdout **不含**那 100KB |
| 2a | `STUB_READ_STDIN=1`、stdin 是永不关闭的管道、**不加** `</dev/null` | **阻塞**（先证明测法能复现真故障） |
| 2b | 同上但**加** `</dev/null` | 限时内完成 |
| 3 | `codex` 存在但 `--version` 失败 | 退出 **127** + 给出修复命令 |
| 4 | `codex` 不在 PATH | 退出 127 |
| 5 | 桩退出非 0 | 脚本退出非 0，日志尾部回显 |
| 6 | 桩退出 0 但答复文件为空 | 退出非 0（**不许把空当成成功**） |
| 7 | `--model` 传了无效 slug（桩模拟 400） | 退出非 0，**不静默退回默认** |
| 8 | `--model X --effort high` | 桩收到 `-m X` 和 `-c model_reasoning_effort="high"` |
| 9 | 不传 model | 桩**没有**收到 `-m` |
| 10 | 默认模式 | 桩收到 `--sandbox read-only` |
| 11 | `--write` | 桩收到 `--sandbox workspace-write` |
| 12 | `--write` 在 git 仓库里 | 输出含基线 HEAD + `git status --short` + `git diff --stat` |
| 13 | `--write` 在**非** git 目录 | 输出明说拿不到 diff，不伪造验收 |
| 14 | `--write` 跑前工作区已有 N 个未提交变更 | 验收块把 N 报出来 |
| 15 | 未知选项 / 空任务 | 退出 **64** |
| 16 | 任务文本以 `-` 开头 | 不被当成选项（`--` 终止符） |

## Boundaries

**Always**
- 改调用形态就跑 `test-channel.sh`
- 新增判据同时加正反用例
- 探测/执行失败时**说清楚失败了**，不发绿灯

**Ask first**
- 增加任何外部依赖
- 改沙箱默认值
- 新增 flag

**Never**
- 默认可写（`--write` 必须显式）
- 把过程日志 `cat` 回上下文
- 用 `command -v` 当可用性判据
- 无效模型 slug 静默退回默认
- 在非 git 目录伪造验收块

## Success Criteria

1. 19 条断言全绿，`validate.sh` 通过
2. 单次委托回到调用方 stdout 的体量 **≤ 过程日志的 1/40**（今日实测区间 63×–340×）
3. 从 Claude Code 的 Bash 工具里调用**不挂起**
4. 只读模式下 Codex 无法写入 cwd；写模式下无法写入 cwd 之外（实测已验证沙箱边界）
5. `--write` 的输出**必然**含 git 验收块，且内容与 `git status` 实际一致
6. 任何失败路径的退出码都非 0，且 stderr 有可执行的下一步

## Open Questions

- **日志目录无限增长。** `$TMPDIR/delegate-codex/` 今天一轮就堆了 10+ 个文件。
  自动清理（保留 N 天 / N 个）还是完全不管？倾向保留最近 50 个，但没定。
- **wrapper 自身要不要设超时上限？** 现在完全交给调用方。Claude 的 Bash 默认 120s
  会打断，命令文档里写了要设 600000 —— 但那是靠模型记得。
- **`--effort` 的合法值不校验，直接透传。** 传错由 codex 报错。要不要在本地拦一层？
