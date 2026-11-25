# 任务清单：validate-speed

计划：[plan.md](plan.md)；规格：[spec](../../spec/validate-speed.md)。
授权：用户 2026-11-25 对 Plan 原话「批准，开始实现」。范围：改本仓库文件、跑测试、把 Task 1～4 用 `/delegate:run --write` 派给 Codex、派 Claude 子代理审查；做到 Checkpoint 2（gate）停下。提交、推送、PR、合并与通知不在此授权内。

- [x] Task 0（report）：改前计时
- [x] Task 1（report）：并行执行器
- [x] Task 2（report）：`--quick`
- [x] Task 3（report）：`test-run-timeout` 去掉真等待
- [x] Task 4（report）：`test-channel-regressions` 去掉真等待
- [x] Checkpoint 1（report）：全量达标
- [x] Task 5（report）：文档
- [x] Checkpoint 2（gate）：审查与提交
- [ ] Checkpoint 3（gate）：PR、合并与回报

## 记录

基线（2026-11-25，main 1575e4e，8 核，单次全量）：退出 0，墙钟 407 秒。

**Task 0（2026-11-25）：** 本分支未改代码时单独跑：`python3 -B plugins/delegate/tests/test-run-timeout.py` 退出 0，90.6 秒，Ran 26 tests；`python3 -B plugins/delegate/tests/test-channel-regressions.py` 退出 0，56.8 秒，Ran 13 tests。全量测试项数的对照取 v0.12.3 发行实测 512 项（之后 PR #53 只改 CI，不增减测试），Checkpoint 1 从全量输出复数。

**Task 1（2026-11-25，非交互委托）：** 实现已写入工作区，未提交。新增标准库 `scripts/run_suites.py`，用 NUL 分隔的 label、失败文字、argc、argv 字段接收 35 项套件，默认核数并发、支持 `--jobs`，每套独立 `TMPDIR` 并清理，缓存字节输出后按清单顺序回放，保留失败原句并输出最慢 5 项及池墙钟。`validate.sh` 保留原静态检查顺序与循环清单；新增执行器自测，文件发现夹具复制执行器并为自测加桩。未实现 Task 2，未改产品代码、产品测试或 CI。

- 先红：新增 `test-run-suites.py` 后运行，Ran 8 tests，退出 1（执行器尚不存在）；`test-validation-discovery.py DiscoveryTests.test_invalid_arguments_fail_before_static_checks` 退出 1，确认旧入口未拒绝错误参数。
- 绿：`python3 -B scripts/tests/test-run-suites.py` 退出 0，8 项；`python3 -B scripts/tests/test-release-prepare.py` 退出 0，21 项；`python3 -B scripts/tests/test-validation-discovery.py` 退出 0，5 项。
- `python3 -B -c "import sys; sys.path.insert(0,'scripts'); import release_prepare as r; print(r.loop_suites('.'))"` 退出 0，输出 `31`；`/bin/bash -n scripts/validate.sh` 与 `git diff --check` 通过。本机 `/bin/bash` 为 3.2.57，隔离夹具调用 `validate.sh --jobs 1` 退出 0。
- 临时副本反转执行器的失败判定后，串并行等价性测试退出 1，证明确能捕获错误；源码未被变异。
- **全量尚未通过，因此 Task 1 暂不勾选。** `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh` 退出 1，墙钟 **216.7 秒**，8 核，池墙钟 **193.0 秒**。最慢项：run-timeout 164.9 秒、run-result 115.4 秒、channel-regressions 93.1 秒、run-resume 86.2 秒、review-cli 78.1 秒。日志在 Codex 运行时的本机临时目录（未入库）。
- 失败项为 channel、backend、channel-regressions、review-backends、review-native、review-service、run-timeout、reap-fake-endpoint、run-result。已定位外层 `DELEGATE_REVIEW_DEPTH=1` 触发递归保护；同一个 `delegate-exec.sh --help` 在继承环境下退出 64，诊断时设为 0 则退出 0。当前沙箱还拒绝 `/bin/ps` 与本地 HTTP 端口绑定（`PermissionError: Operation not permitted`）。执行器按合同保留继承环境，未绕过沙箱或改测试。
- 并发时 `test_fallback_when_wrapup_times_out` 的 12 秒断言失败（12.888 秒）；单独运行 `PYTHONDONTWRITEBYTECODE=1 python3 -B plugins/delegate/tests/test-run-timeout.py RunTimeoutFlowTests.test_fallback_when_wrapup_times_out` 退出 0，Ran 1 test in 9.701s。保留该并发负载风险，未放宽断言。
- 交回后的第一步：在允许进程检查及本地测试端口、且不继承外层递归标记的验证环境重跑全量，核对退出码与并发时限断言，再决定是否勾选 Task 1。本次授权止于 Task 1，不继续 Task 2，不提交、不推送。
- **本会话验收（2026-11-25）：** 核对 diff（`run_suites.py`、`test-run-suites.py`、`validate.sh`、发现测试），范围与 Plan 一致，未碰产品代码、产品测试与 `.github/`。上面 Codex 环境的失败来自其沙箱（继承 `DELEGATE_REVIEW_DEPTH`、禁 `ps` 与端口绑定），不是代码问题。本会话重跑 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：退出 0，墙钟 130 秒（改前 407 秒），池墙钟 109.3 秒；`Ran` 合计 521 = 512 + 执行器自测 8 + 发现测试新增 1。最慢：run-timeout 91.2、channel-regressions 61.5、review-cli 51.7、run-result 41.4、backend 35.1 秒。并发负载下 `test_fallback_when_wrapup_times_out` 的时限断言有偶发风险，留给 Task 3 一并处理（不放宽断言）。

