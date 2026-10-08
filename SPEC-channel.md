# Spec: channel（委托通道）

当前合同：2026-10-08。早期 `tasks/channel/` 记录是历史，不覆盖本规格。

## 目标与边界

将一个已决策任务交给 Codex，隔离过程日志，返回最终答复与可核验的写模式 Git 概览。不负责分类、不可绕过的用户授权、结果正确性、远端登录有效性或发布。两种模式均要求 Git 工作区。

实现：`scripts/codex-exec.sh` 管理参数、日志和 Git；共用 `backend.py` 检查基础认证；`run_codex.py` 管理执行进程组。依赖 Bash 3.2、Python 3、Git、Codex CLI。

## 参数与预检

```bash
bash plugins/delegate/scripts/codex-exec.sh [--write] [--model <slug>] [--effort <level>] [--] "任务"
```

`--help/-h` 不调用 Codex。未知选项、缺参数、零或多个任务、非 Git 工作区退出 64。模型和推理档透传，不维护可能过期的本地白名单。

基础检查使用 PATH 查找 CLI、`codex --version` 与 `codex login status`；每项探测最多 5 秒。必须识别 ChatGPT 登录，API key/未知状态拒绝。运行前不信任 hook 缓存。CLI/依赖失败 127，认证失败非零；不回显可能含凭据的原始认证文本。

## 调用与生命周期

- 默认 sandbox=read-only；用户当前轮明确授权 `--write` 才用 workspace-write。
- 删除 `OPENAI_API_KEY` 和 `CODEX_API_KEY`，CLI 配置指定 `forced_login_method="chatgpt"`、`model_provider="openai"`。
- `--ephemeral`、无颜色、stdin=/dev/null，preamble 明确非交互任务与行为范围。
- `-o` 写最终答复，合并 stdout/stderr 写过程日志。
- Codex 开新进程组。期限默认/上限 540 秒；环境变量可缩短，非法或非正值回落默认。期限不包括前置探测和后置验收。
- 到期或 TERM/INT/HUP：TERM 进程组，最多等 2 秒，KILL 残余并回收直接子进程；正常退出也清理同组残余。
- 外部 Bash timeout=600000。超时退出 124；信号对应 143/130/129；其他执行失败保留状态，空答复退出 1。
- 自行脱离进程组的后代不在清理保证中；行为指令不是 OS 权限隔离。真实沙箱允许的 tmp/额外根以宿主配置为准。

## 写入与输出

允许已有未提交修改和尚无 HEAD 的 Git 仓库。启动前记录 HEAD 与已有变更数量。执行已开始的所有退出路径（成功、失败、超时、空答复、中断）输出：基线、status --short、diff --stat、diff --cached --stat。成功到 stdout，失败到 stderr。失败不会自动回滚；统计混有原有修改，须查看实际 diff。

成功只返回答复和元数据，答复无体积上限，不保证固定压缩率。过程文件在 `${TMPDIR:-/tmp}/delegate/`；目录 0700、新文件 0600，拒绝目录软链接。失败日志回显尾部最多 40 行/16KiB 与完整路径。每次完成后尽力保留最近 50 组日志与答复，清理失败不改执行状态；单个日志无体积上限。

## 验证与成功标准

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-channel.sh
python3 -B plugins/delegate/tests/test-channel-regressions.py
python3 -B plugins/delegate/tests/test-backend.py
```

原有 24 条断言验证参数、stdin、stdout 隔离、沙箱参数、日志清理、普通超时、Git 基线。回归验证忽略 TERM 的有界退出、后代不再写文件、wrapper 中断、失败/空答复/超时后的 Git 证据、100KB 单行错误的回显上限、非 Git 不执行、无 CLI 仍能 help。backend 回归验证认证拒绝、执行配置和缓存。

免费测试使用桩，只能验证调用参数与进程管理，不能证明真实 CLI 沙箱/付费模型行为。`test-channel.sh --live` 会消耗额度，不进入 validate；初轮离线修复未运行，后续真实验证见 [验收记录](docs/releases/v0.4.0.md)。改调用形态必须跑总验证，修改行为先用回归复现故障。新增后端、flag、沙箱默认或非 Git 支持需另定范围。
