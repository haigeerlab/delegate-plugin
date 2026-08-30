# delegate

一个 Claude Code 插件：把**已经决策完毕**的执行工作交给另一个额度池（当前后端是 Codex CLI），
只把结论带回来。

设计理念、工作流与边界见 [DESIGN.md](DESIGN.md)。

## 它解决什么

不是「Claude token 不够」——那是症状。真问题是上下文经济学的错配：

Claude Code 的一切都在一条主会话上下文里。每次 grep 的输出、每个读进来的文件、
每轮测试日志，全部留在里面**并被之后每一轮重读**。而：

- **最吃上下文的活**（探索、审查、实现循环）**最不需要判断**
- **最需要判断的活**（定方案、裁轻重、验收）**几乎不吃上下文**

`delegate` 把第一类搬出去，只把结论带回来。实测压缩比：

| 真实任务 | 过程输出 | 回到上下文 |
|---|---|---|
| 一次代码审查 | 165 KB | 1.9 KB（87×）|
| 在真实仓库改两个缺陷 + 写 77 行测试 | 343 KB | 1.0 KB（340×）|

## 判据

**不是「这活难不难」，而是「这活里还有没有没定的决策」。**

决策全定完、只剩执行和查证 → 可以派。还需要取舍判断 → 留在 Claude。

| 活的类型 | 分流 |
|---|---|
| 代码审查 / 找回归 / 安全审 | 派，只读 |
| 跨文件摸结构、梳理调用链 | 派，只读 |
| 复现 bug、定位根因、读栈 | 派，只读 |
| 单个 task 的实现（改文件 + 跑测试到绿） | 派，`--write` |
| 批量机械改动（重命名、迁移、格式） | 派，`--write` |
| 需求澄清 / 架构取舍 / 验收交回来的东西 / 改一行 | **不派** |

**绝不自动派**：只提议，等一个明确的肯定答复再调。这是不可违反的性质，不是配置项。

## 安装

需要 [Codex CLI](https://github.com/openai/codex)：

```bash
npm install -g @openai/codex@latest
codex --version        # 必须真的输出版本号
codex                  # 交互式登录一次
```

然后装插件：

```bash
claude plugin marketplace add <本仓库路径或 URL>
claude plugin install delegate@delegate-marketplace
```

装完跑一次体检：`/delegate:doctor`

## 用法

```bash
/delegate <任务>                                  # 只读
/delegate --write <任务>                          # 可改文件，需你明确要求
/delegate --model gpt-5.6-sol --effort high <任务>
```

`--write` 的输出会带一段 **git 验收块**（基线 HEAD、`git status --short`、`git diff --stat`）。
**必须看它，不能只信自述** —— 实测撞到过自述说改好了而 `git status` 是空的。

## 三个模块

| 模块 | 职责 | 断言 |
|---|---|---|
| `channel` | `codex exec` 的安全调用形态、沙箱、日志隔离、写模式验收块 | 19 |
| `detection` | 三级可用性探测 + 缓存 + 失败静默降级 + 接入体检 | 19 |
| `routing` | 提议式触发：hook 注入判据位置，判断交给模型，决定权在用户 | 9 |

设计与实测记录见 `SPEC-*.md` 和 `tasks/<module>/`。

## 调用形态的四个不可省元素

每一个都对应一种**静默**失败：

| 元素 | 省掉会怎样 |
|---|---|
| `env -u OPENAI_API_KEY` | 走 API key 按量计费，「另一个额度池」的前提消失 |
| `< /dev/null` | 非 TTY stdin 让 `codex exec` **永久挂起** |
| `-o` + stdout 重定向 | 过程输出全进上下文，**价值反转成倒贴** |
| 非交互 preamble | 停在「请确认后我执行」，什么也没做 |

## 已知限制

- **「该提议时会主动提议」没有自动化验证。** `claude -p` 是单轮的，没有人可答，
  提议行为无从观测。eval 的硬判据只有「绝不自动派」。
- **eval 在本机跑**，用户的全局 `CLAUDE.md` 会一起加载，验的是组合效果而非本插件的隔离效果。
- `auth.json` 存在不代表 token 没过期。真正的可用性只有发一次请求才知道。
- 过程日志目录（`$TMPDIR/delegate/`）目前不自动清理。
- 与 [`spec-guard`](https://github.com/yizhongkaimail-collab/spec-guard-plugin) 是**松耦合**：
  本插件不依赖 agent-skills；同装时委托边界自动对齐 task 边界。

## 开发

```bash
/bin/bash scripts/validate.sh                        # 结构 + 语法 + 清单 + 各判决器自检（免费）
/bin/bash plugins/delegate/tests/test-channel.sh
/bin/bash plugins/delegate/tests/test-detection.sh
/bin/bash plugins/delegate/tests/test-routing.sh
/bin/bash plugins/delegate/tests/test-channel.sh --live   # 真调 Codex

/bin/bash evals/propose-not-auto.sh                  # 花 token
/bin/bash evals/routing-fitness.sh                   # 花 token
```

所有 shell 必须兼容 macOS 自带的 **bash 3.2**：变量一律 `${VAR}`，
空数组展开 `${ARR[@]+"${ARR[@]}"}`，不写 `cmd | grep -q`。`validate.sh` 会拦。