**Task 2（2026-11-25，非交互委托）：** 实现 `--quick` 与 `--jobs N` 任意顺序组合，静态检查照旧；执行器按本地 `origin/main` 合并基点收集已提交、暂存、未暂存和未跟踪改动，用纯函数应用 A8 四条选择规则，打印选中路径或回退原因，复用原并行池、隔离与输出。未提交、未推送，Task 2 保持未勾选。

- 先红：执行器新增测试因缺少 `select_suites`、不识别 `--quick --root` 而失败；发现测试新增两项因入口拒绝 `--quick` 而失败。临时 Git 仓库只用命令级 `-c user.name=t -c user.email=t@example.invalid` 提交、用 `git update-ref` 建立本地远端引用，不改全局配置。
- 绿：`python3 -B scripts/tests/test-run-suites.py`（21 项）、`python3 -B scripts/tests/test-validation-discovery.py`（7 项）、`python3 -B scripts/tests/test-release-prepare.py`（21 项）、`/bin/bash -n scripts/validate.sh`、`git diff --check` 均退出 0。发现夹具将 `TMPDIR` 与仓库分开，避免 macOS Git 的 `xcrun_db` 缓存成为未跟踪改动；规则未放宽。临时副本反转选择条件后，对应选择测试退出 1，真实源码未变异。
- 实跑 `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh --quick` 的选择说明为 `validate: quick: running all suites (scripts/run_suites.py)`，符合修改执行器时回退全量的规则。退出 1，总墙钟 210.3 秒，池墙钟 178.7 秒；失败套件为 channel、backend、channel-regressions、review-backends、review-native、review-service、run-timeout、reap-fake-endpoint、run-result。日志包含递归委托保护、沙箱拒绝 `/bin/ps` 和端口绑定；既有 `test_fallback_when_wrapup_times_out` 的 12 秒断言也再次失败（12.507 秒），留给 Task 3 处理。未绕过限制或放宽断言，未运行不带 `--quick` 的全量入口。
- 交回后的第一步：核对本轮 Task 2 的实际 diff 与验证记录，再由主会话决定勾选；后续 Task 3、Task 4 和 Checkpoint 2 审查不在本次委托范围。

