# 任务清单：integration-interface

计划：[plan.md](plan.md)；规格：[spec](../../spec/integration-interface.md)。
授权：用户 2026-10-17 原话“批准这份 Plan，按 Task 1 到 Task 4 做到 Checkpoint 2 停下。”提交、推送、PR、发版和通知其他负责人不在此授权内。

- [x] Task 1：一致性测试（RED），加入总验证
- [x] Task 2：发布 `interface.json`（GREEN）
- [x] Checkpoint 1（report）：接口与测试到位
- [x] Task 3：插件中英文 README“对外接口”一节与待发行说明
- [x] Task 4：总验证与记录
- [x] Checkpoint 2（gate）：交付前人工验收

## 记录

**Checkpoint 1（2026-10-17，report）：**

- RED：无 `interface.json` 时 `python3 -B plugins/delegate/tests/test-interface.py` 退出 1，7 项均在 `setUp` 因 `missing plugins/delegate/interface.json` 失败，无导入或语法错误。
- GREEN：补文件后同一命令 7 项通过；`claude plugin validate ./plugins/delegate` 与 `claude plugin validate .` 均 `Validation passed`。
- 防漂移抽查：临时把 `schemaVersion` 改为 2、`run.backends` 加 `claude-code`，测试 2 项失败（`test_report_schema_version`、`test_backends_match_capabilities`）；还原后核对两处内容并复测通过。
- 合同与源码一致：`review_outcome` 的 AST 扫描无非常量赋值，取值集合等于合同；`execution_status` 赋值均在合同集合内。未改产品脚本。
- 测试文件权限与现有 Python 测试一致（非可执行），由 `scripts/validate.sh` 的 Python 套件清单调用。

**Task 3（2026-10-17）：** 插件中英文 README 新增“对外接口”一节并在“目录”补 `interface.json`；中英文待发行说明各加一条。字段名逐项对照规格，无私有项目名。

**Task 4（2026-10-17）：**

- 首次 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 1：`scripts/tests/test-validation-discovery.py` 的隔离夹具按固定清单生成各 Python 套件占位，未包含新注册的 `interface`。在夹具清单补 `interface` 一项（连带改动，断言不变），重跑退出 0、`validate: ok`。
- `claude plugin validate .`、`claude plugin validate ./plugins/delegate` 均通过；`git diff --check` 退出 0。
- Spec Guard 0.64.2 `verify-artifacts.sh`：4 通过 · 0 警告 · 0 失败。
- 未验证：使用方（spec-guard、decision-inbox）尚未按此接口实现探测或引用；已安装用户需升级后才有 `interface.json`。未调用真实模型，未提交、推送或发版。

**Checkpoint 2（2026-10-17，gate）：** 用户看过实际改动、验证结果与未验证项后回复“验收通过，提交并开 PR 到 main；版本号和发版先不动。”授权范围为提交与开 PR；版本号、发版和通知其他负责人仍未授权。
