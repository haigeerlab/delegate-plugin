# Implementation Plan: channel（委托通道）

Spec：[`../SPEC-channel.md`](../SPEC-channel.md) · 能力图：[`../capability-map.md`](../capability-map.md)
任务清单：[`todo.md`](todo.md)（本项目不用外部 tracker）

## Overview

把 `codex exec` 包成一条安全的委托通道：任务送过去、结论带回来、过程输出不进调用方上下文。
本模块**不认识「什么活该派」**——那是 `routing` 的事。

## Architecture Decisions

1. **测试默认打桩，不打网络。** 17 条断言里 16 条走 `stub-codex`，只有 `--live`
   那组真调。理由：真跑一次 13–75 秒且花额度，而我们要验的是**调用形态**，
   不是模型质量。桩只模拟我们真正依赖的契约点（stdin 行为、stdout/`-o` 分流、
   退出码、收到了哪些 flag），**不模拟模型输出**。

2. **测试套先于实现。** T2 建桩和断言骨架，T3 起每个任务都用它验收。
   spec-guard 的教训：「防线本身也要被测试」写成口号时，四次里零次做到。

3. **第一条竖切是只读通道端到端可用**（T3），不是「先写完参数解析再写调用」。
   高风险的四要素调用排在最前，早失败。

4. **失败路径与成功路径同等对待**（T4 单独成任务）。四种静默失败是这个模块存在的
   全部理由；让它们「响」比让成功路径漂亮重要。

5. **`--write` 排在模型选择之后**（T6 而非 T5）。它是唯一有副作用的路径，
   放在通道其余部分都被断言覆盖之后再加。

## Task List

### Phase 1: 骨架
- [ ] T1 仓库骨架与校验器
- [ ] T2 codex 桩与断言套骨架

**Checkpoint A**：`validate.sh` 通过；空断言套能跑出「总计 0 通过 / 0 失败」；桩可被环境变量驱动。

### Phase 2: 只读通道（核心竖切）
- [ ] T3 最小可用调用：四要素 + 日志隔离 + preamble
- [ ] T4 失败路径要响

**Checkpoint B**（最重要）：只读委托端到端可用；桩吐 100KB 时调用方 stdout 不含之；四种失败各自退出非 0 且 stderr 有下一步。

### Phase 3: 通道能力补全
- [ ] T5 模型与推理档透传
- [ ] T6 `--write` 与 git 验收块

**Checkpoint C**：17 条断言全绿；`/bin/bash scripts/validate.sh` 通过。

### Phase 4: 接线与真跑
- [ ] T7 `/delegate` 命令与插件清单接线
- [ ] T8 `--live` 真跑冒烟

**Checkpoint D**：装进 user scope 后 `/delegate` 可用；`--live` 通过，日志/答复体量比 ≥ 40×。

## Risks and Mitigations

| 风险 | 影响 | 缓解 |
|---|---|---|
| 桩与真 `codex` 行为漂移，断言测的是空气 | **High** | 桩只模拟契约点不模拟模型；T8 `--live` 冒烟每次发版前必跑；spec 记了基线版本 0.150.1 |
| Codex CLI 破坏性变更（flag 改名/移除） | Med | `--live` 会红。已知先例：`experimental_instructions_file` 在 0.150.1 已消失 |
| bash 3.2 不兼容（`${VAR}`、空数组展开） | Med | 一律 `/bin/bash` 跑测试；`validate.sh` 接静态检查 |
| 测试在 zsh 下跑会得出相反结论（MULTIOS 拼接输入重定向） | Med | 断言套一律 `/bin/bash` 执行；已写进 T3 验收 |
| 过程日志目录无限增长 | Low | Open Question，Checkpoint C 之后定 |
| 写模式在非 git 目录伪造验收 | Med | T6 的反向用例专门盯它 |

## Open Questions

- 日志目录清理策略（保留最近 N 个？N 天？完全不管？）——倾向保留 50 个，未定。
- wrapper 自身是否设超时上限，还是继续靠调用方给 Bash 设 600000。
- `--effort` 合法值本地拦一层，还是透传给 codex 报错。
