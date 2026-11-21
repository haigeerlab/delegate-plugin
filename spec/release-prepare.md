# 规格：release-prepare（发版准备到「只差你点头」）

<!-- spec-guard: review approved af4b9e52b954 -->

简体中文 | [English](../docs/en/SPEC-release-prepare.md)

2026-11-21 起草。来源：生态总账 S101 r3（plugin-ecosystem 仓 `research/2026-11-21-合并之后的接管梳理.md`，提交 dd6c6d3，第一、三、四节），ecosystem-lead 转交（#21885，转自 autopr-design #21882），称用户已批准 r3，原话「按推荐批准」。用户 2026-11-21 在本会话接下并定排期（「接，排在后面」），确认需求摘要与 Q1～Q4 全按推荐（「都按推荐」）；同日批准本规格，原话「批准」。调用约定已与 autopr-design 对齐（#21966、#21967）。

## 起因

autopilot 的「插件」模板要能调用 delegate 的发版步骤。现在仓库没有任何发版脚本，v0.8.x 到 v0.10.0 都是手工改版本号、写发行说明、改链接与测试数量、跑检查。delegate 属于流水线自己用的四个插件，按梳理文档第四节方案 A，最高只到「备好等批」（r3 的 `prepare` 档）：AI 做完全部准备，停在只差用户点头的位置，发版和本机升级由人做。

## 前提

用户 2026-11-21 确认（「都按推荐」）：

- **A1 只做到备好等批。** 在本地新的发版分支上做好版本准备、提交一次、跑完全部免费检查，输出汇总，写明影响面、检查结果和必须由人执行的命令；这些命令一条也不执行。
- **A2 机械部分归脚本，文字归会话。** 搬内容、改链接、改测试数量由脚本做；起因、影响面等文字由调用它的 AI 会话事先写进待发行说明，脚本只检查有没有写。
- **A3 失败就停。** 任何前提或检查不过，报固定诊断码、非 0 退出，不留下半成品提交。
- **A4 仓库脚本。** 放在仓库根 `scripts/`，不作为插件命令发给用户。
- **A5 停在本地。** 不推送、不开 PR、不打标签、不合并、不碰本机安装与 `~/.claude`、`~/.codex`；推送和开 PR 由 autopilot 编排以机器人身份另做（第三批）。
- **A6 一个模块**，不需要用法草案。

autopr-design #21967 的约束（采纳）：

- **A7 无人值守。** 不读标准输入、不弹确认；`--check` 只检查、不写任何东西。退出码 0 = 已备好（`--check` 时为「会备好」），非 0 = 停下交人，原因写进 JSON。
- **A8 同一版本重跑不叠提交。** 要么复用已有的发版提交，要么明确拒绝。
- **A9 输出能当证据。** JSON 带 `schema`（`delegate.release-prepare/v1`）、基线提交 SHA、发版提交 SHA；每项检查写命令与退出码；每条「待人执行的命令」附一句为什么必须由人做。

本规格新提出、请用户审时一并确认：

- **A10 待发行说明的固定形状。** 中文 `docs/releases/unreleased.md` 与英文页在「已归入……」那段之后，必须有：一行 `<!-- release-title: <标题> -->`；本次的变更小节（`## …`，一个或多个）；`## 影响面`（英文 `## Impact`）；`## 验证与已知限制`（英文 `## Validation and known limitations`）。缺任何一项报 `release_notes_incomplete`。脚本把这些原样搬进 `v<X>.md`，在验证小节末尾补一句本次实测的测试数量，再加固定的 `## 更新`（升级步骤）小节，并把待发行说明收回成一段。
- **A11 基线必须是主干最新。** 工作区干净，当前 `HEAD` 等于本地记录的 `origin/main`（脚本不联网、不 fetch，由调用方事先 fetch）；否则 `base_not_main` 或 `worktree_dirty`。发版分支名固定 `release/v<X>`，从基线切出。
- **A12 版本规则。** `<版本>` 形如 `X.Y.Z`，大于当前 `plugin.json` 的版本，标签 `v<X>` 本地不存在；否则 `version_invalid`、`version_not_newer` 或 `tag_exists`。
- **A13 重跑规则。** `release/v<X>` 已存在时：它只比基线多一个提交、提交说明带尾注 `Release-Prepare: v<X>`，就复用（不新建提交，重跑检查，输出同一个发版提交 SHA）；否则报 `release_branch_conflict`。
- **A14 失败清理。** 新建分支后检查失败：丢弃本次改动、切回原分支、删除本次新建的 `release/v<X>`，输出里发版提交 SHA 为 `null`。复用已有分支时检查失败：不删分支，只报失败。
- **A15 检查清单。** `scripts/validate.sh`（从输出数 Python 测试项数）、`claude plugin validate .`、`claude plugin validate ./plugins/delegate`、`git diff --check`、spec-guard 的 `verify-artifacts.sh`（从 Claude 已安装插件记录解析路径，不写死版本）。任何一项命令找不到报 `check_unavailable`，视同失败。
- **A16 接口变化。** 比较最新版本标签（`v*` 按版本排序的最后一个）里的 `interface.json` 与本次的版本号，写进 JSON；不判断兼容性，只报数字。
- **A17 测试方式。** 逻辑写在 `scripts/release_prepare.py`，`.sh` 只是入口；免费测试用临时 git 仓库和假检查命令，不在测试里递归跑 `validate.sh`。真实端到端只在交付验收时，在临时克隆上跑一次、不推送、验完删除。

