# Implementation Plan: routing（提议式执行器路由）

历史归档：本文保留早期实现时的方案与勾选状态，部分命令、认证判据、性能或测试约定已过时。当前合同见 [模块规格](../../SPEC-routing.md)，使用入口见 [README](../../README.md)。本文不作为当前任务清单。

Spec：[`../../SPEC-routing.md`](../../SPEC-routing.md) · 能力图：[`../../capability-map.md`](../../capability-map.md)
任务清单：[`todo.md`](todo.md)

## Overview

让 Claude 在合适的时机**主动提议**委托，等用户点头再调；并守住三条回来之后的纪律。
`channel` 提供通道，`detection` 提供「派得出去吗」，routing 只负责**在什么时候说什么话**。

## Architecture Decisions

1. **hook 不做分类。** 用正则判断「这活该不该派」的 hook 就是假警报机器，
   而假警报比不报危害大。hook 只注入事实和判据的位置，判断交给模型，决定权在用户。

2. **确定性部分与行为部分分开验收。** `test-routing.sh` 免费、进 validate；
   `evals/*.sh` 花 token、按需跑、绝不进 validate。混在一起的后果是要么不敢跑、
   要么每次跑都烧钱。

3. **eval 三种结局。** 通过 / 不通过 / **没跑起来**。少了第三种就会
   拿工具故障去指控产品 —— spec-guard 踩过，0.7.18 才补上。

4. **routing 用自己的脚本注入，不改 detection 的输出。**
   两个模块各管各的 stdout，detection 那 19 条断言不受影响。

5. **先做「不许自动派」，再做「该派时提议」。** 前者是不可违反的性质，
   后者是效果。性质不成立时效果再好也不能发。

## Task List

### Phase 1: 注入与闸门
- [x] R1 `route.sh`：读 detection 缓存，可用才注入；不可用零注入
- [x] R2 `SKILL.md`：分流表 + 三条纪律 + 「不许自动派」的明文

**Checkpoint H**：9 条确定性断言全绿；Codex 不可用时零注入；注入内容不含越闸措辞。

### Phase 2: 行为验证
- [x] R3 `evals/_preflight.sh` + `propose-not-auto`（判「不自动跑」；「提议了没有」降为观察项）
- [x] R4 `evals/routing-fitness`（差分：该派的派、不该派的不派）

**Checkpoint I**：两个 eval 的 `--scaffold-only` 与 `--selftest` 免费通过；真跑一次 `propose-not-auto` 通过。

## Risks and Mitigations

| 风险 | 影响 | 缓解 |
|---|---|---|
| **模型越过闸门自己调** | **High** | R3 是最重要的一条；判据在桩的调用日志上，不看措辞 |
| hook 注入变成每轮噪音 | Med | 注入只有一行；Codex 不可用时零注入；R1/R2 断言钉住 |
| eval 把「没跑起来」记成「不通过」 | **High** | 三种结局，`--selftest` 喂已知输入验判决器自己 |
| **判据把探测调用数成了委托** | **High** | 只数 `exec`；`--version` 是 detect.sh 每轮都会打的。首跑就是被它误判成「模型越闸」，而 transcript 里模型根本没提委托 |
| **`claude -p` 单轮，判不了「提议并等确认」** | **High** | 已降级为观察项并写进 spec；这半个卖点目前没有自动化验证 |
| eval 测的是脚手架不是产品 | Med | 对照组充当脚手架自检；`_preflight.sh` 核对装着的插件 == 仓库内容 |
| skill 根本没被加载 | Med | 参照 spec-guard：注入里放一句显式触发指令；eval 里判 skill 是否加载 |
| **关键词判决器被条件句骗过** | **High** | 改成解析固定格式首行；真跑实测被骗过一次 |
| **脚手架规模让尺寸闸门抢先触发，差分变量串了** | **High** | 放大到 30 文件 / 120 函数；两次真跑各撞一次 |
| 对照组例子选得不好，测的是例子 | Med | 写进 Open Questions，先用一个明显的取舍类任务，跑完复盘 |

## Open Questions

见 [`../../SPEC-routing.md`](../../SPEC-routing.md)：对照组用什么任务、eval 判据放 transcript 还是文件系统、skill 会不会被加载。
