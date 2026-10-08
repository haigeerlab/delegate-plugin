# 当前合同条款与验证证据

日期：2026-10-08；产品源码基准：`56c3ba76f1059f929bc908c0e45469abc623859a`。
本页把现有合同重新编号后映射到源码和测试，不恢复历史任务，不补造前置计划或批准。
中英文规格使用同一组 CH/DET/RT 编号。每个模块当前 plan 的 Task 5 核对本页；Task 6 记录文档验收结果。编号不代表测试充分覆盖。

## 如何读结果

“已覆盖”仅指该行列出的确定性检查；“部分覆盖”表示该条款仍有明确缺口。首轮接入实际运行 `scripts/validate.sh` 退出 0（Shell 24 + 19 + 9，Python 10 + 7，eval 自检 7 + 12）；文档补全沿用该结果，没有重复运行总测试；随后实际执行 26 项[免费定向补验](2026-10-08-supplemental.md)，全部通过。它们是一次性证据，不是新增永久回归。
运行时源码和清单与基准不变；当前测试仅 test-detection.sh 应用 F8 隔离修复，文档检查不能替代新源码快照的复验。历史真实样本的来源及限制另见 [历史验证摘要](2026-10-08-history.md)。

完整路径相对仓库根；表内省略前缀的 `test-*.sh/py` 均在 `plugins/delegate/tests/`，`backend.py` / `run_codex.py` 在 `plugins/delegate/scripts/`，`detect.py` / hook 文件在 `plugins/delegate/hooks/`。用例名或原 Shell 标签用于定向定位，不把全套通过当作每个分支都有独立断言。

## channel

