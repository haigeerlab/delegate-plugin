# 规格：review-fingerprint（可在别的机器复算的补丁指纹）

<!-- spec-guard: review approved 1e7ad24d735f -->

简体中文 | [English](../docs/en/SPEC-review-fingerprint.md)

2026-11-20 起草。来源：生态总账 S98，autopr-design 需求 3a（plugin-ecosystem 仓 `research/2026-11-18-自动PR系统设计/plugin-requests-draft.md`，提交 7560e19），由 ecosystem-lead 转交（#21652）。用户 2026-11-20 决定接下并按推荐写规格，原话：「接，按推荐写规格」；同日批准本规格与能力图新行，原话：「批准，写英文页和 Plan」。

## 起因

autopilot 要在 GitHub Actions 上重新算一次审查报告里的补丁指纹，确认审查结论对应的就是要合并的那个补丁。现在的 `scope.diff_sha256` 是对 `git diff` 输出文字算的 sha256，做不到这一点：

- 仓库自己的 `.git/config`（`diff.algorithm`、`diff.noprefix`、`diff.context`、`core.quotepath` 等）和仓库里的 `.gitattributes` 会改变 diff 文字；
- git 版本不同，diff 文字也可能不同；`index` 行里对象编号的缩写长度还会随仓库对象数量自动变化。

前两类可以逐项用 `-c` 堵住，第三类堵不住。只要指纹对 diff 文字算，就不能跨机器稳定。

## 前提（2026-11-20 用户按推荐确认）

- **A1** 新增指纹字段 `scope.fingerprint`，只依赖 git 里存的内容：被审的每个文件改动前后的对象编号和文件权限。与 git 配置、git 版本、diff 输出格式无关。
- **A2** `scope.diff_sha256` 原样保留，计算方式和含义都不变；文档注明它只在本机有效，不能跨机器复算。不为它加 `-c` 加固：加固会改掉现有输出的值，也解决不了 git 版本差异。
- **A3** 只在基准为 `commits`（审两个提交之间的改动）时输出指纹。`staged`、`unstaged`、`working-tree` 审的是本机还没提交的内容，别的机器上没有，这三种模式下字段为 `null`。
- **A4** 复算方用的是同一个仓库（对象编号格式相同，同为 SHA-1 或同为 SHA-256）。delegate 不处理两种格式之间的转换。
- **A5** delegate 只负责把算法写明、做稳定、写进接口；复算、对比 PR 的改动文件、决定能不能合并，都由使用方（autopilot）负责（用户 11-19 原则「每个插件只做它能力范围内的事」）。
- **A6** 只增字段：接口版本 1.3 → 1.4，审查报告 `schema_version` 仍为 `1`。原先在 [run-rules](run-rules.md) 里预告的 1.4 内容（`run.restore`、`run.concurrent`、`doctor.quota`）尚未立项，以后顺延到下一个次版本。发行版本 v0.9.0。

依赖：[claude-review](claude-review.md)（审查上下文与报告生成）、[integration-interface](integration-interface.md)（`interface.json` 与报告合同、版本规则）。

## 指纹算法 `blob-pairs-v1`

**输入：**

- 报告里的 `scope.baseline.from`、`scope.baseline.to`：已解析的完整提交编号（delegate 现在就输出完整编号）。
- 被审路径集合 P：`from` 与 `to` 之间有改动、并且落在审查范围（`include` 去掉 `exclude`）内的文件路径，不做改名识别。P 和 `diff_sha256` 覆盖的文件完全一致，原样写进报告的 `scope.fingerprint.paths`。

**每个路径取两侧条目：** 在 `from` 提交的树里找路径 p，得到权限 `from_mode` 和对象编号 `from_oid`；在 `to` 提交的树里同样得到 `to_mode`、`to_oid`。

- 权限写成 git 树里的 6 位八进制，例如 `100644`、`100755`、`120000`（软链接）、`160000`（子模块）。
- 对象编号写成小写十六进制全长（SHA-1 仓库 40 位，SHA-256 仓库 64 位）。
- 路径在这一侧不存在，或者在这一侧是目录（`040000`），记为 `000000` 和全零编号，位数与仓库的对象编号相同。

