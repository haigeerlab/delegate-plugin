# 规格：channel（委托通道）

简体中文 | [English](../docs/en/SPEC-channel.md)

当前合同：2026-10-08。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。当前 `tasks/channel/` 只跟踪维护核对，不追认历史验收，也不覆盖本规格。


## 技术栈与命令

Bash 3.2 wrapper、Python 3 标准库、Git、Codex CLI；Claude Code 是产品命令宿主。CLI 版本随安装变化，运行时探测，不把版本号固定为未经验证的最低版本。
本产品为脚本插件，无独立编译构建或 dev server。下方原合同列出模块测试；仓库统一验证/开发加载如下，加载命令只启动宿主，不自行委托。

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
claude --plugin-dir "$PWD/plugins/delegate"
```

## 项目结构

路径均相对仓库根；插件内相对路径在原合同中说明。

```text
plugins/delegate/scripts/codex-exec.sh      → 参数、预检、日志与 Git 输出
plugins/delegate/scripts/backend.py         → channel/detection 共用基础认证
plugins/delegate/scripts/run_codex.py       → 进程组启动、期限与清理
plugins/delegate/tests/test-channel.sh      → Shell 桩断言
plugins/delegate/tests/test-channel-regressions.py → Python unittest 生命周期/Git 回归
plugins/delegate/tests/test-backend.py      → 共用认证/执行配置回归
spec/channel.md                            → 当前中文合同
docs/en/SPEC-channel.md                    → 当前英文合同
tasks/channel/plan.md / todo.md            → 当前维护步骤与记录
```

## 代码风格

保持已有风格，不做格式重构。Bash 兼容 3.2，变量用 `${VAR}`、数组展开按已有空数组守卫，不使用 `cmd | grep -q`；Python 使用标准库、4 空格缩进、snake_case 函数名，JSON 通过序列化器生成，不手工拼转义。
以下为 `plugins/delegate/scripts/backend.py` 的现有片段，展示实际写法（上下文片段，不是新命令）：

```python
    env = os.environ.copy()
    for key in ('OPENAI_API_KEY', 'CODEX_API_KEY'):
        env.pop(key, None)
