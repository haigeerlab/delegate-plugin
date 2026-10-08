# 规格：detection（本地基础条件与诊断）

简体中文 | [English](../docs/en/SPEC-detection.md)

当前合同：2026-10-08。历史原文见 [归档索引](../docs/archive/pre-spec-guard/README.md)。当前 `tasks/detection/` 只跟踪维护核对，不追认历史验收，也不覆盖本规格。


## 技术栈与命令

Bash 3.2、Python 3 标准库、Git、Codex CLI；Claude Code 提供 hook/doctor 宿主。缓存绑定插件清单版本，CLI 可用性由实时探测或有限 TTL 判断。
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
plugins/delegate/hooks/detect.py            → 身份缓存、探测、原子写入
plugins/delegate/hooks/detect.sh            → Shell 静默入口
plugins/delegate/hooks/doctor.sh            → 刷新和规则诊断
plugins/delegate/scripts/backend.py        → 共用 CLI 基础认证
plugins/delegate/tests/test-detection.sh    → Shell 桩断言
plugins/delegate/tests/test-backend.py      → Python unittest 认证/身份/串行回归
spec/detection.md                            → 当前中文合同
docs/en/SPEC-detection.md                    → 当前英文合同
tasks/detection/plan.md / todo.md            → 当前维护步骤与记录
```

## 代码风格

保持已有风格，不做格式重构。Bash 兼容 3.2，变量用 `${VAR}`、数组展开按已有空数组守卫，不使用 `cmd | grep -q`；Python 使用标准库、4 空格缩进、snake_case 函数名，JSON 通过序列化器生成，不手工拼转义。
以下为 `plugins/delegate/hooks/detect.py` 的现有片段，展示实际写法（上下文片段，不是新命令）：

```python
        with tempfile.NamedTemporaryFile(mode='w', dir=str(CACHE_FILE.parent), delete=False) as output:
            temporary = output.name
            json.dump(data, output, ensure_ascii=False)
            output.write('\n')
        os.replace(temporary, str(CACHE_FILE))
```

## 开发边界

- **Always：** 修改前阅读合同；行为修复先复现再复验；保持 Bash 3.2 和双语合同同步；检查实际 diff 和相关测试。
- **Ask first：** 新后端/依赖/flag、沙箱默认或认证方法变更、超出现有模块的能力；付费 live、委托、提交和远端写入取得各自授权。
- **Never：** 暴露凭据/完整私密日志；削弱失败断言；自动回滚用户修改；追认历史审批或擅改归档；把桩结果当作完整宿主行为保证。

## 测试策略

Shell 产品套使用 `stub-codex` 和临时夹具；Python 回归使用标准库 `unittest`。测试位置见项目结构，原合同保留精确命令和断言范围。未设行覆盖率百分比，不虚构阈值。
验证按条款和风险判断，包含正反场景；源码中的保证若没有独立断言，映射明确标“部分覆盖”。真实模型、权限与交互验证单列，未经授权不运行付费样本。

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

## 成功条件与验证映射

以下编号于 2026-10-08 为既有合同添加检索标识，不是历史编号或批准记录。

- **DET-01：** 基础可用性以 CLI 的 ChatGPT 登录为准，探测期限受限；不证明远端/额度。
- **DET-02：** 缓存类型、8 小时 TTL、未来时间和身份匹配按原合同；写入原子且失败降级。
- **DET-03：** 各入口强制刷新/缓存命中/静默输出及 prompt 串行顺序符合原合同。
- **DET-04：** doctor 刷新并报告有限的中文规则诊断，不改业务规则，不把启发式当完整规则验证。

精确测试、实现位置和覆盖缺口见 [条款到证据映射](../docs/verification/2026-10-08-contract-matrix.md)。当前维护计划 Task 5 负责核对该映射，不宣告全部产品条款已经充分验收。

## 开放问题

历史任务逐项验收、旧审批/插件版本及完整交互宿主行为仍未核实。当前已知覆盖缺口列在映射中；此处不新增能力或更强保证。