**拼成规范文本：**

```text
delegate-blob-pairs-v1\n
<p1>\0<from_mode> <from_oid> <to_mode> <to_oid>\n
<p2>\0<from_mode> <from_oid> <to_mode> <to_oid>\n
…
```

- 第一行是固定的版本头 `delegate-blob-pairs-v1`，后接换行。
- 每个路径一行，按路径的 UTF-8 字节序升序排列。
- 路径原样写入（UTF-8，不加引号、不转义），后接一个 NUL 字节，再接四个字段，字段之间用一个空格隔开，行尾一个换行（`\n`）。
- P 为空时，规范文本只有版本头。

**结果：** `sha256(规范文本的字节)`，写成小写十六进制。

**复算参考（不属于合同，任何能读 git 树的工具都可以）：**

```bash
git --literal-pathspecs ls-tree -z --full-tree <commit> -- <path>
```

输出 `<mode> <type> <oid>\t<path>\0`；没有输出或 `type` 为 `tree` 时，按「不存在」处理。

## 报告字段

`scope` 下新增 `fingerprint`：

```json
"fingerprint": {
  "algorithm": "blob-pairs-v1",
  "sha256": "<64 位小写十六进制>",
  "paths": ["<P，按 UTF-8 字节序>"]
}
```

基准不是 `commits` 时为 `"fingerprint": null`。审查失败、条件不满足时，只要已经取得审查上下文，字段照样输出，和 `diff_sha256` 一致；取上下文之前就失败的情况，两者都是 `null`。

**使用方的解读规则（写进 README 和接口合同）：**

- 指纹只证明「审查看到的补丁 = 这些路径从 `from` 到 `to` 的这些变化」。要确认 PR 里没有审查没看到的文件，使用方要自己对比 PR 的改动文件和 `paths`。
- 审查结论能不能用，仍按 [integration-interface](integration-interface.md) 的解读规则（`completed` 且有结论）。指纹一致不等于审查有结论，更不等于批准合并。
- 遇到不认识的 `algorithm` 值，使用方应当按「无法复算」处理，不能当成一致。

## 接口 1.4

`interface.json` 的 `interface` 改为 `"1.4"`，`review.report` 下新增：

```json
"report": {"schemaVersion": 1,
           "fingerprint": {"field": "scope.fingerprint", "algorithm": "blob-pairs-v1",
                           "baselineModes": ["commits"]}}
```

其余字段不变。

## 技术栈与命令

Python 3 标准库，测试用 `unittest` 和临时 git 仓库，不跑真实模型、不付费。

```bash
python3 -B plugins/delegate/tests/test-review-context.py
python3 -B plugins/delegate/tests/test-review-fingerprint.py
python3 -B plugins/delegate/tests/test-interface.py
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

## 项目结构

```text
plugins/delegate/scripts/review_fingerprint.py    → 新增：规范文本与 sha256（纯函数，不调 git）
plugins/delegate/scripts/review_context.py        → commits 模式取两侧条目，生成 fingerprint
plugins/delegate/scripts/review_result.py         → scope 下输出 fingerprint
plugins/delegate/scripts/delegate_backend.py      → 取上下文前失败时的占位加 fingerprint: null
plugins/delegate/interface.json                   → 1.4，review.report.fingerprint
plugins/delegate/tests/test-review-fingerprint.py → 新增：算法与固定测试向量
plugins/delegate/tests/test-review-context.py     → 各基准模式、仓库配置干扰
plugins/delegate/tests/test-interface.py          → 1.4 断言
scripts/validate.sh、scripts/tests/test-validation-discovery.py → 加入新套件
spec/review-fingerprint.md、docs/en/SPEC-review-fingerprint.md → 本合同
spec/integration-interface.md 及英文页            → 加 1.4 的指向句
插件 README 中英文、待发行说明                       → 对外接口一节同步
```

## 实现要点

- 两侧条目用一次 `git diff --raw -z --no-renames --no-abbrev --no-relative <from> <to> -- <P>` 取得：它给出的就是两侧权限和全长编号，不存在的一侧本来就是 `000000` 和全零编号。仍走现有 `git()`，沿用已屏蔽全局和系统配置的环境。
- 取得的路径集合必须和 P 完全相同，否则报固定码 `fingerprint_inputs_inconsistent`，整次审查按取上下文失败处理（与 `input_changed` 同级），不输出半截指纹。
- 规范文本由 `review_fingerprint.py` 的纯函数生成，测试直接调用它，与取条目的代码分开。

## 代码风格

保持现有风格：4 空格缩进，标准库，错误只用固定码，不把路径、编号或 git 输出写进诊断。示例（`review_context.py` 现有写法）：

```python
    diff_args = ['diff', '--no-ext-diff', '--no-textconv', '--no-renames']
    if mode == 'commits':
        for key in ('from', 'to'):
            baseline[key] = git(root, 'rev-parse', '--verify', '--end-of-options', baseline[key] + '^{commit}').decode().strip()
