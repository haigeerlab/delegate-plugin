# 实施计划：integration-interface

<!-- spec-guard: review approved -->

日期：2026-10-17。规格：[spec/integration-interface.md](../../spec/integration-interface.md)（用户 2026-10-17 批准）。任务：[todo.md](todo.md)。
本计划只覆盖免费的本地实现与验证；提交、推送、PR、发版和通知其他插件负责人另行授权。

## 顺序与依赖

Task 1 → Task 2 → Checkpoint 1 → Task 3 → Task 4 → Checkpoint 2。串行，不派子代理。
Task 1 先写一致性测试并确认它失败，Task 2 补文件转绿；文档在接口定稿后再写，避免说明先于事实。

## Task 1：一致性测试（RED）

**描述：** 新增 `test-interface.py`，用标准库 `unittest` 从 `delegate_capabilities.BACKENDS`、`review_result.base_report()`、`FINDING_FIELDS` 取事实，比对 `interface.json` 与合同的五项断言；并把它加入总验证的 Python 套件清单。
`execution_status` 取值用 `base_report()` 的归一化行为验证（合法值原样保留、非法值归为 `failed`）；`review_outcome` 取值用 AST 扫描 `scripts/` 中对 `review_outcome` 的字符串赋值，与合同集合比对，不靠正则猜。
**验收条件：** 测试在缺少 `interface.json` 时因“文件不存在”失败，而不是导入错误或语法错误；不改其他测试。
**验证：** `python3 -B plugins/delegate/tests/test-interface.py` 退出非 0，失败原因是缺文件。
**依赖：** 无。
**涉及文件：** `plugins/delegate/tests/test-interface.py`、`scripts/validate.sh`。
**规模：** S，2 文件。

## Task 2：发布 `interface.json`（GREEN）

**描述：** 在插件根目录新增规格中的首版 `interface.json`，内容与规格逐字段一致。
**验收条件：** Task 1 测试全绿；两项 plugin validate 通过；不改任何产品脚本。
**验证：** `python3 -B plugins/delegate/tests/test-interface.py`；`claude plugin validate ./plugins/delegate`；`claude plugin validate .`。
**依赖：** Task 1。
**涉及文件：** `plugins/delegate/interface.json`。
**规模：** XS，1 文件。

## Checkpoint 1（report）：接口与测试到位

把 Task 1 的失败输出与 Task 2 的通过输出记入 todo 后继续。若测试暴露合同与源码不一致（例如源码还能产出合同未列的取值），停下报告，改规格还是改合同由用户定，不改源码迁就文档。

## Task 3：对外文档与待发行说明

**描述：** 插件中英文 README 新增“对外接口”一节：`interface.json` 的位置与读取方式、版本规则、`backends` 不代表可用、v1 报告的取得方式、稳定字段与解读规则；“目录”一节补 `interface.json` 一行。`docs/releases/unreleased.md` 中英文各记一条。
**验收条件：** 中英文内容对应、字段名与规格一致；不出现私有项目名；不改其他章节。
**验证：** 逐项对照规格的字段表；`git diff --check`；本地链接检查随总验证运行。
**依赖：** Task 2。
**涉及文件：** `plugins/delegate/README.md`、`plugins/delegate/README.en.md`、`docs/releases/unreleased.md`、`docs/en/releases/unreleased.md`。
**规模：** S，4 文件。

## Task 4：总验证与记录

**描述：** 运行全部免费验证，结果记入 todo；核对产物约定。
**验收条件：** 下列命令全部退出 0；todo 记下命令、结果和未验证项。
**验证：**

```bash
PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh
claude plugin validate .
claude plugin validate ./plugins/delegate
git diff --check
```

另用当前启用的 Spec Guard 运行 `verify-artifacts.sh` 与 `phase-guard.sh`。
**依赖：** Task 3。
**涉及文件：** `tasks/integration-interface/todo.md`。
**规模：** XS，1 文件。

## Checkpoint 2（gate）：交付前人工验收

把实际 diff、验证结果和未验证项交用户审。之后的提交、PR、版本号与发版、通知 spec-guard 和 decision-inbox 负责人，逐项等用户授权。

## 影响面

只新增一个静态文件、一个测试和文档；报告生成、命令参数、hook 与后端行为不变。已安装用户在升级前看不到 `interface.json`，使用方探测会得到“未知”或“未安装”，属预期。

## 风险与缓解

- **说明和代码漂移：** 由 Task 1 的一致性测试守住，改字段时测试会红。
- **使用方把 `backends` 当成可用：** 规格、README 和 `interface.json` 的语义都写明只是支持声明；可用性仍看 `/delegate:doctor`。
- **AST 扫描漏掉动态赋值：** 现有 `review_outcome` 赋值都是字符串常量或常量条件表达式；测试遇到无法静态解析的赋值时直接失败，提示人工核对。

## 开放问题

- 版本号是否在本模块合入时升到 0.5.3，留到 Checkpoint 2 后与发版一起定。
