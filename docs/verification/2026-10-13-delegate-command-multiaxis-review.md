# delegate 命令与功能多维审查

2026-10-13，`delegate-plugin` / `codex/spec-guard-conventions-public`，模块 `claude-review`。用户请求审查当前斜杠命令及功能是否合理。本批完成限定审查，结论 **Request changes**：四个核心命令职责和命名合理，保留；确认3项Required问题，先修再复审，不认可当前版本直接交付。

基准HEAD `823c42383cf055ea8af99256618daf6212d10735`，实际对象为当前未提交源码；28份源码/合同/文档的摘要固定于 `.agent/acceptance/command-review-20261013/source-manifest.json`。覆盖四命令、路由skill、两层参数解析、共同范围/报告、实际执行边界接点、相关测试及README/规格。未泛扫整个仓库；未完整重审Darwin ABI、原版所有权限行为或供应链漏洞。

## 命令布局与功能判断

| 核心入口 | 职责 | 判断 |
|---|---|---|
| `/delegate:review` | 两后端、明确范围、只读、共同报告 | 合理；用户按审查目的进入，再选执行者 |
| `/delegate:run` | 已确认任务交给Codex，默认只读，显式write才修改 | 合理；与审查分开，不让Claude只读后端承担修复 |
| `/delegate:doctor` | 所选后端无模型诊断，条件和未验证项分开 | 合理；参数/诊断体验可改进 |
| `/delegate:help` | 能力、范围、参数和迁移帮助 | 合理；保留轻量入口，详细内容移出命令模板 |

不建议增加 `/codex-review`、`/claude-review` 等按模型/执行器命名的并列入口。`--backend codex|claude-code` 和 `--model` 分开正确；默认Codex及显式选择保持现有调用兼容。自动选相反宿主、失败换执行器、把多模型视角当准确率证明都不应加入。

模型数量增加不等于后端数量增加：同一CLI的新模型仍由其 `--model` 和验证管理；只有新增另一种执行器，才扩展适配与能力/参数/权限/结果映射。当前两个后端用简单分派足够，不需要提前造通用调度平台。Codex的实际入口是迁移skill，Claude是命名空间斜杠；文档区分两者合理，不应假造同名UI能力。

## 已确认问题（必须修正）

### CMD-001 · Required / P1：范围外文件名能阻断限定审查

定位：`plugins/delegate/scripts/review_context.py:196`、`:205`、`:220`；路径验证 `:27`。

`capture_document` 对整个仓库的untracked列表、树/index条目先调用严格 `names/paths`，之后才按scope过滤。合法文件名中的方括号在scope传输合同中被拒绝，因此**不在审查范围内**的文件也能使输入采集失败。

实际复现：对正常合成仓库执行 `review --paths src/a.py --dry-run` 先成功；仅新增未跟踪 `outside/[id]/page.tsx` 后，相同命令分别选择codex和claude-code均退出127、diagnostic=scope_path_invalid、backend_started=false。没有读取该文件内容或启动模型，失败被正确标为未完成，但正常的限定审查因此不能使用。动态路由目录等普通项目结构会触发这一问题。

建议：区分仓库状态元数据与要传输的路径；先通过安全的字面pathspec/scoped筛选限定候选，再验证真正选中的文件及Spec/Plan。范围外名字只影响必要的dirty事实，不应被当成用户输入路径判非法；不能靠要求用户重命名无关文件、放宽穿越/链接验证或扩大审查范围解决。

修复验收：范围外已追踪和未跟踪方括号路径分别存在时，两后端相同限定范围仍成功预览、摘要不变、排除文件不进快照；真正非法请求路径继续拒绝。现有测试未覆盖本例，22项相关回归通过不能证明这条合同成立。

### CMD-002 · Required / P2：模型归属校验不完整，旧入口还有另一套规则