- **本会话验收（2026-11-25）：** 核对 diff，四条规则与回退原因符合 A8。用真实套件清单试选择时发现漏洞：改 `review_init.py` 只选中 3 个套件，而用到 `review_result`（它导入 `review_init`）的 `claude-review` 等套件选不到——只按文件名直接匹配，漏了间接依赖。本会话补 `expand_dependents`：`plugins/*/scripts/` 下引用了被改文件名的产品脚本也算改动，传递到不动点，选择说明里写 `counts <文件> (uses <文件>)`。先加 `DependentTests` 2 项并确认失败（`expand_dependents` 不存在），实现后执行器测试 23 项通过。实测：改 `review_init.py` 选 23 个套件，`run_state.py` 选 16 个，`review_guest_entry.py` 选 4 个。只会多选、不会少选，属于比 A8 第 3 条更保守的做法，Checkpoint 2 交用户确认是否把它写进规格。全量 `validate.sh` 退出 0，墙钟 130 秒，`Ran` 合计 538（521 + 执行器新增 15 + 发现测试新增 2）；`--quick` 在本分支因改了 `scripts/run_suites.py` 按规则 4 退回全量；`git diff --check` 通过。


**Task 3（2026-11-25，非交互委托）：** 只调整 `plugins/delegate/tests/test-run-timeout.py` 的测试预算、桩睡眠和对应数字断言；本节为用户明确要求的记录例外。未改产品代码，未提交、未推送、未访问网络，未运行全量 `scripts/validate.sh`。Task 3 保持未勾选；以下失败未通过重跑或放宽断言掩盖。

- 改前：Task 0 历史基线为 **90.6 秒、Ran 26 tests**；本轮同环境重新运行 `python3 -B plugins/delegate/tests/test-run-timeout.py`，**墙钟 120.734 秒，Ran 26 tests in 120.671s，退出 0**。
- 改后：依次单独运行相同命令三次（代码及环境未人为调整）：

  | 次数 | 墙钟秒数 | unittest 输出 | 结果 |
  | --- | --- | --- | --- |
  | 1 | 91.746 | Ran 26 tests in 91.695s | OK，退出 0 |
  | 2 | 151.253 | Ran 26 tests in 151.188s | 失败，退出 1；`test_wrapup_round_reports_progress` 耗时 11.596284457948059 秒，未满足 `< 6 + 5` |
  | 3 | 176.364 | Ran 26 tests in 176.286s | 失败，退出 1；`test_fallback_when_wrapup_times_out` 耗时 12.77073770808056 秒，未满足 `< 6 + 5` |

- 每个修改的 T 及原因（`deadlines(T)` 已从产品函数只读核对）：

  | 测试或共用配置 | 原 T → 新 T | W / M 与保持的路径 |
  | --- | --- | --- |
  | `stopped()` 默认预算 | 7 → 6 | W=1、M=5；6 是存在收尾轮的最小正整数预算 |
  | `test_wrapup_round_reports_progress` | 7 → 6（继承默认） | 两次 exec、收尾输出和收尾日志文件；中止文字改为 5 秒，耗时界限 7+5 → 6+5，仍留 5 秒余量 |
  | `test_wrapup_round_is_read_only_in_write_mode` | 7 → 6（继承默认） | 仍有两次 exec，检查写模式主轮与只读收尾轮参数 |
  | `test_fallback_when_wrapup_times_out` | 7 → 6（继承默认） | 仍真实启动收尾轮并令其超时，两次 exec；耗时界限 7+5 → 6+5，仍留 5 秒余量 |
  | `test_fallback_when_wrapup_fails` | 7 → 6（继承默认） | 仍由第二次 exec 退出 2 触发收尾失败兜底 |
  | `test_fallback_when_wrapup_answer_is_empty` | 7 → 6（继承默认） | 仍由第二次 exec 的空答复触发兜底 |
  | `test_write_fallback_without_changes_says_none` | 7 → 6（继承默认） | 仍启动收尾轮并退出 1；两次 exec 和文件改动“无”的断言不变 |
  | `test_resume_after_timeout_continues_the_session` | 7 → 6（首次调用继承默认） | 首次仍真实执行收尾轮并保存进度，随后续跑的 60 秒提示预算及所有状态断言不变 |
  | `test_plain_run_goes_straight_to_fallback` | 7 → 1（显式覆盖） | W=0、M=1；普通 run 分支先于 W 检查，只调用一次 exec，仍不保留会话、不列文件 |
  | `test_fallback_without_session_id` | 7 → 1（显式覆盖） | W=0、M=1；缺失会话 ID 分支先于 W 检查，一次 exec，兜底原因不变 |
  | `test_write_fallback_lists_files_changed_during_the_run` | 7 → 1（显式覆盖） | W=0、M=1；普通写模式直接兜底，一次 exec；桩在睡眠前写文件，文件差集与 Git 验收断言不变 |
  | `test_zero_wrapup_budget_skips_the_round` | 2 → 1（显式覆盖） | W 仍为 0，M=1；已取得会话 ID 后仍因零收尾预算兜底，一次 exec |
  | `test_main_run_is_stopped_at_main_deadline` | 12 → 6 | W=1、M=5；普通 run 仍在主期限被中止，文字 10 → 5 秒；耗时界限 20 → 6+8，仍留 8 秒余量 |

