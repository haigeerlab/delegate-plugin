# 119 个历史未勾项逐项裁决

日期：2026-10-08。归档与当前产品源码基准：`56c3ba76f1059f929bc908c0e45469abc623859a`。

原文只读，未改任何旧复选框。每个条目有来源行、原文、当前依据和状态；所有历史完成时间及人工批准仍为 unknown。当前证据满足不等于当时已经完成。

覆盖 119 / 119：当前证据满足 106，现行合同替代 13，仍待验证/确认 0。

[机器记录](2026-10-08-historical-reconciliation.json)保存完整原文、来源、证据路径/行号及哈希；本页提供逐项导航。现行免费补验见[定向结果](2026-10-08-supplemental.md)。

## 当前仍需处理的条目

| 条目 | 理由 |
|---|---|

## channel

| 条目 / 原文来源行 | 原条件（短览） | 当前裁决 | 理由及证据 |
|---|---|---|---|
| channel:1-A1 / 14 | .claude-plugin/marketplace.json 与 plugins/delegate/.claude-plugin/plugin.js… | 现行合同替代 | 插件清单 version 已有；marketplace 本身采用现行 name/owner/plugins 格式，无根 version。两项原生校验通过，旧要求不能按原字面补勾。（MAN, MP, PM, VAL） |
| channel:1-A2 / 15 | validate.sh 检查：JSON 语法、所有 .sh 的 bash -n、可执行位、${VAR} 写法（不许 $VAR 紧跟多字节）、不许 cm… | 当前证据满足 | 现行 validate 的 JSON/Bash/可执行位和危险模式检查在源码可定位，首轮总验证退出 0。（VALIDATOR, VAL） |
| channel:1-A3 / 16 | 喂一个已知坏输入（故意写 $VAR中文）时 validate.sh 非零退出 | 当前证据满足 | MUT-01-multibyte-variable：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT） |
| channel:1-V1 / 19 | /bin/bash scripts/validate.sh 退出 0 | 当前证据满足 | 首轮接入实际 /bin/bash scripts/validate.sh 退出 0；产品源码未改，不把它写成历史时点的执行。（VAL） |
| channel:1-V2 / 20 | 手工注入坏输入后退出非 0，还原后回到 0 | 当前证据满足 | MUT-01-multibyte-variable：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT） |
| channel:2-A1 / 33 | 桩把收到的完整 argv 写进一个可断言的调用日志 | 当前证据满足 | stub-codex 用 printf %q 写完整 argv；当前断言套读取该调用日志检验参数。（STUB, CH） |
| channel:2-A2 / 34 | 桩支持：STUB_ANSWER / STUB_EXIT / STUB_STDOUT_BYTES / STUB_READ_STDIN | 当前证据满足 | STUB_ANSWER/EXIT/STDOUT_BYTES/READ_STDIN 在桩中存在，通道正反断言实际覆盖对应行为。（STUB, CH, VAL） |
| channel:2-A3 / 35 | 断言套能把 PATH 指向桩，且**不触网** | 当前证据满足 | 测试套将 PATH 置桩并以临时认证响应运行；首轮运行免费产品套，无模型请求。（CH, STUB, VAL） |
| channel:2-A4 / 36 | 空套跑出「总计 0 通过 / 0 失败」并退出 0 | 现行合同替代 | 这是初建空骨架时的阶段条件；当前非空套为 24 条，不能从现有套回推空骨架当时运行。（CH, VAL） |
| channel:2-V1 / 39 | /bin/bash plugins/delegate/tests/test-channel.sh 退出 0 | 当前证据满足 | 首轮通道产品套 24 通过、0 失败。（VAL, CH） |
| channel:2-V2 / 40 | 手工让桩 STUB_EXIT=3，确认调用日志里记下了 argv | 当前证据满足 | 现行 test-channel.sh 的失败调用设置 STUB_EXIT=3，并校验状态及 stderr；桩每次先记录 argv。（STUB, CH, VAL） |
| channel:3-A1 / 53 | 调用含全部四要素：env -u OPENAI_API_KEY、</dev/null、-o + stdout 重定向、非交互 preamble | 当前证据满足 | wrapper 仍具 env -u 两类 key、stdin=/dev/null、-o/日志重定向和非交互 preamble，backend 回归检验认证配置。（WRAP, BACK, VAL） |
| channel:3-A2 / 54 | 断言 1：桩吐 100KB 到 stdout → 调用方拿到的 stdout **不含**那 100KB | 当前证据满足 | 通道断言 1 以 100KB 桩过程输出核验 stdout 隔离；首轮通过。（CH, VAL） |
| channel:3-A3 / 55 | 断言 2a（**反**）：STUB_READ_STDIN=1 + stdin 是永不关闭的管道 + **不加** </dev/null → 桩阻塞 | 当前证据满足 | 通道 2a/2b 为限时正反成对断言：直接读未关闭 stdin 阻塞，wrapper 关闭 stdin 后完成；首轮通过。（CH, VAL） |
| channel:3-A4 / 57 | 断言 2b（**正**）：同样条件**加上** </dev/null → 桩在限时内完成 | 当前证据满足 | 通道 2a/2b 为限时正反成对断言：直接读未关闭 stdin 阻塞，wrapper 关闭 stdin 后完成；首轮通过。（CH, VAL） |
| channel:3-A5 / 58 | 断言 10：桩收到 --sandbox read-only | 当前证据满足 | 通道断言 10 读取桩参数并校验 read-only；不扩展为真实权限证明。（CH, VAL） |
| channel:3-A6 / 59 | 断言 15/16：空任务或未知选项退出 **64**；以 - 开头的任务不被当成选项 | 当前证据满足 | 通道 15a/15b/16 覆盖无任务、未知选项和 -- 后以 - 开头的任务；首轮通过。（CH, VAL） |
| channel:3-A7 / 60 | 输出末尾回报日志路径与「过程 N 字节 / 答复 M 字节」 | 当前证据满足 | wrapper 成功尾部输出模型/推理、过程与答复体量和日志路径；过程正文不进入 stdout。（WRAP, CH, VAL） |
| channel:3-V1 / 63 | test-channel.sh 新增 7 条断言全绿 | 当前证据满足 | 对应的 1/2a/2b/10/15a/15b/16 七个当前断言都在 24 条通过结果中，不解释为过去新增时的结果。（CH, VAL） |
| channel:3-V2 / 64 | 断言 2a/2b 必须带超时上限，挂起要判失败而不是卡住套件 | 当前证据满足 | 2a/2b 的持有者和外层观察有界；首轮 suite 已完成，未以无限挂起代替失败判断。（CH, VAL） |
| channel:3-V3 / 65 | **断言必须在 /bin/bash 下跑**：zsh 的 MULTIOS 会把多个输入重定向**拼接** | 当前证据满足 | 首轮真实运行使用 /bin/bash 总入口，模块 Shell 套也由 /bin/bash 调用。（VALIDATOR, VAL） |
| channel:4-A1 / 79 | 断言 3：codex 存在但 --version 失败 → 退出 **127** + 提示 npm install -g @openai/codex@… | 当前证据满足 | 通道断言 3 同时检验 127 和安装提示；首轮通过。（CH, VAL） |
| channel:4-A2 / 80 | 断言 4：codex 不在 PATH → 退出 127 | 当前证据满足 | 通道断言 4 检验 CLI 缺失的 127；当前回归还验证 help 无 CLI 可用。（CH, REG, VAL） |
| channel:4-A3 / 81 | 断言 5：桩退出非 0 → 脚本退出非 0，stderr 回显日志尾部与完整日志路径 | 当前证据满足 | 通道断言 5 检验非零原码、尾部和日志路径；另有 100KB 单行错误上限回归。（CH, REG, VAL） |
| channel:4-A4 / 82 | 断言 6：桩退出 0 但答复文件为空 → **退出非 0**（不许把空当成功） | 当前证据满足 | 通道断言 6 检验空答复非零；写失败回归含 empty 场景。（CH, REG, VAL） |
| channel:4-V1 / 85 | test-channel.sh 新增 4 条断言全绿 | 当前证据满足 | 原 3/4/5/6 对应的当前四个失败场景在通道 24 通过结果中。（CH, VAL） |
| channel:5-A1 / 101 | 断言 8：--model X --effort high → 桩收到 -m X 和 -c model_reasoning_effort="high" | 当前证据满足 | 通道断言 8 验证 -m 和 model_reasoning_effort 透传，当前参数与原任务目的相同。（CH, WRAP, VAL） |
| channel:5-A2 / 102 | 断言 9：不传 → 桩**没有**收到 -m | 当前证据满足 | 通道断言 9 验证不传模型时无 -m，尊重配置默认。（CH, VAL） |
| channel:5-A3 / 103 | 断言 7：桩模拟无效 slug 的 400 → 脚本退出非 0 | 当前证据满足 | 断言 7 用受控非零桩验证不删 -m 重试；不声称真正请求了网络 400。（CH, VAL） |
| channel:5-A4 / 104 | 输出末尾回报实际使用的模型与推理档（不传时显示「配置默认」） | 当前证据满足 | wrapper printf 在成功尾部显示实际传入模型/推理或配置默认；有源码依据。（WRAP） |
| channel:5-A5 / 105 | 空数组展开写成 ${ARR[@]+"${ARR[@]}"}（bash 3.2） | 当前证据满足 | EXTRA 展开采用 Bash 3.2 空数组守卫，已通过首轮 /bin/bash 检查。（WRAP, VAL） |
| channel:5-V1 / 108 | test-channel.sh 新增 3 条断言全绿 | 当前证据满足 | 当前 7/8/9 三个模型参数断言存在且在首轮通道通过结果中。（CH, VAL） |
| channel:5-V2 / 109 | /bin/bash scripts/validate.sh 通过（bash 3.2 静态检查） | 当前证据满足 | 首轮真实总入口退出 0，包含 Bash 模式、清单与模块验证；不倒推历史完成时间。（VALIDATOR, VAL） |
| channel:6-A1 / 122 | 断言 11：--write → 桩收到 --sandbox workspace-write | 当前证据满足 | 通道断言 11 验证 --write 对应 workspace-write；只是传参证明。（CH, VAL） |
| channel:6-A2 / 123 | 断言 12：git 仓库里 → 输出含基线 HEAD + git status --short + git diff --stat | 当前证据满足 | 通道断言 12 与失败/Git 回归检验 baseline/status/diff；本批 SUP-06 还验证无 HEAD 输出。（CH, REG, SUP, VAL） |
| channel:6-A3 / 124 | 断言 13：**非** git 目录 → 明说拿不到 diff，**不伪造验收块** | 现行合同替代 | 当前非 Git 在执行前退出 64，不执行 Codex；旧的继续运行但说明无 diff 条件已由更严格合同替代。（WRAP, REG, REL） |
| channel:6-A4 / 125 | 断言 14：跑前已有 N 个未提交变更 → 验收块把 N 报出来 | 当前证据满足 | 通道断言 14 验证已有 2 个修改的基线计数；源码不自动回滚。（CH, VAL） |
| channel:6-A5 / 126 | 默认仍是只读；--write 必须显式 | 当前证据满足 | 默认 read-only，仅显式 --write 改 sandbox，断言 10/11 通过；授权是行为规则而非不可绕过锁。（WRAP, CH, CMD, VAL） |
| channel:6-V1 / 129 | test-channel.sh 新增 4 条断言全绿，**19 条全绿** | 现行合同替代 | 当前通道套为 24 条并加 7 个 Python 生命周期回归，旧 19 条固定总数已过时；对应四场景有当前证据。（CH, REG, VAL） |
| channel:6-V2 / 130 | /bin/bash scripts/validate.sh 通过 | 当前证据满足 | 首轮真实总入口退出 0，包含 Bash 模式、清单与模块验证；不倒推历史完成时间。（VALIDATOR, VAL） |
| channel:7-A1 / 143 | commands/delegate.md 的 allowed-tools 只放 Bash(<脚本路径> *) | 现行合同替代 | 用户具体批准当前保留 Bash 的取舍，双语 ADR Accepted；旧固定脚本路径条件被当前合同替代，未满足旧字面。当前批准不追认原历史批准。（CMD, MUT, ADR） |
| channel:7-A2 / 144 | 文档写明：Bash timeout 设 600000；--write 必看验收块；**不要 cat 整个日志** | 当前证据满足 | 主命令明确 timeout 600000、写模式查看实际 Git diff 和按片段读取日志；这是文本证据，不是宿主行为验收。（CMD） |
| channel:7-A3 / 145 | 文档写明 --write 需用户当轮明确要求，Claude 不得自行升级 | 当前证据满足 | 主命令和 skill 明确当轮授权才可加 --write、模型不得升级。（CMD, SKILL） |
| channel:7-A4 / 146 | plugin.json 正确声明 commands | 现行合同替代 | 当前 plugin.json 无 commands 字段，命令在标准 commands/ 目录发现；两项原生清单校验通过，旧显式声明要求不再是当前清单方式。（PM, CMD, VAL） |
| channel:7-V1 / 149 | /bin/bash scripts/validate.sh 通过（含清单一致性） | 当前证据满足 | 首轮真实总入口退出 0，包含 Bash 模式、清单与模块验证；不倒推历史完成时间。（VALIDATOR, VAL） |
| channel:7-V2 / 150 | 装进 user scope 后 /delegate 能跑通一次真实委托 | 当前证据满足 | B3：原生交互 user-scope /delegate:delegate 实际解析，无 --plugin-dir；Bash timeout 600000，唯一真实 read-only exec 成功答复18字节，业务全部内容哈希不变；一次样本，历史批准未知。（CMD, BULK） |
| channel:8-A1 / 163 | --live 真调一次只读委托，答复非空 | 当前证据满足 | 当前快照 test-channel.sh --live 实际退出 0，25 条通过、真实只读答复非空（3 字节）；源码哈希一致。原临时日志随套件清理，保存的是入口输出及快照，不伪造日志/answer 完整哈希或历史批准。（CH, LIVE） |
| channel:8-A2 / 164 | 断言日志/答复体量比 **≥ 40×** | 现行合同替代 | 0.4.0 明确体量比只作观察，取消固定 40 倍门槛；不可拿单个高比例样本恢复旧保证。（REL, CH） |
| channel:8-A3 / 165 | 不带 --live 时这组被跳过且在输出里说明「跳过不代表通过」 | 当前证据满足 | 免费 test-channel.sh 输出 LIVE 已跳过（跳过不代表通过）；首轮免费套通过。（CH, VAL） |
| channel:8-A4 / 166 | 前置检查 codex --version 与 auth.json，缺任一则报「**没跑起来**」而不是「不通过」 | 现行合同替代 | 当前 live/执行以 CLI ChatGPT 登录为准，不要求 auth.json；backend 回归证明无 auth.json 的桩状态可用。（BEPY, BACK, REL） |
| channel:8-V1 / 169 | /bin/bash plugins/delegate/tests/test-channel.sh --live 通过 | 当前证据满足 | 当前快照 --live 入口实际退出 0，原有桩断言和真实只读非空答复检查通过；一次样本，不证明全部沙箱配置或历史当时完成。（CH, LIVE） |
| channel:8-V2 / 170 | 不带 flag 时套件仍全绿且明确标出跳过 | 当前证据满足 | 免费 test-channel.sh 输出 LIVE 已跳过（跳过不代表通过）；首轮免费套通过。（CH, VAL） |