合同：[中文](../../spec/channel.md) / [English](../en/SPEC-channel.md)。维护计划：[Task 4–6](../../tasks/channel/plan.md#内容补全计划2026-10-08)。

| 条款 | 实现来源 | 验证来源与验收对象 | 当前覆盖与未验证项 |
|---|---|---|---|
| CH-01 | `scripts/codex-exec.sh` 参数/预检；`scripts/backend.py` check（均在 `plugins/delegate/` 下） | `test-channel.sh` 3/4/8/9/9b/15a/15b/16；`test-channel-regressions.py` 的 `test_help_works_without_codex_and_lists_supported_options`；`test-backend.py` 的 `test_api_key_and_unknown_login_are_rejected_without_echoing_credentials` | 已覆盖所列参数、预检和认证拒绝；未穷举所有 CLI 输出变化 |
| CH-02 | wrapper 的 exec 参数与环境；`backend.py`；`run_codex.py` | `test-channel.sh` 2a/2b/10/11；`test-backend.py` 的 `test_exec_enforces_chatgpt_and_openai_provider` | 部分覆盖：桩证明传参/关闭 stdin，真实 sandbox 权限边界和全部宿主配置未专项验证 |
| CH-03 | `run_codex.py` stop_group/main；wrapper 信号 trap | `test-channel.sh` C23/C24；`test-channel-regressions.py` 的 `test_timeout_ignoring_sigterm_is_bounded_and_returns_124`、`test_timeout_kills_descendant_before_it_can_write_marker`、`test_wrapper_sigterm_reaps_codex_and_descendant`；backend 的登录超时回归 | 部分覆盖：期限、TERM 和同组清理有断言；SUP-01/02/03 已验证 INT/HUP/正常结束同组残余清理的受控样本（16 秒延迟标记观察）；永久回归及全部竞态仍未覆盖，不扩大到自行脱组的后代 |
| CH-04 | wrapper 的基线/Git acceptance 和退出分支 | `test-channel.sh` 12/13/14；`test-channel-regressions.py` 的 `test_write_failures_report_git_acceptance_and_keep_changes`、`test_write_mode_rejects_non_git_directory_without_exec` | 已覆盖所列成功/失败/空答复/超时、已有修改和非 Git 场景；SUP-06 补验 Git 无 HEAD 的受控成功样本；其他边界未穷举 |
| CH-05 | wrapper 的日志目录、umask、尾部和 retain 逻辑 | `test-channel.sh` 1/5/C20/C21/C22；`test-channel-regressions.py` 的 `test_large_single_line_failure_log_has_bounded_stderr_and_full_path` | 部分覆盖：隔离/回显上限/保留有断言；SUP-04/05 补验日志 0700/0600 和软链接拒绝；尚未纳入永久回归 |

## detection

合同：[中文](../../spec/detection.md) / [English](../en/SPEC-detection.md)。维护计划：[Task 4–6](../../tasks/detection/plan.md#内容补全计划2026-10-08)。

| 条款 | 实现来源 | 验证来源与验收对象 | 当前覆盖与未验证项 |
|---|---|---|---|
| DET-01 | `backend.py` probe_cli/check；`detect.py` probe | `test-detection.sh` 1–6/10；backend 的 `test_chatgpt_login_does_not_require_auth_json`、`test_api_key_and_unknown_login_are_rejected_without_echoing_credentials`、`test_failed_login_is_not_reported_as_available`、`test_login_timeout_kills_group_with_inherited_output` | 已覆盖基础认证和期限；远端/额度原本就在保证范围外 |
| DET-02 | `detect.py` identity/read_cache/write_cache | `test-detection.sh` 7/8/9/12a/12b；backend 的 `test_cache_from_other_codex_home_is_not_reused`、`test_future_cache_timestamp_triggers_a_fresh_check` | 部分覆盖：命中/过期/损坏/home/未来时间/写失败有断言；SUP-07–24 补验所列字段类型/身份分量、权限/软链接和 4 写线程 120 次写/145 次读的有限样本；缺永久回归与跨进程压力/全部故障覆盖，同路径账号切换不保证立即失效 |
| DET-03 | `detect.py` main；`detect.sh`；`prompt.sh` | `test-detection.sh` 7/7b/10/10b/11；backend 的 `test_doctor_refreshes_a_previously_unavailable_cache`、`test_prompt_cold_cache_injects_one_confirmation_pointer` | 已覆盖所列入口刷新、静默/合法输出和冷缓存串行行为；不是宿主完整会话验收；FOOTPRINT-01 补验单个业务 Git 夹具三个 hook 的前后目录快照相同 |
| DET-04 | `doctor.sh` 的刷新和中文规则诊断 | `test-detection.sh` 13/13b/14/15；backend 的 doctor 刷新回归 | 部分覆盖：受控环境的所列中文启发式场景及 MUT-06 反例通过。F8 已修复：规则检查自行使用本套受控 CLI；实际当前探测两场景各 19/0，无外层 CLI 的总验证通过。英文/任意项目规则覆盖不属于现有保证 |

## routing

合同：[中文](../../spec/routing.md) / [English](../en/SPEC-routing.md)。维护计划：[Task 4–6](../../tasks/routing/plan.md#内容补全计划2026-10-08)。

| 条款 | 实现来源 | 验证来源与验收对象 | 当前覆盖与未验证项 |
|---|---|---|---|
| RT-01 | `hooks.json`、`prompt.sh`、`route.sh`、detect 共用缓存 | `test-routing.sh` R1/R2/R2b/R3/R5/R6；backend 的 `test_prompt_cold_cache_injects_one_confirmation_pointer` | 已覆盖有效/无效缓存、单行 JSON、不重探、单 handler 和 cold-cache；不是所有宿主调度场景验证 |
| RT-02 | route 提示、`skills/delegate-routing/SKILL.md`、`commands/delegate.md` | `test-routing.sh` R4/R8；`evals/propose-not-auto.sh --selftest` 验证判决器，不发模型请求 | 部分覆盖：指令措辞可发现，判决器有反例；原生 TTY 已实际加载 skill；后续较大案例明确推荐具体只读委托、沿用默认模型并等待，exec为0；只有指定样本，持续遵守及失败恢复仍未充分验收 |
| RT-03 | delegate-routing 六类分流表和返回纪律；主命令调用形态 | `test-routing.sh` R7 加指令文件定向阅读；channel 参数断言可复用 | 部分覆盖：文本与调用形态可核对；真实宿主的六类决策、失败后复核纪律未做完整互动验收 |
| RT-04 | `evals/_preflight.sh`、`propose-not-auto.sh`、`routing-fitness.sh` | 总验证的 preflight 自检、propose 7 项及 routing 12 项自检（均免费） | 已覆盖所列判决器正反输入；SUP-25/26 的两个免费 scaffold 实际退出 0；不作为宿主加载或模型行为验收 |

## 仍需单独处理

- 当前产品覆盖缺口：CH-02/03/05、DET-02、RT-02/03 的部分覆盖；其他行也只证明明确列出的场景，不保证所有分支。
- 历史 119 个未勾项：[逐项裁决](2026-10-08-historical-reconciliation.md)已覆盖全部，106 项当前证据支持、13 项合同替代、0 项仍待验证；119 项历史完成及批准均未知，旧勾选不改。
- 历史批准、旧插件版本和 gate：证据未知，不能由当前条款编号、测试或 phase 补造。
- 完整真实权限、模型和交互验证：需明确测试目标/工具/授权；此前免费批次只补文档和受控离线证据；此前有限 live 通道通过、Claude 路由认证 NORUN；后续整批实际差分通过，原生 skill 加载及已安装命令通过，但主动推荐及完整互动仍不齐备。

新行为修复应在相应模块 plan/todo 新增有验收和验证的切片，先复现后修改；本表不是新增实现授权。

[免费反向验证](2026-10-08-mutation.md)：9 个特定变异覆盖 10 条原条件，正常基线和还原通过；不证明所有变异、历史批准或永久回归。

[F8 当前工作区验证](2026-10-08-f8-applied.md)针对已应用的单文件测试修复；此前变异证据属于修改前快照，运行时未改，历史批准仍未知。

[最新有限 live 验证](2026-10-08-live.md)：当前通道 --live 25/0、真实只读答复非空，补 channel:8-A1/8-V1 的样本证据；不证明真实沙箱的全部权限边界。路由处理/对照两组因 Claude OAuth 会话过期返回 NORUN，没有模型判断，不关闭 RT-02/03 的完整宿主缺口。

[七项整批最新证据](2026-10-08-bulk.md)：处理/对照实际首行不同且无 exec；自然提示实际加载 skill；user-scope 斜杠命令真实只读成功。当前 Bash 取舍已记录双语 ADR；主动推荐样本仍待验证，不扩大为 RT-02/03 完整覆盖或全部沙箱配置通过。

[最后原生交互样本](2026-10-08-proposal.md)：较大案例取得主动推荐、等待确认、默认模型及零exec的直接证据，原条件裁决106/13/0。完整产品覆盖仍有明确缺口；模型假设超时后拆批重派的通知措辞未证明额外调用授权纪律，本次没有实际重派。