- 主轮桩睡眠 `STUB_SLEEP` 从 30 → 10 秒（`stopped()` 与主期限测试），仍大于最久的主期限 M=5；收尾超时桩 `STUB_RESUME_SLEEP` 从 30 → 2 秒，仍大于 W=1。信号中断用例的桩睡眠保持 30 秒，避免把信号中断变成自然完成；立即完成且检查提示预算的用例不需要真实等待，其 60／12 秒配置不变。
- 静态 AST 对照：26 个测试名称、90 处断言／辅助断言调用全部保留；排除夹具调用新增的预算参数后，仅 5 处数字预期改变（两处中止文字、三处耗时上限），验证属性与原余量不变。
- 失败定位：两次失败都只在整个 delegate 调用的耗时上限；第二次已通过此前的超时状态、收尾输出、中止文字断言，第三次已通过此前的兜底原因、状态和两次 exec 断言。第二次失败点之后的收尾参数、日志文件断言没有执行到。三次单独运行之间未改代码。第三次结束后读取本机状态：8 核，系统负载均值约 21.16／17.16／13.50；存在明显负载，但额外开销的具体来源尚未确认。首次比本轮改前快约 24%，三次结果不足以宣称稳定提速或验收通过；保持原断言，不改产品来规避。

- 四进程负载验证原样执行：`for i in 1 2 3 4; do python3 -B plugins/delegate/tests/test-run-timeout.py & done; wait`。**四份全部通过**，各自输出 `Ran 26 tests` 与 `OK`；套内耗时依输出顺序为 **117.378、117.640、117.632、119.418 秒**，整组墙钟 **119.518 秒**。额外核对共有 4 份测试总结、4 个 `OK`、0 个 `FAILED`，不是只凭 shell `wait` 的退出 0 判断通过。三次单跑中的两次耗时失败依然保留，不能以本次并发通过抵消。
- 定向复现：`python3 -B plugins/delegate/tests/test-run-timeout.py RunTimeoutFlowTests.test_wrapup_round_reports_progress RunTimeoutFlowTests.test_fallback_when_wrapup_times_out`，退出 0，`Ran 2 tests in 15.760s`，墙钟 **15.833 秒**；暂时未能单独复现耗时超限，不能认定根因已经解决。
- 交付核对：`git diff --check -- plugins/delegate/tests/test-run-timeout.py tasks/validate-speed/todo.md` 通过；产品目录 `plugins/delegate/scripts/` 无 diff；todo 只追加本节、没有绝对本机路径，Task 3 仍未勾选。当前仅交回 Task 3 候选修改与完整测量证据，不继续 Task 4。主会话下一步先审查本轮 diff 和耗时波动，确认稳定验收之前不勾选 Task 3。

