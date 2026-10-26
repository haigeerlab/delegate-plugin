# S36 付费实测：真实 `--write` 不再改用户配置

2026-10-26，write-trust 模块 Checkpoint 3（WT-07）。用户授权原话：「两处 Spec 修订复审批准；Checkpoint 3 付费实测批准，按你写的步骤跑一次。」

## 做法

- 本机 codex-cli 0.162.1，ChatGPT 登录，模型与推理档取用户配置默认（日志：`gpt-6.1-sol`）。
- 测前确认真实 `~/.codex/config.toml` 里没有 `delegate-s36-live` 字样，记 sha256。
- 在家目录新建从未用过 Codex 的仓库 `~/delegate-s36-live-20261026231004`，做一次初始提交。
- 在该仓库里用本分支源码运行：

```bash
/bin/bash <worktree>/plugins/delegate/scripts/delegate-exec.sh run --write -- "在仓库根目录新建 hello.txt，内容为 ok"
```

## 结果

| 检查 | 结果 |
|---|---|
| 退出码 | 0，结果行 `status=done` |
| 过程日志头 | `approval: never`、`sandbox: workspace-write [workdir, /tmp, $TMPDIR]` |
| 文件写出 | `hello.txt` 内容 `ok`；git 验收块 `?? hello.txt` |
| stderr | 只有 `delegate: host=unknown backend=codex model=unknown`，没有「未能确认」提示 |
| 真实 `~/.codex/config.toml` sha256 | 测前测后都是 `c84d6a4bc314065332efdec280985595c0654b3adcfe7e64cd2ea7136f3b3c8b` |

runId `20261026231004.41079`。过程日志在本机 `${TMPDIR}/delegate/` 下，未进入仓库。

## 结论

真实登录下的写模式运行照常完成写入，Codex 没有往用户配置追加信任记录（WT-07 成立）。修复前同样的首次运行会追加 `[projects."<仓库路径>"] trust_level = "trusted"`（S35 实测与本模块 Checkpoint 2 的对照组）。

临时仓库 `~/delegate-s36-live-20261026231004` 保留，是否删除由用户决定。

## 未覆盖

- 只跑了普通仓库根目录一种情形；worktree 与子目录由桩测试和免费真机核验覆盖。
- 可续跑与续跑的真实运行没有付费重测（参数由桩测试覆盖）。