定位：`plugins/delegate/scripts/delegate_backend.py:58`，旧入口 `plugins/delegate/scripts/codex-exec.sh:76`。

Python只对整个slug的前缀/精确别名做家族识别，尽管语法允许提供商前缀；Bash旧入口另外维护区分大小写的case。

实际证据（全部是假CLI或纯解析）：

- 公共 `run --model anthropic/claude-sonnet-5-5` 退出0，**假Codex exec实际收到** `-m anthropic/claude-sonnet-5-5`。
- `--backend claude-code --model openai/gpt-5 --review-context fixture.json` 被Python解析接受；本例只验证解析，没有启动Claude。
- 直接旧 `codex-exec.sh --model SONNET` 退出0，假Codex收到SONNET；公共Python入口则会识别其归属Claude。

这违反明确的“后端和模型不能混用”要求。真实CLI后来可能报错，不能替代在封装内一致识别已知对方模型，也不能让错误参数先进入认证或模型调用。

建议：复用一个后端专属模型校验，统一已知家族/别名的大小写和提供商前缀处理，公共review/run及旧入口使用同一规则；对未知自定义slug采取明确、已记录的策略，保留兼容范围，不推断新的后端、不偷偷换模型。不要为方便维护把所有未来模型锁死成静态发布列表。

修复验收：上述三例在任何CLI探针/exec前明确退出64；已知合法模型、已有自定义slug合同和默认模型行为保持；假CLI记录证明没有跨传参数。增加相应测试，不只测裸sonnet/gpt名称。

### DOC-001 · Required / P2：“最新状态”与当前实际结果矛盾

定位：`README.md:7`、`README.en.md:7`；参考当前 `docs/verification/2026-10-13-delegate-s2-resume-result.json`。

两版README首屏仍说S1修复后未真实模型复验、Claude缓存未同步。实际S2已经同步61文件、四入口核验、最新源码双向各一次4/4通过。该段标为“最新”，不能靠让用户翻后面的历史记录解释，会再次造成“代码是否开发完、到底能不能用”的混乱。

建议：双语README首屏只保留稳定产品范围、当前发布/未发布身份和一条当前状态链接；把S1失败、恢复、安装控制器等时间线留在verification。当前普通双向通过与完整安全未验分开表述；同步未发布说明里过期的“未安装”等陈述，不删除原始失败证据。

验收：两版首屏与S2最终记录一致，明确普通双向通过、尚未发布和仍未验安全项；读者无需阅读长时间线即可判断当前阶段。

## 可选改进与已知限制

