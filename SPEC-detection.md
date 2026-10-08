# 规格：detection（本地基础条件与诊断）

简体中文 | [English](docs/en/SPEC-detection.md)

当前合同：2026-10-08。早期 `tasks/detection/` 记录保留为历史。

## 目标与实现

提供近期本地基础条件供 routing 提议；异常静默降级，hook 不发模型请求、不写业务项目、不自行委托。基础“可用”只表示 CLI 可运行且报告 ChatGPT 登录，**不代表**远端连接、额度、模型权限或 token 必然有效。

- `backend.py`：PATH、版本命令、CLI 登录状态；与 channel 共用。
- `detect.py`：wrapper 可执行检查、缓存有效性、原子写入与输出合同。
- `detect.sh`：静默 shell 入口，兼容缺 Python 的降级。
- `doctor.sh`：强制刷新和按需中文全局 AGENTS.md 检查。

## 认证探测

不直接读取 `auth.json`，不以凭据文件存在或大小判登录。遵循 CLI 的 CODEX_HOME 与系统凭据存储。版本/登录探测各最多 5 秒，原始状态输出不写缓存、不回显凭据片段。只接受 CLI 明确报告的 ChatGPT 登录；API key、未知/失败状态按不可用处理。真实执行前再次检测。

旧 `CODEX_AUTH_FILE` 不再是产品认证覆盖接口；仅旧测试桩用它模拟 CLI 登录状态。

## 缓存合同

路径 `${TMPDIR:-/tmp}/delegate/detection.json`。字段：`available` 布尔、`reason` 安全字符串、`checkedAt` 时间、`identity` 对象。

identity 包含：实际 CLI 路径、有效 Codex home、插件根目录、插件清单版本。身份不同、字段类型不合法、旧格式、坏 JSON、未来时间或超过 8 小时都失效。

同目录临时文件（0600）写完后 `os.replace`，避免读到半个 JSON；缓存目录 0700，拒绝目录软链接。写入失败，hook 不注入可用事实并保持退出 0。CLI 路径与 home 不变时的账号切换/凭据过期不保证立即失效；doctor 强制刷新，执行始终实时探测。

## 入口与输出

- `--session-start`：强制探测写缓存，静默。
- `--warm`：命中缓存则复用，否则探测；静默。
- `--print`：强制探测，输出可用或安全的不可用原因；用于 doctor。即使缓存不可写，仍可报告当前直接探测结果。
- 默认：缓存可用时输出合法 UserPromptSubmit JSON，说明仅本地基础条件；不可用或内部异常零输出、退出 0。
- 实际 UserPromptSubmit 由 `prompt.sh` 串行 warm 后 route，避免并行 handler 竞争。

## doctor

每次直接刷新，检查 `${CODEX_AGENTS_FILE:-${CODEX_HOME:-$HOME/.codex}/AGENTS.md}`。`CODEX_AGENTS_FILE` 只覆盖诊断文件，不改变 Codex 实际加载规则。

中文启发式寻找等待确认/先出方案等规则及非交互豁免；结果不覆盖英文、全部全局/项目规则，豁免出现也不证明覆盖所有章节。打印诊断范围与问题数量，始终退出 0。只写临时缓存，不修改业务文件或规则。

## 验证

以下命令从本仓库根目录运行：

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-detection.sh
python3 -B plugins/delegate/tests/test-backend.py
```

原有 19 条断言覆盖 wrapper/CLI/登录失败、缓存命中/失效、静默降级、合法 JSON 和 doctor。新增回归覆盖无需 auth.json 的 CLI 登录、API key/未知状态拒绝且不泄漏、登录失败、doctor 刷新旧缓存、home 身份变化、未来时间与冷启动串行输出。

成功标准：异常不产生错误注入；缓存命中不发 CLI 状态请求；doctor 刷新可重复验证；缓存原子完整且绑定身份。不再把未测量的 <5ms 当承诺；Python 启动、文件 I/O 与 CLI 探测会产生本机开销，真实性能需单独测量。
