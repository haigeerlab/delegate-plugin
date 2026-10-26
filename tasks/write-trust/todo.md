# 任务清单：write-trust

计划：[plan.md](plan.md)；规格：[spec](../../spec/write-trust.md)。
授权：用户 2026-10-26 原话「前提 A1–A9、能力图新行、Spec 和 Plan 全部批准。写入能力图并记下批准；实现前先告诉 delegate-owner 协调 S35 的先后。」范围为 Task 1–Task 4 与 Checkpoint 1、2 的本地实现与免费验证；Task 2 动 `codex-exec.sh` 前须等 delegate-owner 协调与 S35 的先后。Checkpoint 3 付费实测、提交、推送、PR、版本号与发版不在任何默认授权内。

- [x] Task 1：`codex_trust.py` 纯函数与单元测试
- [x] Task 2：接入 `codex-exec.sh`
- [x] Checkpoint 1（report）：桩测试全绿
- [x] Checkpoint 2（report）：免费真机核验
- [x] Task 3：文档
- [x] Task 4：总验证与记录
- [x] Checkpoint 3（gate）：付费实测
- [x] Checkpoint 4（gate）：交付前人工验收

## 记录

**Task 1（2026-10-26）：** RED：`python3 -B plugins/delegate/tests/test-write-trust.py` 16 项中 11 项因 `No module named 'codex_trust'`、4 项因脚本不存在（退出 2）失败。GREEN：新增 `codex_trust.py` 后 16 项通过（表头／点号／内联表／单引号键命中，`<根>-sub`、`<根>/sub/deeper` 不命中，四种读不准原因，普通仓库与 worktree 的根目录、子目录覆盖键均为主仓库路径，运行前后配置字节与 mtime 不变）。计划外多改两处登记：`scripts/validate.sh` 的套件清单加 `write-trust`，`scripts/tests/test-validation-discovery.py` 的 fixture 套件清单同步加上（否则发现回归因缺文件失败）。`PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`；`git diff --check` 通过。Task 2 等 delegate-owner 协调与 S35 的先后。

**先后安排（2026-10-26，负责人 delegate-owner 决定）：** S35（run-timeout）先合入 main；S36 等负责人通知后 `git fetch origin` 并 rebase 到 origin/main，再从 Task 2 接着做。rebase 时能力图新行移到 run-timeout 之后、Build order 同步；`scripts/validate.sh` 与发现回归 fixture 的套件清单若与 S35 冲突，两边都保留。在此之前不碰 `codex-exec.sh`、README、`run-resume.md`、`channel.md`、`unreleased.md`。

**rebase（2026-10-26）：** 负责人通知 S35 已合入 main（haigeerlab/delegate-plugin#15，合并提交 e7a5e1b）。未提交改动先备份到 scratchpad（补丁＋未跟踪文件副本），还原后 `git merge --ff-only origin/main`，再 `git apply --3way` 套回；`scripts/validate.sh`、发现回归 fixture、能力图三处冲突以 main 为准重加：套件清单为 `run-timeout write-trust`，能力图新行放在 run-timeout 之后，Build order 同步。未使用 git stash。

**Task 2（2026-10-26）：** RED：`test-write-trust.py` 新增 `WriteRunTests` 6 项，3 项失败（写模式 run、可续跑与续跑、读不准提示）。GREEN：`codex-exec.sh` 在 `APPROVAL` 之后加 `TRUST` 数组（仅写模式调用 `codex_trust.py`），普通 run 与 `exec resume` 两条 `CODEX_ARGS` 都展开；超时收尾续跑固定只读，不加。22 项通过。顺带把夹具抽成 `RepositoryFixture` 基类，避免父类测试在子类重跑。

**Checkpoint 1（2026-10-26，report）：** `test-write-trust.py`、`test-run-resume.py`、`test-review-backends.py`、`test-run-timeout.py` 均 OK；`test-channel.sh` 24 通过 / 0 失败；`scripts/validate.sh` 退出 0、`validate: ok`；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过。现有测试断言未改。

**Checkpoint 2（2026-10-26，report）：** 免费真机核验 5 个用例（对照写入；普通仓库根目录、子目录、worktree 子目录、已有 untrusted 均不写入），全部 401，真实配置 sha256 `c84d6a4b…3c8b` 前后一致。首次运行对照组超时一次，重跑正常。记录：`docs/verification/2026-10-26-delegate-s36-write-trust-check.md`。

**Task 3（2026-10-26）：** 中英文同步：根 README「输出与验收」那段改写为新行为（不再出现「现在会改动 Codex 的用户配置」）；插件 README 第 26 行改回「不修改全局配置」并注明读不准时的例外；新增 `docs/en/SPEC-write-trust.md`；`spec/channel.md`、`spec/run-resume.md` 及英文页各加一句指向；`docs/en/capability-map.md` 新行与 Build order；中英文待发行说明新增 write-trust 一节。`spec/write-trust.md` 第 3 行由「English（批准后补…）」改为英文页链接。

**Task 4（2026-10-26）：** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 0、`validate: ok`；`claude plugin validate .` 与 `./plugins/delegate` 均通过；`git diff --check` 通过。spec-guard `verify-artifacts.sh`：4 通过 · 2 警告 · 0 失败，两条警告为 `spec/run-resume.md`（加了一句指向）与 `spec/write-trust.md`（补英文链接）在批准后已修订，需用户复审后重记批准；HEAD 干净副本上为 0 警告，确认由本次改动引起。未验证：WT-07 付费实测（Checkpoint 3，待授权）。

**Spec 复审（2026-10-26）：** 用户原话「两处 Spec 修订复审批准；Checkpoint 3 付费实测批准，按你写的步骤跑一次。」已用 review-mark 重记：`spec/write-trust.md` 指纹 6e8ad64dfdd8、`spec/run-resume.md` 指纹 e78ae2487595；`verify-artifacts.sh` 4 通过 · 0 警告 · 0 失败。

**Checkpoint 3（2026-10-26，gate，已授权）：** 在 `~/delegate-s36-live-20261026231004` 跑一次真实 `--write`：退出 0、`status=done`，`hello.txt` 写出，日志 `sandbox: workspace-write`、`approval: never`，无「未能确认」提示；真实 `~/.codex/config.toml` sha256 前后均为 `c84d6a4b…3c8b`。记录：`docs/verification/2026-10-26-delegate-s36-write-trust-live.md`。临时仓库保留，待用户决定是否删除。

**Checkpoint 4（2026-10-26，gate）：** 用户原话「Checkpoint 4 验收通过。授权提交、推送并开 PR（中文提交信息与 PR 描述）；不发版。」