## detection

| 条目 / 原文来源行 | 原条件（短览） | 当前裁决 | 理由及证据 |
|---|---|---|---|
| detection:D1-A1 / 14 | detect.sh 支持 --print（人看的）与 hook 模式（输出 JSON 或什么都不输出） | 当前证据满足 | detect.sh 转发 --print 或 hook 默认模式；对应打印和空/JSON 断言已通过。（DET, DETPY, VAL, F8） |
| detection:D1-A2 / 15 | 断言 10：PATH 里没有 codex → hook 模式**退出 0 且 stdout 完全为空** | 当前证据满足 | 检测断言 10 校验无 CLI 时退出 0 且 stdout 为空；首轮通过。（DET, VAL, F8） |
| detection:D1-A3 / 16 | hooks.json 注册 SessionStart 与 UserPromptSubmit，路径用 ${CLAUDE_PLUGIN_ROOT} | 当前证据满足 | hooks.json 同时注册 SessionStart/UserPromptSubmit，路径引用 CLAUDE_PLUGIN_ROOT；当前 prompt 串行结构另见 D1-A4/R1-A8。（HOOK, PROMPT, BACK, F8） |
| detection:D1-A4 / 17 | hooks.json 里的命令即使脚本缺失也不报错（照 spec-guard 的写法留兜底） | 当前证据满足 | 注册命令使用 if [ -f ] 和 stderr 重定向，缺文件不调用；静态结构证据，不冒称所有宿主处理都已实测。（HOOK, F8） |
| detection:D1-V1 / 20 | /bin/bash scripts/validate.sh 退出 0 | 当前证据满足 | 首轮总验证退出 0，产品源码与该基准不变。（VAL, F8） |
| detection:D1-V2 / 21 | /bin/bash plugins/delegate/tests/test-detection.sh 退出 0 | 当前证据满足 | 首轮检测产品套 19 通过、0 失败。（DET, VAL, F8） |
| detection:D1-V3 / 22 | 变异：把「零输出」那条去掉 → 断言 10 必须变红 | 当前证据满足 | MUT-02-unavailable-detection-output：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT, F8） |
| detection:D2-A1 / 35 | 断言 1：三级全过 → 可用 | 当前证据满足 | 检测断言 1 校验当前 CLI 基础条件可用；不声称远端/额度可用。（DET, BEPY, VAL, F8） |
| detection:D2-A2 / 36 | 断言 2：wrapper 不可执行 → 不可用，原因指向 wrapper | 当前证据满足 | 检测断言 2 校验 wrapper 不可执行的原因。（DET, VAL, F8） |
| detection:D2-A3 / 37 | 断言 3：codex 不在 PATH → 不可用 | 当前证据满足 | 检测断言 3 校验 PATH 无 Codex 的安全原因。（DET, VAL, F8） |
| detection:D2-A4 / 38 | 断言 4：codex 在 PATH 但 --version 失败 → 不可用，提示含 npm install -g @openai/codex@lat… | 当前证据满足 | 检测断言 4 校验版本命令失败的安装提示；首轮通过。（DET, BEPY, VAL, F8） |
| detection:D2-A5 / 39 | 断言 5/6：auth.json 不存在 / 存在但为空 → 不可用，提示去登录 | 现行合同替代 | 生产代码不读取/覆盖 auth.json，CODEX_AUTH_FILE 仅留在旧桩模拟 CLI 状态；当前改用 CLI/keychain/CODEX_HOME 认证合同。（BEPY, STUB, BACK, REL） |
| detection:D2-A6 / 40 | auth.json 路径可用 CODEX_AUTH_FILE 覆盖（**测试绝不碰真实 ~/.codex/**） | 现行合同替代 | 生产代码不读取/覆盖 auth.json，CODEX_AUTH_FILE 仅留在旧桩模拟 CLI 状态；当前改用 CLI/keychain/CODEX_HOME 认证合同。（BEPY, STUB, BACK, REL） |
| detection:D2-V1 / 43 | 6 条断言全绿 | 现行合同替代 | 1–6 旧标签仍在套里，但其中 auth.json 判据已经改为 CLI 状态；不能以标签数量证明旧认证合同成立。（DET, BEPY, REL） |
| detection:D2-V2 / 44 | 变异：把第 2 级换成只查 command -v → 断言 4 必须变红（这是真实故障的形状） | 当前证据满足 | MUT-03-skip-version-probe：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT, F8） |
| detection:D3-A1 / 57 | 断言 7：缓存新鲜 → **不再调用 codex**（用 stub-codex 的调用日志为空来证明） | 当前证据满足 | 检测断言 7 通过桩调用日志验证新鲜缓存不调用 CLI；首轮通过。（DET, DETPY, VAL, F8） |
| detection:D3-A2 / 58 | 断言 8：缓存 checkedAt 超过 8 小时 → 重探（调用日志有一次） | 当前证据满足 | 检测断言 8 与本批 SUP-17 验证过期重新判断，不复用过期缓存。（DET, SUP, VAL, F8） |
| detection:D3-A3 / 59 | 断言 9：缓存文件是非法 JSON → 重探，不崩，退出 0 | 当前证据满足 | 检测断言 9 验证坏 JSON 静默重探；首轮通过。（DET, VAL, F8） |
| detection:D3-A4 / 60 | 缓存文件写在 ${TMPDIR} 下，**不写进任何项目目录** | 当前证据满足 | CACHE_FILE 从 TMPDIR 派生；生产 hook 不向业务项目写缓存。源码依据和本批隔离夹具一致。（DETPY, SUP, F8） |
| detection:D3-V1 / 63 | 3 条断言全绿 | 当前证据满足 | 当前 7/8/9 三个缓存断言存在且首轮通过。（DET, VAL, F8） |
| detection:D3-V2 / 64 | 变异：让缓存永不过期 → 断言 8 必须变红 | 当前证据满足 | MUT-04-never-expire-cache：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT, F8） |
| detection:D3-V3 / 65 | 手工确认跑完之后项目目录里没有新增文件 | 当前证据满足 | FOOTPRINT-01：在独立无 HEAD Git 业务夹具运行三个 hook，前后目录项/内容哈希/权限/修改时间（含 .git）相同，缓存位于外部 TMPDIR；单个受控样本，不证明一切业务环境。（DETPY, MUT, F8） |
| detection:D4-A1 / 78 | 断言 11：把 hook 的 stdout 喂给 python3 -c 'json.load(sys.stdin)'，空则跳过，非空必须解析成功 | 当前证据满足 | 检测断言 11 将非空 stdout 做 JSON 解析，多场景均通过。（DET, VAL, F8） |
| detection:D4-A2 / 79 | 断言 12：构造一个探测内部失败点（比如缓存目录不可写）→ 仍退出 0、不注入噪音 | 当前证据满足 | 12a/12b 断言覆盖缓存写失败和目录建不出的降级；首轮通过。（DET, VAL, F8） |
| detection:D4-A3 / 80 | JSON 结构与 spec-guard 一致：hookSpecificOutput.hookEventName / additionalContext | 当前证据满足 | detect/route 经 JSON serializer 输出 hookSpecificOutput 字段；JSON 断言及两个本批 scaffold 成功解析。（DETPY, ROUTE, SUP, VAL, F8） |
| detection:D4-A4 / 81 | 注入的内容**只有事实**，不含「你应该派给 Codex」这类建议（那是 routing 的活） | 当前证据满足 | detect.py 自身注入只含基础条件事实；提议式路由措辞在 route.sh，组合 prompt 允许注入路由指针，职责没有混用。（DETPY, ROUTE, PROMPT, F8） |
| detection:D4-V1 / 84 | 2 条断言全绿 | 当前证据满足 | 当前 JSON/内部失败 11/12a/12b 场景首轮通过；旧“2 条”只对应场景组，不倒推早期运行。（DET, VAL, F8） |
| detection:D4-V2 / 85 | 变异：在输出前面多打一行普通文本 → 断言 11 必须变红 | 当前证据满足 | MUT-05-extra-plain-text：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT, F8） |
| detection:D5-A1 / 98 | hooks/doctor.sh + commands/doctor.md（allowed-tools: Bash，脚本按 ${CLAUDE_PLUGI… | 当前证据满足 | doctor 文件、命令及 Bash 工具声明存在，脚本路径引用 CLAUDE_PLUGIN_ROOT。（DOCMD, DOCTOR, F8） |
| detection:D5-A2 / 99 | 断言 13：AGENTS.md 含「等确认 / 先出方案 / 不要直接开始改代码」这类模式 → 报告风险并给出修法（加交互式条件） | 当前证据满足 | 检测断言 13 校验规则风险与非交互修法，13b 还校验已豁免场景；首轮通过。（DET, DOCTOR, VAL, F8） |
| detection:D5-A3 / 100 | 断言 14（**反向**）：AGENTS.md 干净 → **不报** | 当前证据满足 | 检测断言 14 校验干净规则不报告风险；首轮通过。（DET, VAL, F8） |
| detection:D5-A4 / 101 | 断言 15：没有 ~/.codex/AGENTS.md → 不报错 | 当前证据满足 | 检测断言 15 校验无全局规则文件不报错；首轮通过。（DET, VAL, F8） |
| detection:D5-A5 / 102 | AGENTS.md 路径可覆盖，测试用临时文件，**绝不读用户真实的那份** | 当前证据满足 | doctor 支持 CODEX_AGENTS_FILE；检测套用临时规则文件，backend 测试隔离 HOME/CODEX_HOME。（DOCTOR, DET, BACK, F8） |
| detection:D5-V1 / 105 | 3 条断言全绿，**19 条全绿** | 当前证据满足 | 13/14/15 的对应场景已通过，当前检测套总数为 19，不能证明历史三条新增时就已运行。（DET, VAL, F8） |
| detection:D5-V2 / 106 | /bin/bash scripts/validate.sh 通过 | 当前证据满足 | 首轮总验证退出 0，产品源码与该基准不变。（VAL, F8） |
| detection:D5-V3 / 107 | 变异：把「干净就不报」改成「总是报」 → 断言 14 必须变红 | 当前证据满足 | MUT-06-doctor-false-alarm：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT, F8） |

## routing

| 条目 / 原文来源行 | 原条件（短览） | 当前裁决 | 理由及证据 |
|---|---|---|---|
| routing:R1-A1 / 14 | R1 断言：缓存说不可用 → 零注入 | 当前证据满足 | 当前路由 R1 校验不可用缓存零注入；首轮通过。（RT, VAL） |
| routing:R1-A2 / 15 | R2 断言：缓存缺失 → 零注入（不猜） | 当前证据满足 | 当前路由 R2 校验缺失缓存零注入；首轮通过。（RT, VAL） |
| routing:R1-A3 / 16 | R3 断言：缓存说可用 → 一行合法 JSON | 当前证据满足 | 当前 R3 校验有效缓存单行 JSON，且不重探；本批两个 scaffold 也实际解析通过。（RT, SUP, VAL） |
| routing:R1-A4 / 17 | R4 断言：注入内容含「等用户确认」之意，**不含**「我这就派」这类越闸措辞 | 当前证据满足 | 当前 R4 同时校验确认闸门措辞及禁止越闸词；这是指令文本证据。（RT, ROUTE, VAL） |
| routing:R1-A5 / 18 | R5 断言：任何情况的 stdout 为空或可被 json.load 解析 | 当前证据满足 | 当前 R5 多种缓存输出为空或合法 JSON；首轮通过，不延伸到一切未枚举环境。（RT, VAL） |
| routing:R1-A6 / 19 | R6 断言：缓存损坏/不可读 → 退出 0、零噪音 | 当前证据满足 | 当前 R6 校验坏缓存零输出/零噪音/退出 0；所有权限异常只由 try/except 静态兜底，不宣称穷举。（RT, ROUTE, VAL） |
| routing:R1-A7 / 20 | route.sh **不重新实现探测** —— 只读缓存（判据只能有一份实现） | 当前证据满足 | route 从 detect 导入 read_cache，未独立做 CLI 探测；R3 验证调用日志不增加。（ROUTE, RT, VAL） |
| routing:R1-A8 / 21 | hooks.json 增加 route.sh 的 UserPromptSubmit 注册，脚本缺失不报错 | 现行合同替代 | 当前只注册 prompt.sh 串行 warm→route，取消独立并行 route handler；冷缓存/单 handler 回归通过，旧注册形态已替代。（HOOK, PROMPT, BACK, REL） |
| routing:R1-V1 / 24 | /bin/bash plugins/delegate/tests/test-routing.sh 退出 0 | 当前证据满足 | 首轮路由产品套 9 通过、0 失败。（RT, VAL） |
| routing:R1-V2 / 25 | 变异：让不可用时也注入 → R1 必须变红 | 当前证据满足 | MUT-07-unavailable-routing-output：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT） |
| routing:R1-V3 / 26 | 变异：注入里加一句「我这就派给 Codex」→ R4 必须变红 | 当前证据满足 | MUT-08-cross-confirmation-gate：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT） |
| routing:R2-A1 / 39 | R7 断言：SKILL.md 含分流表的六类活（审查 / 摸结构 / 定位 / 单 task 实现 / 批量机械改动 / 不该派的） | 当前证据满足 | R7 验证六类分流表可读；实际六类宿主决策不是此静态断言的结论。（RT, SKILL, VAL） |
| routing:R2-A2 / 40 | R8 断言：含「不许自动派」的明文 | 当前证据满足 | R8 精确校验“绝不自动派”文字；首轮通过。（RT, SKILL, VAL） |
| routing:R2-A3 / 41 | 三条回来之后的纪律写明：不 cat 整个日志、--write 必看 git 验收块、--write 需用户当轮明确要求 | 当前证据满足 | skill 与主命令都写明按片段读日志、失败也看 Git、当轮授权 --write。（SKILL, CMD） |
| routing:R2-A4 / 42 | frontmatter 的 description 写得能被匹配到（参照 spec-guard 的经验：措辞决定会不会被加载） | 当前证据满足 | B2：原生交互自然提示实际调用 Skill(delegate:delegate-routing)，JSONL/TTY/debug直接证明加载，不是仅列表或 hook 指针；单次提示样本，不保证所有情境。（SKILL, BULK） |
| routing:R2-V1 / 45 | 2 条断言全绿 | 当前证据满足 | 当前 R7/R8 两个文本断言首轮通过。（RT, VAL） |
| routing:R2-V2 / 46 | 变异：删掉「不许自动派」那句 → R8 必须变红 | 当前证据满足 | MUT-09-remove-auto-ban：F8 修复前临时产品副本的特定故意错误触发指定断言失败，无变异基线和还原后套通过；仅证明此反向样本，历史完成/批准仍未知。（MUT） |
| routing:R3-A1 / 59 | 三种结局：通过 / 不通过 / **没跑起来**（退出码 0 / 1 / 2） | 当前证据满足 | propose judge 实现 0/1/2，7 项判决器正反自检在首轮实际通过。（PROP, VAL） |
| routing:R3-A2 / 60 | --scaffold-only 免费建脚手架并自检 hook 是否激活 | 当前证据满足 | 本批 SUP-25 实际 --scaffold-only 退出 0、route JSON 校验通过；这不是宿主激活实测。（SUP, PROP） |
| routing:R3-A3 / 61 | --selftest 喂已知输入给判决器自己（免费，进 validate.sh） | 当前证据满足 | propose --selftest 7 通过并纳入 validate；当前实际首轮结果可追溯。（PROP, VALIDATOR, VAL） |
| routing:R3-A4 / 62 | evals/_preflight.sh 核对「装着的插件内容 == 仓库内容」，不一致就拒跑 | 现行合同替代 | 当前 eval 使用 --plugin-dir 加载源码并原生 validate 源目录；不再比较安装缓存和仓库是否相同。（PREF, PROP, REL） |
| routing:R3-A5 / 63 | 「没有自动调」判**桩的调用日志**（文件系统）；「提议了」判 transcript —— | 当前证据满足 | 无自动 exec 检查调用日志，提议只读 transcript 作为观察项；注释说明 headless 不判提议失败。（PROP） |
| routing:R3-V1 / 67 | --selftest 通过并接进 validate.sh | 当前证据满足 | propose --selftest 7 通过并纳入 validate；当前实际首轮结果可追溯。（PROP, VALIDATOR, VAL） |
| routing:R3-V2 / 68 | --scaffold-only 通过 | 当前证据满足 | 本批 SUP-25 免费 scaffold 实际通过。（SUP） |
| routing:R3-V3 / 69 | 真跑一次通过 | 当前证据满足 | 具体批准的64文件/16640行原生单样本实际加载Skill，推荐具体只读委托、默认模型并等用户确认，exec为0、业务内容快照相同；仅此样本，不证明所有提示、失败重派授权或完整交互，历史批准未知。（PROP, SKILL, PROPOSE） |
| routing:R4-A1 / 82 | 处理组（决策已定、只剩执行）→ 应当提议 | 当前证据满足 | B1：恢复认证后获新批次具体批准，既有差分入口退出0，处理组首行判断：委托、对照组判断：自己做，两组 exec=0；以前 OAuth NORUN 保留为旧快照，一次样本不代表所有模型情境。（FIT, BULK, LIVE） |
| routing:R4-A2 / 83 | 对照组（还需取舍，比如「这两个方案选哪个」）→ **不应当**提议 | 当前证据满足 | B1：恢复认证后获新批次具体批准，既有差分入口退出0，处理组首行判断：委托、对照组判断：自己做，两组 exec=0；以前 OAuth NORUN 保留为旧快照，一次样本不代表所有模型情境。（FIT, BULK, LIVE） |
| routing:R4-A3 / 84 | **对照组同时充当脚手架自检**：它要是也提议了，处理组的结果无从归因， | 当前证据满足 | routing judge 对照组主张委托返回 NORUN，12 项自检覆盖两组都委托及格式失败。（FIT, VAL） |
| routing:R4-A4 / 86 | --selftest + --scaffold-only（免费） | 当前证据满足 | 首轮 routing 自检 12 通过；本批 SUP-26 scaffold 实际退出 0。（FIT, SUP, VAL） |
| routing:R4-V1 / 89 | --selftest 通过并接进 validate.sh | 当前证据满足 | routing-fitness --selftest 纳入总验证并实际 12 通过。（FIT, VALIDATOR, VAL） |
| routing:R4-V2 / 90 | 真跑一次，两组结果分开 | 当前证据满足 | B1：恢复认证后获新批次具体批准，既有差分入口退出0，处理组首行判断：委托、对照组判断：自己做，两组 exec=0；以前 OAuth NORUN 保留为旧快照，一次样本不代表所有模型情境。（FIT, BULK, LIVE） |

## 证据索引

| ID | 来源 | 作用 |
|---|---|---|
| VAL | [docs/process/2026-10-08-adoption/report.md](../process/2026-10-08-adoption/report.md)，行 20 | 首轮接入实际总验证：52 Shell、17 Python、判决器自检。 |
| MAN | [scripts/check-manifests.py](../../scripts/check-manifests.py)，行 34 | 现行清单结构与必填字段；原生清单核验见首轮报告。 |
| MP | [.claude-plugin/marketplace.json](../../.claude-plugin/marketplace.json)，行 2 | marketplace 清单采用 name/owner/plugins/source；没有根 version 字段。 |
| PM | [plugins/delegate/.claude-plugin/plugin.json](../../plugins/delegate/.claude-plugin/plugin.json)，行 2 | 插件 version 0.4.0；命令自动发现而非清单 commands 声明。 |
| STUB | [plugins/delegate/tests/stub-codex](../../plugins/delegate/tests/stub-codex)，行 3 | argv 日志及 STUB_* 行为；不含模型调用。 |
| CH | [plugins/delegate/tests/test-channel.sh](../../plugins/delegate/tests/test-channel.sh)，行 71 | 当前通道断言套；具体断言编号在逐项理由中。 |
| REG | [plugins/delegate/tests/test-channel-regressions.py](../../plugins/delegate/tests/test-channel-regressions.py)，行 66 | 生命周期/Git/错误回显回归。 |
| BACK | [plugins/delegate/tests/test-backend.py](../../plugins/delegate/tests/test-backend.py)，行 43 | 认证、缓存身份、冷启动及 live harness 的桩回归。 |
| WRAP | [plugins/delegate/scripts/codex-exec.sh](../../plugins/delegate/scripts/codex-exec.sh)，行 5 | 现行参数、执行形态、日志与 Git 输出实现。 |
| VALIDATOR | [scripts/validate.sh](../../scripts/validate.sh)，行 20 | 语法、模式、清单、eval 与产品套总入口。 |
| DET | [plugins/delegate/tests/test-detection.sh](../../plugins/delegate/tests/test-detection.sh)，行 34 | 当前 19 条检测断言；旧 auth.json 标签仅用于测试桩。 |
| DETPY | [plugins/delegate/hooks/detect.py](../../plugins/delegate/hooks/detect.py)，行 17 | CLI 身份、TTL、原子缓存及事实输出。 |
| BEPY | [plugins/delegate/scripts/backend.py](../../plugins/delegate/scripts/backend.py)，行 22 | 当前以 CLI ChatGPT 登录为判据，不直接读取 auth.json。 |
| HOOK | [plugins/delegate/hooks/hooks.json](../../plugins/delegate/hooks/hooks.json)，行 3 | 两个事件；UserPromptSubmit 只注册串行 prompt.sh。 |
| PROMPT | [plugins/delegate/hooks/prompt.sh](../../plugins/delegate/hooks/prompt.sh)，行 5 | 先 warm，后 route 的串行编排。 |
| DOCMD | [plugins/delegate/commands/doctor.md](../../plugins/delegate/commands/doctor.md)，行 3 | doctor 命令的宿主脚本路径和工具声明。 |
| DOCTOR | [plugins/delegate/hooks/doctor.sh](../../plugins/delegate/hooks/doctor.sh)，行 19 | 规则诊断路径覆盖、中文启发式和不修改规则。 |
| CMD | [plugins/delegate/commands/delegate.md](../../plugins/delegate/commands/delegate.md)，行 4 | 现行委托命令声明、确认、timeout 和返回纪律。 |
| RT | [plugins/delegate/tests/test-routing.sh](../../plugins/delegate/tests/test-routing.sh)，行 64 | 当前 9 条路由断言。 |
| ROUTE | [plugins/delegate/hooks/route.sh](../../plugins/delegate/hooks/route.sh)，行 10 | 只读共用缓存、单行 JSON、确认指针。 |
| SKILL | [plugins/delegate/skills/delegate-routing/SKILL.md](../../plugins/delegate/skills/delegate-routing/SKILL.md)，行 3 | 分流表、提议纪律、description 和回来后规则。 |
| PREF | [evals/_preflight.sh](../../evals/_preflight.sh)，行 7 | 显式源码加载及原生校验，已不比较安装缓存内容。 |
| PROP | [evals/propose-not-auto.sh](../../evals/propose-not-auto.sh)，行 28 | 判决器硬条件为无自动 exec；提议只是观察项。 |
| FIT | [evals/routing-fitness.sh](../../evals/routing-fitness.sh)，行 44 | 处理/对照组完整首行判决及 NORUN 条件。 |
| REL | [docs/releases/v0.4.0.md](../releases/v0.4.0.md)，行 17 | 0.4.0 已记录认证、串行 hook、模型样本及体量比变更。 |
| HIST | [docs/verification/historical-evidence.json](historical-evidence.json)，行 2 | 精确本地证据提交 f961e...；先前样本的源码归属限制见历史摘要。 |
| SUP | [docs/verification/2026-10-08-supplemental-results.json](2026-10-08-supplemental-results.json)，行 6 | 本批 26 个受控离线样本，含两个免费 scaffold；不是永久回归或真实宿主验收。 |
| MUT | [docs/verification/2026-10-08-mutation-results.json](2026-10-08-mutation-results.json)，行 6 | 本批 9 个特定变异覆盖 10 条原条件及零足迹样本；含工具声明引入提交与首轮外层 CLI 依赖记录。 |
| F8 | [docs/verification/2026-10-08-f8-applied-results.json](2026-10-08-f8-applied-results.json)，行 16 | 批准单文件测试隔离修复后，当前仓库两个探测反例和无外层 CLI 总验证通过，工作区尚未提交。 |
| LIVE | [docs/verification/2026-10-08-live-results.json](2026-10-08-live-results.json)，行 41 | 当前通道真实只读样本通过；Claude 路由两组认证 NORUN，未验收路由决策。 |
| ADR | [docs/decisions/ADR-001-command-tool-scope.md](../decisions/ADR-001-command-tool-scope.md)，行 5 | 本次具体批准的当前工具取舍，不追认历史批准。 |
| BULK | [docs/verification/2026-10-08-bulk-results.json](2026-10-08-bulk-results.json)，行 19 | 四个 Claude 会话/一次真实 Codex；差分、原生 Skill/斜杠与快照证据；主动推荐保持未验证。 |
| PROPOSE | [docs/verification/2026-10-08-proposal-results.json](2026-10-08-proposal-results.json)，行 3 | 具体批准的较大原生单会话：实际加载、推荐、默认模型、等待、零exec及内容快照；完整互动限制另保留。 |

## 判断边界

- 现行合同替代包括 auth.json 判据、固定 40 倍、旧固定测试总数、安装缓存一致性、独立 route handler 等；不是新发现的产品回归。
- channel:7-A1 的旧窄 allowed-tools 与当前 Bash 声明不同；本次当前批准已记录 ADR 并归为替代，原历史批准仍未知。
- 119条原条件当前裁决已收束为106/13/0；指定提议案例通过不证明所有提示或失败恢复纪律。完整产品覆盖缺口和所有历史批准未知仍独立保留。
- 裁决不会启用文档基线、事项账本或 capability history，不会导入或改写旧 tracker 状态。