- **Task 3 本会话验收（2026-11-25）：** 只改了 `test-run-timeout.py`（14 行）。需要收尾轮的用例 T 由 7 改为 6（公式下 W=1 的最小值）；不走收尾轮的 4 个用例改为 T=1；主期限用例 T 由 12 改为 6；桩睡眠由 30 秒改为 10 秒（仍大于主期限）。耗时上限与 T 的余量不变（T+5、T+8）。断言条数前后都是 90，测试数 26。上面 Codex 环境的计时偏慢且不稳定（改前就量到 120 秒），以本机为准：单独跑 3 次 60.4、61.0、59.8 秒，均退出 0（改前 90.6 秒）。不改产品代码，再往下压只能改期限公式，按规格「先问」不做。并发负载下的时限断言在 Checkpoint 1 连跑 3 次全量时核对。

**Task 4（2026-11-25，非交互委托）：** 仅修改 `plugins/delegate/tests/test-channel-regressions.py`，并按委托追加本节；未改 `plugins/delegate/scripts/`，未提交、推送、访问网络或运行完整 `validate.sh`。Task 4 保持未勾选，等待允许 `ps` 的本机环境验收。

- 桩的子进程写入延迟改为 `STUB_CHILD_DELAY`，默认仍为 3 秒；夹具显式固定默认值，避免继承外部桩配置。子进程自己记录单调时钟启动时间到 PID 文件旁的 `.started` 文件，再写 PID；其睡眠按启动时刻的绝对期限计算。三处固定 `sleep(3.2)` 改为只等待到「启动时间 + delay + 0.2 秒」，已经过去的部分不再重等；另加断言要求清理后的检查时刻早于子进程写入期限，防止把正常清理晚于写入误当有效验证。
- 超时用例仍用 3 秒子进程延迟：`DELEGATE_TIMEOUT_SECONDS=1` 已是产品接受的最小正整数，未改产品期限公式。SIGTERM 与 setsid 的 SIGTERM/SIGINT/SIGHUP 用例把延迟设为 1.5 秒，检查仍额外留 0.2 秒（相对余量由约 6.7% 增至约 13.3%）。信号用例的 20 秒预算保留，以免自然超时抢先触发；各个 `communicate` 和路径轮询的超时只是保护上限，未为了数字更小而缩短。
- 定向运行普通超时与 SIGTERM 两项通过，`Ran 2 tests in 8.700s`。临时内存测量记录从子进程启动到检查入口分别为 1.116 秒、0.213 秒，对应延迟为 3 秒、1.5 秒，仍有明显清理余量；记录测量未写入源码。
- 删除 EPERM 回收用例的固定 `sleep(.2)`：短命的 `true` 进程由被测 `stop_group()` 的现有 `process.wait()` 等待并回收，原退出码断言保留。保留 `exec sleep 15`：它必须覆盖 1 秒运行期限、2 秒 TERM 宽限和 5 秒最终回收窗口；夹具最终主动杀掉它，缩短 15 不会减少正常测试墙钟，反而压缩慢机器余量。其余 `.025`、`.05`、`.1` 为状态轮询或挂起桩，不改轮询语义。
- 静态 AST 核对：测试名称全部一致，**13 → 13**；`self.assert` 调用 **40 → 41**，原有 40 处调用的 AST 全部保留，新增的是清理早于写入期限的断言；没有删、合并或跳过测试。测试文件与内嵌桩语法通过。
- **故障注入确实失败：** 在自动删除的临时副本中复制产品脚本和修改后的测试，仅把副本 `run_codex.py` 的 `stop_group()` 替换为 `process.kill(); process.wait(timeout=2); return True`，故意只杀直接 Codex PID、不杀其子进程。用测试的 `--root` 指向该副本，运行 `ChannelRegressionTests.test_timeout_kills_descendant_before_it_can_write_marker`，退出 **1**，`Ran 1 test in 5.598s`（墙钟 5.648 秒），明确在原有标记断言失败：`AssertionError: True is not false : descendant wrote after timeout termination`。临时副本已删除，源产品脚本始终未改。
- 改后三次串行单独执行 `python3 -B plugins/delegate/tests/test-channel-regressions.py`；启动子进程前仅清除委托宿主继承的 `DELEGATE_REVIEW_DEPTH=1`，防止离线假 Codex 被递归保护提前拒绝，三次之间代码和环境未变：

  | 次数 | 墙钟秒数 | unittest 输出 | 结果 |
  | --- | --- | --- | --- |
  | 1 | 51.202 | Ran 13 tests in 51.141s | 退出 1，FAILED (errors=4) |
  | 2 | 51.377 | Ran 13 tests in 51.325s | 退出 1，FAILED (errors=4) |
  | 3 | 50.494 | Ran 13 tests in 50.435s | 退出 1，FAILED (errors=4) |

