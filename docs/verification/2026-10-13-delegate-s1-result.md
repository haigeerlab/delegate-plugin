# S1入口验收：正向未启动模型，停止；监督脚本路径缺陷已修复源码

2026-10-13，仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，claude-review。用户明确批准原话“批准S1”。

## S1实际结果

当前Codex主会话已应用真实安装的delegate source-command-review技能，按命令模板调用启用插件列表返回的本地源码根目录。正向只调用一次，4.405秒退出127：conditions_missing / inconclusive、backend_started=false、cleanup confirmed、anchor_start_unverified。四文件均未审，observed_models为空；当时源码、输入、被观察settings/登记未变。没有UI手动点击Codex选择器，不能声称这个动作发生。[完整JSON](2026-10-13-delegate-s1-result.json)。

故障发生于runtime预检的可信监督进程启动，Claude模型审查未开始。费用和用量后端未提供，不填0美元。依据S1“失败或未知即停”，没有再次调用review、没有反向执行、没有向“Claude验收会话”发送交接。只读查询过Agent-Relay目录，没有注册/发送/唤醒。原批forward-started标记保留，批准S1不延伸到修复后的重新执行。

## 已确认缺陷NATIVE-START-001

Required / P2，纳入现有Task6，不新建外部事项。正向驱动把PATH限定为已批准Node加/usr/bin/bin，wrapper实际选择Xcode Python3.9.6；外层驱动是已存在Python3.10.7。旧运行器要求launchd直接读取本地插件在Documents中的review_macos.py。零模型探针复现ready缺失、last exit code2；只对固定受信监督脚本捕获启动stderr，得到明确EPERM“can't open file …review_macos.py”。相同Xcode Python能运行，路径改变后成功；不能归因为Python版本太低，也没有安装升级Python。

修复：主进程仅把review_macos.py/review_result.py/claude_review.py三个受信代码文件暂存到既有私有control树，目录0700/文件0600，launchd从那里加载。该步骤没有拷贝凭据、业务数据或全局配置；OS继续禁止reviewer读写control树；工具/网络/身份/期限/进程归属和清理不变，没有扩大权限、读取权限数据库或关闭系统保护。确切OS拒绝机制未调查；TCC/应用身份只能是候选，不能宣称已证明。此前所有间歇失败也不能追认为同根因。

实际同解释器对照：旧路径4.063秒失败；临时受信代码路径0.317秒成功；修复后从本地源码调用0.183秒成功，均零Claude/模型/认证调用。新注册回归先以正确ProgramArguments索引断言旧实现失败，再修复；9项native合同通过。最初测试原型索引误写3，已更正为2后重新取得有意义的红结果，不能把那个原型失败当回归证据。

## 免费验证与限制

源代码修复后宿主免费总套143 Python/53 shell/19 eval通过。首次默认工具沙箱总套因service测试读取自建进程的ps被拒而失败；在宿主相同免费套通过，两次结果分别保存，未删除断言或跳过套件。

实际Mac内核生命周期/OS拒写拒读14项通过，其中新增reviewer无法读取暂存监督代码；超时、INT/TERM/HUP、detached/double-fork、父先退、无关进程和代际保护继续通过。

公共假CLI首轮6方法：2失败/1错误（预检超时、长TMPDIR外层20秒超时、取消准备10秒未启动）；没有掩盖。定向复验3方法后空/坏/拒权及长路径通过，取消仍失败；独立时序探针3.224秒见替身init，SIGTERM退出143/cancelled/cleanup confirmed；在没有同时运行总套时原取消方法一次串行复验通过。最后为核验连跑干扰，在无其他验证套同时运行时完整公共假CLI套6方法/8场景23.280秒通过；前述失败记录保留，首轮时间差根因未知，并发负载仅候选，不证明长期稳定性。没有放宽生产期限或测试断言，也没有重复真实模型。

私有日志：`/path/to/private-evidence,-host}.log`、`delegate-s1-anchor-macos-regression.log`、`delegate-s1-anchor-public-{fixture,focused,cancel-serial,serial-full}.log`；探针和原S1报告在批次目录，均合成/必要诊断，不倾倒原版过程。Task2/6/8仍未整体勾选。

## 安装与下一步

这次只改源码3个产品文件及双语规格/ADR，没有更新正常安装或全局配置。Claude缓存仍完整匹配修复前61文件；命令内容没有变化，已有四入口显示验收有效，但不能把缓存说成已含监督加载修复。Codex本地启用根目录指向源码，已获得新实现；旧固定真实审查证据只对应旧代码版本。

修复后的真实模型、新命令双向调用未验。下一步先由用户审阅这次有限修复与限制；如要同步Claude缓存、再次执行S1对应范围，安装与新增模型/交接须具体另授权并重新固定源码，不重放原S1或自动重试。提交、推送、发布未执行。最终人工Checkpoint3仍未通过。

## 限定修复供审

相对S1前固定源码的三文件delta（本机私有证据，原路径未公开）、摘要（本机私有证据，原路径未公开）。五维定向核对：正确性由同解释器路径对照及红→绿支撑；小段暂存逻辑在现有运行器内，未增加后端/公共参数或通用平台；control的OS拒读拒写保持并新增实际拒读；仅复制三个固定受信模块，不触碰凭据/业务数据；复制量有固定文件集合，生产执行期限不变。该复核不是独立模型或完整安全审计。完整公共假CLI最后串行套已过，但不能由此追认首轮失败或证明长期稳定性。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