| ID / 级别 | 观察、建议与边界 |
|---|---|
| UX-001 · Optional / P2 | paths/module默认HEAD是已定的范围策略，应保留。复现显示dirty工作区在dry-run有标记，正常最终报告只含baseline/hash，不含dirty或排除未提交的摘要，stderr也无提醒。建议普通输出醒目显示读取版本及未提交内容是否纳入，避免审错版本；不新增每次人工闸门或静默改默认。 |
| UX-002 · Optional / P2 | `review_doctor.py --help` 和 `--backend=claude-code` 实测退出64，而review/run支持标准help/等号参数。建议共用普通参数解析，并输出实际解析的CLI/Node/SRT/Python路径与可核实版本及补条件办法，凭据/原始认证日志仍不输出；保留既有“诊断完成不等于后端可用”语义。 |
| UX-003 · Optional / P3 | 四个核心命令之外，路由知识skill也显示为delegate:delegate-routing（已有原生菜单证据），职责是判据而非用户操作。可在Claude将其设为 `user-invocable: false`，保留模型按显式意图使用的能力；这是Claude扩展元数据，Codex显示/自然触发须另核验，不能声称两宿主自动同时隐藏。[官方技能调用控制](https://code.claude.com/docs/en/skills#control-who-invokes-a-skill)。本批未修改元数据或加载。 |
| ARC-001 · Optional / P2 | 公共Mac路径仍从review_guest复用快照工具，guest_entry/service/transport/network旧原型形成额外层次，当前公共CLI不分派到它们。发布包可另做限定清理：先分离真正共用的snapshot工具，再移出仅历史实验用的执行入口，保留原始证据；不把“guest”名字等同未使用，不直接整批删除。本轮不做无关重构。 |
| REL-001 · FYI | 清单仍0.4.0是未发布源码阶段的刻意状态，本身不判当前代码bug；但普通update已实际因同版本保留旧内容。下一发行建议按已有unreleased计划使用0.5.0，注明slash破坏迁移和Mac依赖。不自动安装、改版本、发布或保留两套长期公开slash别名。 |

## 五维结论与证据边界

| 维度 | 结论 |
|---|---|
| 正确性 | CMD-001/002为已复现缺陷。review/run目的分开、非法write/后端参数拒绝、执行状态与结论分离合理。 |
| 可读性与简单性 | 四命令比旧delegate一口承接所有目的清楚；帮助模板迁移后doctor1038/run1843/review3528/help3586 UTF-8字节，都在已核实Codex4000预算内。保留短入口，避免继续塞历史叙事。 |
| 架构与扩展 | 两宿主共享公共入口、宿主/后端/模型分离、BACKENDS能力声明正确；model校验Python/Bash重复需要收束，旧实验路径可另切片简化；更多模型先不增加执行器层。 |
| 安全 | 已有OS拒写/进程清理和S2普通双向证据，不从prompt/allowedTools推导沙箱。此批未确认新的越权或凭据泄露；不是完整安全认证。主动模型越权/递归事件、认证刷新、异常自然helper仍未验证，不能自动勾Task2/6/8。入口allowed-tools:Bash是主会话工具授权，不能与子审查者Read限制混为一谈。 |
| 性能 | 单次同步和有限快照/输出上限合理，CLI第一版无需SDK/调度。范围采集仍全仓枚举树/index/status，工作量随仓库规模增长且可能先碰全局输出上限，CMD-001的范围前置筛选也改善此问题；没有大型仓库耗时基准，不给速度结论。 |

功能能力矩阵的“write=true”描述的是Codex后端总体能力，当前review仍permission=read-only且拒write；需要区分后端能力与本次有效权限，不把capabilities当授权。实际费用/模型只采用后端提供的口径；当前不同模型发现同一合成缺陷不证明总体准确率更高。

## 验证与本批收束

临时源码副本中免费相关回归 **22项通过**：CLI13、backend7、migration2。分别切换默认review后端、反转选中范围存在性条件，两项mutation都使既有公共Codex审查测试实际失败；各自恢复副本后该测试通过。原28份产品/文档摘要全部不变。两处新缺陷不是mutation结果，而是独立假CLI/合成仓库复现；指出了当前测试缺口。

辅助探测曾误用 `--model` 查实际为 `-m` 的假CLI记录；mutation辅助断言还曾把stdout诊断当成unittest stderr字段查找。两处辅助错误已修正，副本始终恢复，不算产品缺陷，具体事实保留在私有探测记录。没有真实模型、安装、全局配置、消息交接或真实事项/Git交付操作；不重复S2已消费调用。

机器证据 `command-multiaxis-review.json`，私有探测细节 `.agent/acceptance/command-review-20261013/probe-result.json`。本次审查没有新增源码实现或删代码。三项Required为本地审查ID，未冒充Issue/Local事项ID，没有自动入账或外部写入。

本批限定审查已完成：3确认Required、4Optional、1FYI、0待调查候选；28份文件按声明的接口/接点纳入核对，不按行宣称所有执行边界代码都已审完。下一步优先在claude-review原plan/todo内处理CMD-001→CMD-002→DOC-001，不重新全仓审查；可选项另决定，不在本轮自动改命名/默认值或扩后端。Checkpoint3保持未批准，所请求审查不构成提交/发布授权。