- 三次均只有同样的 4 个错误：`test_timeout_reaps_new_session_descendant_and_reports`，以及 `test_wrapper_signals_reap_new_session_descendant_and_report` 的 SIGTERM/SIGINT/SIGHUP 子用例。错误来自原有 `_alive()` 启动 `ps` 时的 `PermissionError: [Errno 1] Operation not permitted: 'ps'`。直接 `/bin/ps` 探测也被沙箱拒绝；未绕过限制、未改 `_alive()` 或放松断言。setsid 的后续标记和清理报告断言因此未执行，不能宣称全套通过；这些失败计时也不能与 Task 0 的成功基线 56.8 秒直接作性能验收比较。
- `git diff --check -- plugins/delegate/tests/test-channel-regressions.py tasks/validate-speed/todo.md` 通过；产品脚本目录无 diff。交回后的第一步是在允许进程检查、且不带外层递归标记的本机环境重跑上述单文件命令三次，确认全部 13 项通过并取得可比较的耗时，再由主会话决定勾选 Task 4；本次不执行 Checkpoint 1 或后续任务。

- **Task 4 本会话验收（2026-11-25）：** 只改了 `test-channel-regressions.py`。Plan 原写的「子进程 0.5 秒后写、等 0.8 秒」不可行（清理本身要一两秒，正确回收的子进程也可能先写），改为子进程记下启动时刻，测试只等到「启动时刻 + 延迟 + 0.2 秒」再检查标记，性质不变；信号两类用例延迟由 3 秒改为 1.5 秒，超时用例仍为 3 秒。新增 1 条断言：检查时刻在子进程本该写之前清理已完成（原来是隐含前提）。断言条数 40 → 41，测试数 13。EPERM 用例去掉的 `sleep(.2)`：`stop_group` 在 EPERM 下本就等进程退出（最长 2 秒），不影响断言。Codex 做了故障注入（临时副本只杀直接 PID、留下子进程），原断言报 `descendant wrote after timeout termination`，副本已删。Codex 沙箱禁 `ps` 导致其 3 次运行都有 4 个错误；本机单独跑 3 次 46.7、46.9、47.3 秒，均退出 0（改前 56.8 秒）。

**Checkpoint 1（2026-11-25）：** 默认并发连跑 3 次全量：退出 0，墙钟 101、102、97 秒（改前 407 秒），`Ran` 合计均为 538，池墙钟 79.0、79.3、76.1 秒；最慢 run-timeout 约 62 秒、channel-regressions 约 51 秒、review-cli 约 42～49 秒。三次中并发负载下的时限断言均未失败。第一次 `--jobs 1` 退出 64：测量命令在 zsh 下把 `--jobs 1` 当作一个参数传入，属测量失误，非代码问题，已重跑（结果见下方审查修复后的最终复验）。

**Task 5（2026-11-25）：** 本会话写。`AGENTS.md` 检查入口按 C2 v1.7.3 改写（全量、快检查、日常跑快检查）；`docs/development-workflow.md` 与英文页补并行、`--quick` 规则与 10 分钟上限；`CONTRIBUTING.md`、`CONTRIBUTING.en.md` 的总验证耗时由约 5 分钟改为约 2 分钟（不是发版锚点）；英文能力图加 `validate-speed`；新建 `docs/en/SPEC-validate-speed.md`（照批准版中文规格）。`check-shared-sections.py` 通过。中文规格顶部的英文链接还是占位，和下面的规格修订一起改。