依赖：[integration-interface](integration-interface.md)（`interface.json` 的版本号）。

## 命令

```text
scripts/release-prepare.sh <版本> [--check]
```

- 只接受这两个参数；多给、少给、格式错报 `usage_invalid`，退出 64。标准输入接到 `/dev/null`。
- 标准输出只有一份 JSON（UTF-8，缩进 2）；过程日志写到标准错误。
- 退出码：0 已备好；1 停下交人（原因见 `reason`）；64 参数错误。

## 步骤

1. 前提：参数、版本规则（A12）、基线（A11）、待发行说明形状（A10）、各文件里要改的锚点都找得到（找不到报 `release_docs_anchor_missing`）。
2. `--check`：在内存里做完第 3 步的改写，确认都能做；跑第 4 步的检查（只读）；不切分支、不写文件、不提交。
3. 改写（非 `--check`）：切出 `release/v<X>`；改 `plugin.json` 版本；生成中英文 `v<X>.md`；收回中英文待发行说明；中英文 README、文档索引、贡献指南里的当前发行链接、发行列表、发布验证数字（Python 项数用第 4 步的实测值，循环回归套数从 `validate.sh` 数）。
4. 检查（A15）：在改写后的工作区跑；全过才提交。
5. 提交：一次提交，说明 `chore: 准备 v<X> 发行` 加正文与尾注 `Release-Prepare: v<X>`；输出 JSON。

## 输出

```json
{
  "schema": "delegate.release-prepare/v1",
  "mode": "prepare",
  "status": "ready",
  "reason": null,
  "version": {"before": "0.10.0", "after": "0.11.0"},
  "interface": {"last_release": "1.5", "now": "1.5"},
  "base": {"ref": "origin/main", "sha": "<40 位>"},
  "release": {"branch": "release/v0.11.0", "sha": "<40 位或 null>", "reused": false},
  "notes": {"title": "…", "zh": "docs/releases/v0.11.0.md", "en": "docs/en/releases/v0.11.0.md"},
  "tests": {"python": 388, "loop_suites": 28},
  "checks": [{"name": "validate", "command": ["/bin/bash", "scripts/validate.sh"], "exit_code": 0}],
  "human_steps": [{"command": "…", "why": "…"}]
}
```

- `mode`：`prepare` 或 `check`；`status`：`ready` 或 `stopped`。`stopped` 时 `reason` 为固定诊断码，`release.sha` 为 `null`（A13 复用时除外）。
- `checks` 列出实际跑过的每一项（没跑到的不列）；命令以参数数组给出，不含环境变量与本机路径以外的内容。
- `human_steps` 固定 7 条，每条带 `why`：① 推送 `release/v<X>` 并开 PR（远端写入，按 A5 由编排或人做）；② 合并 PR（流水线自用插件发布最高到 `prepare`）；③ 在合并提交上打附注标签并推送；④ `gh release create v<X> --verify-tag --notes-file docs/releases/v<X>.md`；⑤ Claude Code 侧升级（影响所有在跑的会话，要用户排顺序）；⑥ Codex 侧改 `~/.codex/config.toml` 的 `ref` 并升级（改用户全局配置）；⑦ 重开会话、⌘Q 重开 ChatGPT（桌面动作）。③④ 的命令里合并提交写占位 `<合并提交>`。

## 固定诊断码

`usage_invalid`、`version_invalid`、`version_not_newer`、`tag_exists`、`worktree_dirty`、`base_not_main`、`release_notes_incomplete`、`release_docs_anchor_missing`、`release_branch_conflict`、`check_unavailable`、`check_failed`。`check_failed` 时 `checks` 里能看到是哪一项、退出码多少。

## 技术栈与命令

Bash 3.2 入口加 Python 3 标准库；测试用 `unittest`、临时 git 仓库和假检查命令，不联网、不跑真实模型。

```bash
python3 -B scripts/tests/test-release-prepare.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
scripts/release-prepare.sh              → 新增：入口，stdin 接 /dev/null，调 Python
scripts/release_prepare.py              → 新增：前提、改写、检查、提交、JSON
scripts/tests/test-release-prepare.py   → 新增：临时仓库与假检查命令
scripts/validate.sh                     → 登记新测试（语法检查已覆盖新脚本）
CONTRIBUTING.md、CONTRIBUTING.en.md     → 新增「发版」一节：怎么写待发行说明、怎么跑脚本、人要做的七步
docs/releases/unreleased.md 及英文页    → 按 A10 的形状给出空模板说明（不改已有历史段落）
spec/release-prepare.md、docs/en/SPEC-release-prepare.md → 本合同
```

## 代码风格

保持仓库现有风格：4 空格缩进，标准库，错误只用固定码；git 一律参数数组调用，不经 shell、关掉交互提示。示例（`plugins/delegate/scripts/review_context.py` 现有写法）：