```

## 测试策略

先写测试并确认红，再实现。

- **算法（`test-review-fingerprint.py`）：** 固定测试向量（手工给定路径、权限、编号，断言规范文本逐字节一致和 sha256 值）；空集合；排序按 UTF-8 字节序（含中文路径、大小写）；SHA-256 仓库的 64 位全零。
- **取条目（`test-review-context.py`，临时仓库）：** 新增、删除、修改、只改权限、文件变软链接、文件变目录；结果与 `git ls-tree` 独立复算一致。
- **配置无关：** 同一对提交，在仓库 `.git/config` 里设置 `diff.algorithm=patience`、`diff.noprefix=true`、`diff.context=10`、`core.quotepath=false`、`core.abbrev=12`，再加 `.gitattributes` 的 `-diff`；断言 `diff_sha256` 变了而 `fingerprint.sha256` 不变（同时证明旧指纹确实不稳定）。
- **模式：** `staged`、`unstaged`、`working-tree` 为 `null`；`exclude` 掉的文件不在 `paths` 里。
- **接口：** `test-interface.py` 断言 1.4 与 `review.report.fingerprint`；已有字段不变。

跨 git 版本的稳定性由算法本身保证（只用树里的权限和编号），本模块不在多个 git 版本上实测。

## 开发边界

- **Always：** `diff_sha256` 的值不变；指纹只用树里存的内容；中英文合同、README、接口同步。
- **Ask first：** 为非 `commits` 模式定义指纹；改变 `blob-pairs-v1` 的任何细节（只能出新的算法名，旧名永远表示同一算法）；提升报告 `schema_version`；提交、推送、发版。
- **Never：** 在指纹里使用 diff 文字或受配置影响的输出；输出半截指纹；在 delegate 里替使用方判断「补丁一致、可以合并」。

## 成功条件与验证映射

- **FP-01：** 固定测试向量、空集合、排序、64 位全零通过（桩测试）。
- **FP-02：** 六种改动形态的条目与 `git ls-tree` 独立复算一致（临时仓库）。
- **FP-03：** 仓库配置与 `.gitattributes` 干扰下 `fingerprint.sha256` 不变，`diff_sha256` 改变（临时仓库）。
- **FP-04：** 非 `commits` 模式为 `null`；`paths` 与 `diff_sha256` 覆盖的文件一致；条目集合不一致时报 `fingerprint_inputs_inconsistent` 且无半截指纹。
- **FP-05：** `interface.json` 为 1.4，`review.report.fingerprint` 与本合同一致，已有字段不变；两项 plugin validate 通过。
- **FP-06：** 插件中英文 README 的对外接口一节、integration-interface 中英文指向句、中英文合同、待发行说明同步。
- **FP-07：** 总验证、两项 plugin validate、`git diff --check` 通过。

## 开放问题

- autopilot 复算时 Actions 上的 checkout 需要能取到 `from` 提交（浅克隆要加深）。这是使用方的部署问题，写进 README 提醒，delegate 不处理。
- 以后若要为本机未提交内容定义指纹（`working-tree` 等），另提变更，用新的算法名。