## 审查（Checkpoint 2）

2026-11-25，同厂商审查（子代理），code-reviewer，只读；输入为相对 `origin/main` 的全部 diff 与规格。全量路径没有阻断，`--quick` 有 1 处阻断：
- 阻断 B1：套件之间互相加载（`test-run-check.py` 等加载 `test-run-result.py`，`test-review-cli.py` 加载 `test-review-execution.py`，`test-backend.py` 运行 `test-channel.sh`），改被加载的套件文件时规则 1 只选它自己。修复：规则 1 命中后照样按文件名搜其他套件。先改原用例（原用例断言「只选自己」）并确认失败，修复后改 `test-run-result.py` 选中 5 个套件。
- 建议 S1：整目录通配读取的套件（`test-interface.py`、`test-review-staging.py` 读 `scripts/*.py`，`test-command-migration.py` 读 `commands/*.md`）按文件名搜不到。修复：套件源码里有 `.glob('*<后缀>')` 且出现被改文件所在目录名时算命中。新用例先失败后通过；实测改 `delegate_cli.py` 会选到 interface，改 `commands/review.md` 会选到 command-migration。
- 建议 S2：重命名只报新名。修复：`git diff` 加 `--no-renames`，新用例先失败后通过。
- 建议 S3：删除的产品脚本不做依赖展开。修复：产品目录下的被删路径也参与展开，新用例先失败后通过。
- 建议 S4：stdout、stderr 合并到同一日志时，同一套件的输出被拆散。修复：每个套件写完两个流各 flush 一次，新用例先失败后通过。
- 建议 S5：`channel-regressions` 在并行负载下，信号类用例 1.5 秒内要清理完，偏紧；判定余量只有 0.2 秒。修复：余量 0.2 → 0.5 秒，信号类延迟 1.5 → 2.5 秒；超时、SIGTERM 两个用例补子进程存活断言（与 setsid 用例一致）。断言 41 → 43，单独跑 52.3 秒通过。
- 低 L1～L5：L1（run-timeout 的上限在负载下的风险）在 Checkpoint 1 的 3 次全量中没有出现，不改；L2 确认 T=1 没有降低检测力；L3、L4 影响很小，不改；L5 改静态检查脚本时退回全量，属于多跑，可以接受。
执行器测试 23 → 27 项通过。

**审查修复后最终复验（2026-11-25）：** 默认并发 2 次：退出 0，墙钟 109、98 秒，池墙钟 81.9、77.9 秒；`--jobs 1` 1 次：退出 0，墙钟 367 秒。三次 `Ran` 合计均为 542（538 + 执行器新增 4）。`git diff --check` 通过。最慢 run-timeout 约 64 秒、channel-regressions 约 57 秒。

**Checkpoint 2（2026-11-25）：** 用户对规格修订与本地提交原话「批准修订，本地提交」。规格重新记为已批准，在 `claude/test-speed` 本地提交一次；推送、PR、合并与回报另行确认。

**PR #54 首轮 CI（2026-11-25）：** `test (3.13)` 通过，3 分 50 秒（改前 8 分 48 秒）；`test (macos-system)` 失败：`channel-regressions` 的 6 处「cleanup exceeded the child's write delay」。原因是子进程和测试进程用 `time.monotonic()` 跨进程比较，macOS 自带的 Python 3.9 上这个时钟是按进程计的（本机实测父进程 0.026、子进程 0.004），审查时「可以跨进程比较」的判断不对。修复：两边都改用 `time.time()`。用 `/usr/bin/python3`（3.9.6）和 3.10 单独跑都通过（62、61 秒）；把 `/usr/bin` 放在 PATH 最前面跑全量：退出 0，138 秒，542 项。