```python
def git(repository, *arguments):
    environment = {'PATH': '/usr/bin:/bin', 'LANG': 'C', 'LC_ALL': 'C',
                   'GIT_OPTIONAL_LOCKS': '0', 'GIT_CONFIG_NOSYSTEM': '1',
                   'GIT_CONFIG_GLOBAL': '/dev/null', 'GIT_CONFIG_SYSTEM': '/dev/null',
                   'GIT_ATTR_NOSYSTEM': '1', 'GIT_LITERAL_PATHSPECS': '1',
                   'GIT_TERMINAL_PROMPT': '0'}
```

区别：审查要屏蔽用户的全局配置，发版脚本要提交，需要用户自己的提交身份与提交检查钩子，所以只沿用参数数组、`GIT_TERMINAL_PROMPT=0`、标准输入接 `/dev/null`，不屏蔽全局配置。

## 测试策略

先写测试并确认红，再实现。临时仓库里放一个缩小版的仓库布局（`plugin.json`、`interface.json`、中英文待发行说明、README、贡献指南、文档索引的锚点行），假检查命令按需返回 0 或非 0、打印假的 `Ran N tests`。

- **参数与前提：** 每个诊断码各至少一例；`--check` 前后仓库字节不变（含 `.git` 的分支和引用）。
- **改写：** 版本号、两份 `v<X>.md`（标题、搬入的小节、补的测试数量、`## 更新`）、待发行说明收回、各文档锚点改写，与期望文本逐字一致。
- **检查与提交：** 全过时只有一个新提交、带尾注、父提交为基线；任一检查失败时没有新提交、`release/v<X>` 被删除、回到原分支。
- **重跑：** 同版本第二次跑复用同一提交 SHA；分支被人改过时报 `release_branch_conflict`。
- **输出：** JSON 字段齐全、SHA 为 40 位、`human_steps` 7 条且都有 `why`；不读标准输入（给一个会阻塞的 stdin 也能跑完）。
- **端到端（验收时一次）：** 在本仓库的临时克隆上用真实检查命令跑一次，核对产出后删除克隆，不推送。

## 开发边界

- **Always：** 无人值守；只写本仓库工作区与本地分支；中英文合同与贡献指南同步。
- **Ask first：** 增加联网、推送、开 PR、打标签等任何远端或不可逆动作；改输出 `schema` 版本；改待发行说明的固定形状；提交、推送、发版本模块本身。
- **Never：** 读标准输入或弹确认；碰 `~/.claude`、`~/.codex` 或本机安装；在检查失败时留下发版提交；替会话编写起因、影响面文字。

## 成功条件与验证映射

- **RP-01：** 每个固定诊断码按「固定诊断码」一节触发，退出码与 `reason` 正确（桩测试）。
- **RP-02：** `--check` 不写任何东西（仓库字节与引用前后一致），成功时退出 0。
- **RP-03：** 改写结果与期望文本逐字一致（A10、步骤 3）。
- **RP-04：** 检查全过时恰好一个带尾注的新提交；任一失败时不留提交、不留分支、回到原分支（A14）。
- **RP-05：** 同版本重跑复用提交、冲突时拒绝（A13）。
- **RP-06：** JSON 符合「输出」一节，`human_steps` 7 条各带 `why`；不读标准输入。
- **RP-07：** 贡献指南中英文「发版」一节、待发行说明模板说明、中英文合同同步。
- **RP-08：** 总验证、两项 plugin validate、`git diff --check` 通过；验收时在临时克隆上端到端跑通一次。

## 开放问题

- 无。待发行说明的固定形状（A10）与诊断码清单如需调整，请在审规格时提出。

## 附：autopr-design 的意见（#21967，原文）

> 没有现成约定，按你们的倾向写规格即可，四点都同意。补几条约束，来自合并方案 r3 和安全内核：
> ① 入口：`scripts/release-prepare.sh <版本> [--check]` 可以。要求能无人值守地跑：不读标准输入，不弹确认。`--check` 只检查、不写任何东西。退出码：0 = 已备好；非 0 = 停下交人，原因写进 JSON。用同一版本重跑时，要么复用已有的发版提交，要么明确拒绝，不能叠出第二个提交。
> ② 输出：JSON 里请加 `schema`（如 `delegate.release-prepare/v1`）、基线提交 SHA 和发版提交 SHA。安全内核要求证据绑定到提交，没有 SHA 就没法当证据。测试要写明跑了什么命令、退出码是多少。"待用户执行的命令"每条附一句为什么必须由人做，例如本机升级后要重开会话。
> ③ 停在哪：停在本地发版分支上的一次提交，同意。这正是 r3 里 `prepare` 档"只差你点头"的位置。delegate 属于流水线自己用的四个插件，发布最高只到 `prepare`，所以不需要为 `auto` 设计后续步骤。
> ④ 推送和开 PR：脚本不用做。推分支、开 PR 由 autopilot 编排用机器人身份去做（第三批）。脚本也不要动本机安装和 `~/.codex` 配置，本机安装是后面单独的一步。
