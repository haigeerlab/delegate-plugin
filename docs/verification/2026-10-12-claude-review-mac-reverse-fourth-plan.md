# 反向第四批：固定 Node 运行时后的验收预览

日期2026-10-12。仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`。仅免费准备，尚未发送第四批或启动模型；[固定摘要](2026-10-12-claude-review-mac-reverse-fourth-preview.json)。

## 第三批结果与根因

第三批已在目标报告直接人类“同意”后执行一次，宿主内核身份/祖先通过，公共wrapper退出127/0.472秒，conditions_missing/inconclusive，backend_started=false，4文件均未审，无发现不等于通过。驱动marker只代表一次wrapper尝试，非模型/API请求。来源独立核对输入/上下文/HEAD/status不变，无攻击标记。[实际第三批结果](2026-10-12-claude-review-mac-reverse-third-result.json)。

目标Bash的Node12.22.12排在PATH最前，pnpm Codex入口的顶层await在该运行时触发SyntaxError；版本探针即失败，不是认证或额度结论。来源免费Node12/Node24探针复现：前者退出1，后者正常返回codex-cli0.160.1。未复制凭据、登录或改用户环境。

新增安全阶段诊断已实现并回归：公共报告保留codex_preflight_failed，加入缺CLI/版本探针/登录探针/登录方式分类；不保存原始输出，旧check两值API/旧行为保持。3个故障子例先红后绿，公共执行9测试通过，完整免费总套138 Python/53 shell/19 eval通过。[修复证据](2026-10-12-delegate-preflight-fix.json)。

## 第四批固定范围

- 真实主会话：唯一“Claude验收会话”，Claude目录报告2.1.295；固定上次已实际核验的当前进程身份，发送前再核实，任何重启/变化停止，不能自动更新已批准身份。
- 后端：Codex CLI0.160.1、CLI默认模型；实际模型无可靠证据时unknown。四文件不变：src/pricing.py、REVIEW_DATA.md、SPEC.md、PLAN.md，固定原Git基准，排除excluded.py，须干净。
- 运行时：已有 `/path/to/user-home/.nvm/versions/node/v24.18.0/bin/node`，版本和SHA固定；驱动核对SHA，仅在本次子进程PATH前置Node目录和Codex目录，不安装、改全局PATH或配置。已免费核实在该环境Codex版本探针可运行，未检查认证/额度。
- 当前源码公共review入口，只读沙箱，inline文件内容、禁用shell/apps/plugins/multi_agent、搜索禁用/MCP为空；不执行源码、不改文件或再次派活。
- 一次运行/180秒；Codex本封装无美元或轮次硬上限，交接和模型可能耗用额度。失败/结果未知停止，不重试、换后端或修改固定事实。
- 最终报告、过滤日志与摘要分开，缺用量/模型证据不写零或猜测；独立核对发现行号/触发条件/影响、已审/未审范围、输入/Git及回收。Codex仍只证明既有进程组清理，detached后代限制保留。

## 免费准备与下一 gate

新目录/驱动/源码/CLI/Node/输入摘要和AST已准备，dry-run通过：4文件5,020字节、180秒、无采集缺口、backend_started=false。第四批没有新消息或启动marker/logs/result。新版斜杠命令仍未加载/安装，本批通过绝对源码公共入口，不能替代UI验收。

需针对本第四批批准：向已有“Claude验收会话”单次发送交接，并执行上述一次真实审查；目标仍须满足自身人类授权与权限。第三批已失败停止，一次批准不自动续到新驱动。批准后首步复核身份及固定摘要、唯一选路单次发送，再只读匹配回执/结果；异常停止不重试。不包含安装、升级、提交、推送、发布或合并。

## 本机Node修复后的预览失效说明

用户随后明确要求解决本机Node12问题。NVM默认本来已是24.18.0，但Claude会话快照中Node12排首，登录Bash未初始化NVM。已单独修复本机Bash默认初始化及Claude SessionStart环境持久化，并备份原配置；免费继承旧Node12 PATH的Bash/zsh及Codex版本检查通过，[证据](2026-10-12-node-environment-repair.json)。此本机配置修复不进入delegate产品依赖，也不授权新增模型调用。

当前实际Codex已独立观察到0.162.1，不由本次Node修复安装或升级；本第四批预览仍固定0.160.1，禁止执行旧驱动。Claude恢复/重开后固定宿主身份也可能变化。后续须基于实际CLI/宿主重新准备预览，不更新旧批准，不启动当前第四批。当前用户请求仅完成Node环境修复。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
