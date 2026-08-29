# Spec: detection（后端可用性探测与降级）

> 能力图见 [`capability-map.md`](capability-map.md)。无依赖，与 [`channel`](SPEC-channel.md) 并列。

## Objective

让「Codex 现在能不能用」成为一个**可靠、便宜、且绝不误报**的事实，供 `routing`
决定要不要提议委托；并在接入有问题时给出**可执行的下一步**。

**本模块不调用 Codex，也不决定什么活该派。** 它只回答一个问题：现在派得出去吗。

### 三条不可违反的性质（继承自 spec-guard）

1. **默认不生效** —— 没装 Codex 的机器上，hook 必须静默退 0、零输出、零报错。
   装了这个插件不能给任何项目添乱。
2. **探测失败就降级，不误报** —— 探不出来一律当「不可用」，静默退回默认执行器。
   **绝不因为探测本身出错而阻塞、报警或注入噪音。**
3. **不越权** —— 只注入事实。「要不要派」是 `routing` 的建议，「派不派」是用户的决定。

## Tech Stack

`bash`（兼容 macOS 自带 3.2）+ `python3` 兜底。**不引入** `jq` / `node` / 任何 npm 依赖。

## Commands

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-detection.sh

# 手动看探测结果
/bin/bash plugins/delegate/hooks/detect.sh --print

# 接入体检（斜杠命令 /delegate:doctor 背后的脚本）
/bin/bash plugins/delegate/hooks/doctor.sh
```

## Project Structure

```
plugins/delegate/
├── hooks/
│   ├── hooks.json              ← SessionStart + UserPromptSubmit 注册
│   ├── detect.sh               ← 三级探测 + 缓存；两个事件共用
│   └── doctor.sh               ← 接入体检（按需跑，不在每轮路径上）
├── commands/
│   ├── delegate.md             ← channel 的
│   └── doctor.md               ← /delegate:doctor
└── tests/
    ├── test-detection.sh
    └── stub-codex              ← 与 channel 共用
```

## Code Style

**三级阶梯，顺序是事故换来的**（2026-08-29 实测）：

```bash
# 1) 通道脚本在不在
[ -x "${WRAPPER}" ] || unavailable "wrapper 缺失或不可执行"

# 2) codex 真的跑得起来 —— 绝不能只用 command -v。
#    实测踩过：npm 漏装平台可选依赖时 command -v 为真、二进制却是缺的，
#    守卫放行后炸在 Node 栈里。
command -v codex >/dev/null 2>&1 || unavailable "codex 不在 PATH"
codex --version >/dev/null 2>&1  || unavailable "codex 装坏了：npm install -g @openai/codex@latest"