```

## 开发边界

- **Always：** 修改前阅读合同；行为修复先复现再复验；保持 Bash 3.2 和双语合同同步；检查实际 diff 和相关测试。
- **Ask first：** 新后端/依赖/flag、沙箱默认或认证方法变更、超出现有模块的能力；付费 live、委托、提交和远端写入取得各自授权。
- **Never：** 暴露凭据/完整私密日志；削弱失败断言；自动回滚用户修改；追认历史审批或擅改归档；把桩结果当作完整宿主行为保证。

## 测试策略

Shell 产品套使用 `stub-codex` 和临时夹具；Python 回归使用标准库 `unittest`。测试位置见项目结构，原合同保留精确命令和断言范围。未设行覆盖率百分比，不虚构阈值。
验证按条款和风险判断，包含正反场景；源码中的保证若没有独立断言，映射明确标“部分覆盖”。真实模型、权限与交互验证单列，未经授权不运行付费样本。

## 目标与边界

将一个已决策任务交给 Codex，隔离过程日志，返回最终答复与可核验的写模式 Git 概览。不负责分类、不可绕过的用户授权、结果正确性、远端登录有效性或发布。两种模式均要求 Git 工作区。

实现文件位于 `plugins/delegate/` 下：`scripts/codex-exec.sh` 管理参数、日志和 Git；共用 `backend.py` 检查基础认证；`run_codex.py` 管理执行进程组。依赖 Bash 3.2、Python 3、Git、Codex CLI。

## 参数与预检

在业务 Git 工作区执行，把脚本路径替换为实际源码或安装位置：

```bash
bash /path/to/delegate-plugin/plugins/delegate/scripts/codex-exec.sh [--write] [--model <slug>] [--effort <level>] [--] "任务"
```

`--help/-h` 不调用 Codex。未知选项、缺参数、零或多个任务、非 Git 工作区退出 64。模型和推理档透传，不维护可能过期的本地白名单。

基础检查使用 PATH 查找 CLI、`codex --version` 与 `codex login status`；每项探测最多 5 秒。必须识别 ChatGPT 登录，API key/未知状态拒绝。运行前不信任 hook 缓存。CLI/依赖失败 127，认证失败非零；不回显可能含凭据的原始认证文本。

## 调用与生命周期

- 默认 sandbox=read-only；用户当前轮明确授权 `--write` 才用 workspace-write。
- 删除 `OPENAI_API_KEY` 和 `CODEX_API_KEY`，CLI 配置指定 `forced_login_method="chatgpt"`、`model_provider="openai"`。
- `--ephemeral`、无颜色、stdin=/dev/null，preamble 明确非交互任务与行为范围。
- `-o` 写最终答复，合并 stdout/stderr 写过程日志。
- Codex 开新进程组。期限默认/上限 540 秒；`DELEGATE_TIMEOUT_SECONDS` 可缩短，非法或非正值回落默认。期限不包括前置探测和后置验收。
- 到期或 TERM/INT/HUP：TERM 进程组，最多等 2 秒，KILL 残余并回收直接子进程；正常退出也清理同组残余。
- 外部 Bash timeout=600000。超时退出 124；信号对应 143/130/129；其他执行失败保留状态，空答复退出 1。
- 自行脱离进程组的后代不在清理保证中；行为指令不是 OS 权限隔离。真实沙箱允许的 tmp/额外根以宿主配置为准。

## 写入与输出

允许已有未提交修改和尚无 HEAD 的 Git 仓库。启动前记录 HEAD 与已有变更数量。执行已开始的所有退出路径（成功、失败、超时、空答复、中断）输出：基线、status --short、diff --stat、diff --cached --stat。成功到 stdout，失败到 stderr。失败不会自动回滚；统计混有原有修改，须查看实际 diff。

成功只返回答复和元数据，答复无体积上限，不保证固定压缩率。过程文件在 `${TMPDIR:-/tmp}/delegate/`；目录 0700、新文件 0600，拒绝目录软链接。失败日志回显尾部最多 40 行/16KiB 与完整路径。每次完成后尽力保留最近 50 组日志与答复，清理失败不改执行状态；单个日志无体积上限。

## 验证与成功标准

以下验证命令从本仓库根目录运行：

```bash
/bin/bash scripts/validate.sh
/bin/bash plugins/delegate/tests/test-channel.sh
python3 -B plugins/delegate/tests/test-channel-regressions.py
python3 -B plugins/delegate/tests/test-backend.py
```

原有 24 条断言验证参数、stdin、stdout 隔离、沙箱参数、日志清理、普通超时、Git 基线。回归验证忽略 TERM 的有界退出、后代不再写文件、wrapper 中断、失败/空答复/超时后的 Git 证据、100KB 单行错误的回显上限、非 Git 不执行、无 CLI 仍能 help。backend 回归验证认证拒绝、执行配置和缓存。

免费测试使用桩，只能验证调用参数与进程管理，不能证明真实 CLI 沙箱/付费模型行为。`test-channel.sh --live` 会消耗额度，不进入 validate；v0.4.0 的真实验证范围见 [验收记录](../docs/releases/v0.4.0.md)。改调用形态必须跑总验证，修改行为先用回归复现故障。新增后端、flag、沙箱默认或非 Git 支持需另定范围。

## 成功条件与验证映射

以下编号于 2026-10-08 为既有合同添加检索标识，不是历史编号或批准记录。

- **CH-01：** 参数与基础预检符合既有退出状态；help 不执行 CLI，未知/API key 登录拒绝且不回显凭据。
- **CH-02：** 默认只读、写入按授权传参，ChatGPT/OpenAI 配置及关闭 stdin 正确；桩不能证明真实沙箱权限。
- **CH-03：** 期限及信号遵循原生命周期合同，同组后代清理；脱离进程组的后代不在保证中。
- **CH-04：** 执行开始后的成功/失败/空答复/超时输出 Git 基线及变更概览，保留既有修改，不自动回滚。
- **CH-05：** 答复与过程日志隔离，日志尾部受限且保留策略不改变执行状态；权限、软链接按原日志合同。

精确测试、实现位置和覆盖缺口见 [条款到证据映射](../docs/verification/2026-10-08-contract-matrix.md)。当前维护计划 Task 5 负责核对该映射，不宣告全部产品条款已经充分验收。

## 开放问题

历史任务逐项验收、旧审批/插件版本及完整交互宿主行为仍未核实。当前已知覆盖缺口列在映射中；此处不新增能力或更强保证。
