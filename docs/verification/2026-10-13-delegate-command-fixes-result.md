# delegate 命令审查问题：三批修复结果

2026-10-13，开发仓库 `/path/to/delegate-plugin`，分支 `codex/spec-guard-conventions-public`，模块 `claude-review`。用户“分批次 快速处理审查出来的问题”授权本轮实现；三个Required问题已完成免费验证，四个核心命令保留。原[五维审查报告](2026-10-13-delegate-command-multiaxis-review.md)记录发现时的源码基准，本页记录修复状态，不改写历史证据。

| 批次 | 问题 | 修复及验证 | 状态 |
|---|---|---|---|
| 1 / Task9h | CMD-001/P1：范围外特殊文件名阻断限定review | Git原始名称先按include/exclude过滤，再解码并校验传输路径；全仓dirty事实和输入稳定性检查保留。范围外已追踪/未跟踪、已排除、非法指定路径回归；两后端dry-run等价快照 | 已修复 |
| 2 / Task9i | CMD-002/P2：模型命名空间和旧入口大小写绕过 | 新delegate_model.py统一公共review/run、旧codex-exec.sh；大小写无关识别已知家族/别名及提供商命名空间，不改写slug。跨后端在版本/认证/执行探针前退出64；未知私有slug留给选定CLI，不fallback；opusplan仍拒绝 | 已修复 |
| 3 / Task9j | DOC-001/P2：双语最新状态过期 | README首屏按四入口职责说明，链接当前状态；双语未发布说明区分本机安装与正式发布、S2固定源码与本轮未同步修复 | 已修复 |

## 验证

- 第一批两个新故障用例在原实现RED：范围外/排除文件使capture失败，两个后端preview退出127；修复后上下文10项及公共CLI14项通过。非法选定路径依旧拒绝，快照实际只有src/a.py。
- 第二批第一次测试出现导入路径错误，纠正测试后10个产品断言RED；新增共用校验后后端9项通过。最终总套覆盖公共review/run及旧入口，不启动真实执行器。合法Codex默认/写模式/模型、Claude同家族/私有slug合同保持。
- `PYTHONDONTWRITEBYTECODE=1 /bin/bash scripts/validate.sh`：退出0，148项Python、53条shell、19条eval通过。全部隔离夹具/假CLI，无真实模型。
- 修改的双语README、未发布说明及spec六文件82个本地链接存在；`git diff --check`通过。Spec Guard按当前启用安装定位：产物3通过/0警告/0失败，阶段BUILDING、下一gate仍Checkpoint3。

完整免费日志及机器结果在项目私有忽略目录 `.agent/acceptance/s2-recovery/command-fixes/`，新完整供审包在 `.agent/acceptance/s2-recovery/command-fixes-checkpoint3/`，含product/contracts/evidence diff及manifest；旧checkpoint3快照保持原字节。未stage、commit、push或发布。

## 实际边界与下一步

[S2双向真实审查](2026-10-13-delegate-s2-resume-result.md)和正常安装/四入口显示已经通过，但只覆盖其固定61文件源码。新模型辅助文件使本轮产品源码增加一文件，本次修复未刷新日常缓存、未重载、未做新的真实模型调用；不能据旧S2把新源码标为live已验证。源码bug回归不需要新增模型费用。已有实际Mac14项OS边界记录仍按原版本保留，本轮没有重复其独立运行。

主动模型写入/递归尝试、认证刷新和异常自然helper的完整安全条件（Task2/6/8）仍未完成。范围路径格式、Git16MiB输出、256文件/快照字节等既有上限不放宽；极大仓库仍可能达到采集上限。未知自定义模型能否运行由原版CLI决定，不承诺所有provider slug受支持。

四项Optional（未提交版本反馈、doctor体验、隐藏Claude routing技能、历史guest代码整理）未自动实施；REL-001版本发布身份为FYI。Local事项账本未启用，CMD/DOC编号不是Issue ID，不声称事项入账或交付。三项Required待修复数为0，待调查为0，Optional保持4项。下一步是原Checkpoint3人工审阅本仓库、本分支的新diff及未验限制，尚无最终人工批准；安装、付费模型、通信和Git交付分别需要具体授权。

> 对外说明：本机身份与路径已脱敏；原始记录在私有验收目录保留，未改变原结论或追认历史验收。