# 3) 登录过没有
[ -s "${CODEX_AUTH_FILE:-${HOME}/.codex/auth.json}" ] || unavailable "未登录：跑一次 codex 交互式登录"
```

hook 的输出**必须是合法 JSON**，格式与 spec-guard 一致：

```json
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"..."}}
```

非 JSON 会被宿主拒绝，**而且失败是静默的** —— 这是最难发现的一类故障。

其余约定同 `channel`：`${VAR}` 写法、空数组 `${ARR[@]+"${ARR[@]}"}`、不写 `cmd | grep -q`。

## 缓存

- `SessionStart` 探一次，结果写 `${TMPDIR}/delegate/detection.json`（含 `checkedAt`）。
- `UserPromptSubmit` 只读该文件。**读文件 < 1ms，冷探测实测 40–90ms。**
- 文件缺失、损坏、或超过 8 小时 → 重探。不因为缓存坏了就报错。
- **缓存写在 `${TMPDIR}` 下，不写进用户项目**（性质 1）。

## Testing Strategy

`bash` 断言套（**必须 `/bin/bash` 跑**），默认走 `stub-codex`，正反并重。

**查参数内容一律先 `eval` 还原再 `case` 比对**，绝不直接 grep 中文 ——
bash 3.2 的 `printf %q` 把 UTF-8 打成八进制转义，直接 grep 是恒真的空断言
（`channel` 实测踩过，一个本该被抓的变异存活）。

| # | 用例 | 期望 |
|---|---|---|
| 1 | 三级全过 | 可用 |
| 2 | wrapper 不可执行 | 不可用，原因指向 wrapper |
| 3 | `codex` 不在 PATH | 不可用 |
| 4 | **`codex` 在 PATH 但 `--version` 失败** | **不可用**，提示含 `npm install -g @openai/codex@latest` |
| 5 | `auth.json` 不存在 | 不可用，提示去登录 |
| 6 | `auth.json` 存在但为空 | 不可用 |
| 7 | 缓存新鲜 | **不再调用 codex**（调用日志为空） |
| 7b | `--session-start` 且缓存新鲜 | **仍然实探** —— 它的职责是预热；否则装好 Codex 后重启也要等缓存过期才被发现 |
| 8 | 缓存超过 8 小时 | 重探（调用日志有一次） |
| 9 | 缓存文件是非法 JSON | 重探，不崩 |
| 10 | 没有 codex 的机器上跑 hook | **退出 0、零输出**（性质 1） |
| 10b | SessionStart 模式（`--session-start`）即使后端可用 | **零输出** —— 两个事件共用一个脚本，而 `hookEventName` 必须与实际事件一致；SessionStart 的输出契约没有可核对依据，**不猜**，那一路只探测 |
| 11 | 任何情况下 hook 的 stdout | 要么为空，要么是能被 `json.load` 解析的合法 JSON |
| 12a | 缓存目录存在但不可写（写文件失败） | 仍退出 0，契约不破 |
| 12b | 缓存目录**建都建不出来**（父目录不可写） | 仍退出 0 —— 只做 12a 时 `mkdir -p` 对已存在目录是成功的，这条路径从没被走到，变异存活过 |
| 13 | doctor：`~/.codex/AGENTS.md` 含「等确认 / 不要直接开始改代码」 | 报告该风险并给出修法 |
| 14 | doctor：AGENTS.md 干净 | **不报**（反向） |
| 15 | doctor：没有 `~/.codex/AGENTS.md` | 不报错 |

用例 13 有实测依据：`~/.codex/AGENTS.md` 里的流程编排规则会让 `codex exec`
停在「请确认后我执行」而什么都不做，且**没有按调用关闭它的开关**
（`project_doc_max_bytes=0` 只关项目级；`experimental_instructions_file` 在
0.150.1 已不存在）。

## Boundaries

**Always**
- 探不出来一律当「不可用」，静默降级
- hook 输出要么为空、要么是合法 JSON
- 缓存写在 `${TMPDIR}`

**Ask first**
- 增加探测层级（每一级都在每轮路径上，要付时间）
- 改缓存 TTL
- 让 hook 读用户项目以外的任何文件

**Never**
- 单用 `command -v` 当可用性判据
- 探测失败时报警、阻塞、或注入噪音
- **在每轮 hook 里读用户的 `~/.codex/AGENTS.md`** —— 那是 `doctor` 的活，
  按需跑；放进每轮路径既费时间又越权
- 往用户项目里写任何文件

## Success Criteria

1. 18 条断言全绿，`validate.sh` 通过
2. 缓存命中时每轮开销 **< 5ms**；冷探测 **< 200ms**（实测 `codex --version` 40–90ms）
3. 没装 Codex 的机器上：hook 静默退 0、零输出、零报错
4. 探测脚本任何内部错误都不产生非零退出、也不产生非 JSON 输出
5. 三级阶梯每一级都能被单独复现地测到，尤其第 2 级的「`command -v` 为真但跑不起来」

## Open Questions

- **缓存 TTL 定 8 小时是拍的。** 会话中途装好 Codex 要等到过期或重启才被发现。
  按需加一个 `/delegate:doctor` 之后主动刷新缓存？
- **`codex doctor` 是官方自带的诊断子命令**，和我们的 `doctor.sh` 关注点不同
  （它查安装/配置/认证，不查「委托是否会被 AGENTS.md 卡住」）。要不要在
  `doctor.sh` 里顺带调它并转述？
- **多机器 / 多账号**：`auth.json` 存在不代表 token 没过期。真正的可用性只有
  发一次请求才知道，但那要花额度。目前接受这个缺口。
