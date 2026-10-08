# Implementation Plan: detection（后端可用性探测与降级）

历史归档：本文保留早期实现时的方案与勾选状态，部分命令、认证判据、性能或测试约定已过时。当前合同见 [模块规格](../../SPEC-detection.md)，使用入口见 [README](../../README.md)。本文不作为当前任务清单。

Spec：[`../../SPEC-detection.md`](../../SPEC-detection.md) · 能力图：[`../../capability-map.md`](../../capability-map.md)
任务清单：[`todo.md`](todo.md)

## Overview

回答一个问题：**现在派得出去吗。** 三级探测 + 缓存 + 失败静默降级，
外加一个按需跑的接入体检。不调用 Codex，也不决定什么活该派。

## Architecture Decisions

1. **探测与注入分离。** `detect.sh` 只算「可用/不可用 + 原因」，两个 hook 事件共用它。
   要不要把这个事实注入给模型、注入成什么话，是 `routing` 的事。
   这样 `routing` 还没做的时候，detection 也能独立验收。

2. **性质 1 优先于一切功能。** 第一个任务就是「没装 Codex 时静默退 0、零输出」，
   而不是「探测能跑通」。装了插件不能给别的项目添乱 —— 这条不成立的话后面都不用做。

3. **AGENTS.md 扫描只在 `doctor` 里，绝不进每轮路径。** 它既费时间又越权。
   每轮路径上只有一次「读缓存文件」（< 1ms）。

4. **缓存坏了等于没缓存。** 文件缺失/非法 JSON/过期，一律重探，不报错。
   缓存是省时间的，不是真相源。

5. **测试仍然打桩。** 与 channel 共用 `stub-codex`；`auth.json` 路径用
   `CODEX_AUTH_FILE` 覆盖，绝不碰用户真实的 `~/.codex/`。

## Task List

### Phase 1: 性质先行
- [x] D1 hook 骨架与「零足迹」：没装 Codex 时静默退 0、零输出
- [x] D2 三级探测阶梯 + 每一级的原因

**Checkpoint E**：没装 Codex 的机器上 hook 零输出退 0；三级阶梯每一级可单独复现地测到，尤其「`command -v` 为真但 `--version` 失败」。

### Phase 2: 缓存与健壮性
- [x] D3 缓存：写、读、过期、损坏
- [x] D4 输出契约：要么为空、要么合法 JSON；内部出错也不破坏这条

**Checkpoint F**：缓存命中时不再调用 codex（调用日志为证）；喂进损坏缓存、构造内部失败点，hook 仍退 0 且输出可被 `json.load` 解析。

### Phase 3: 接入体检
- [x] D5 `doctor.sh` + `/delegate:doctor`：安装/登录/AGENTS.md 流程编排规则

**Checkpoint G**：19 条断言全绿；`doctor` 对含「等确认」的 AGENTS.md 报风险、对干净的不报。

## Risks and Mitigations

| 风险 | 影响 | 缓解 |
|---|---|---|
| hook 输出非 JSON → 宿主拒绝，**且失败静默** | **High** | 断言 11 把 stdout 喂给 `json.load`；D4 专门做这条契约 |
| 探测本身出错却报成「链路有问题」（假警报） | **High** | 性质 2；断言 12 构造内部失败点，验仍退 0 且无噪音 |
| 测试污染用户真实 `~/.codex/` | Med | 一律用 `CODEX_AUTH_FILE` 与临时 HOME，断言里明确断言没碰真实路径 |
| 测试污染真实 `${TMPDIR}/delegate/` | Med | 两个套件都把 TMPDIR 指向自己的临时目录；实测积到 1310 个文件 / 9.3MB 才发现 |
| 每轮路径变慢 | Med | 缓存命中只读一个文件；AGENTS.md 扫描隔离在 doctor |
| doctor 在**已经修好**的 AGENTS.md 上报假警报 | **High** | 认「已声明非交互豁免」；断言 13b；真实文件上实测过 |
| `auth.json` 存在但 token 已过期 | Low | 已知缺口，写在 spec 的 Open Questions 里，不假装能测 |

## Open Questions

见 [`../../SPEC-detection.md`](../../SPEC-detection.md) 的 Open Questions：缓存 TTL 定 8 小时是拍的；
要不要转述 `codex doctor`；`auth.json` 存在 ≠ token 有效。
