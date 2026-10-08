# 接入前原始记录 / Pre-adoption records

来源提交 / Source commit：`56c3ba76f1059f929bc908c0e45469abc623859a`。八份文件按字节保存，勾选、正文与原有相对路径不变。

`.md.txt` 是原始文本，不作为可执行计划或当前链接。历史相对路径应结合原路径或 `git show <commit>:<originalPath>` 阅读。当前开发流程见 [开发约定](../../development-workflow.md)。

Eight files are preserved byte for byte. The `.md.txt` copies are source evidence, not active plans or current navigation. Interpret their relative paths using the original location or the Git snapshot. See [Development workflow](../../en/development-workflow.md) for current conventions.

| 原路径 / Original path | 原文 / Raw copy | SHA-256 |
|---|---|---|
| `tasks/plan.md` | [原文 / Source](tasks/plan.md.txt) | `46bb3c72b57ecc36e6bb1e39bcf32edde8d65cbbce7b2ef2d636ef027235169c` |
| `tasks/todo.md` | [原文 / Source](tasks/todo.md.txt) | `8377e4f510153d3be63135fae148fc29c2f2ed4e76781953b9f3b1fd4cdbc4d7` |
| `tasks/channel/plan.md` | [原文 / Source](tasks/channel/plan.md.txt) | `567b776a7d55a7615396df70c7eae8ff5dbd6ae2934a2382fe20105a8d383b96` |
| `tasks/channel/todo.md` | [原文 / Source](tasks/channel/todo.md.txt) | `7872b6be2631a17b72283984159221f91a1c4bbf1511a2ce1142ef558dbb19c8` |
| `tasks/detection/plan.md` | [原文 / Source](tasks/detection/plan.md.txt) | `fb7f8325fa193aba04a9b5469c394e4b4ca25ab4764c1be1000547ac2beeed02` |
| `tasks/detection/todo.md` | [原文 / Source](tasks/detection/todo.md.txt) | `af91033eee6569aae5f260b0c08b6588abdb38244d6eebea200e2d2a28b93fc4` |
| `tasks/routing/plan.md` | [原文 / Source](tasks/routing/plan.md.txt) | `a29da9c24ba8fdf38754a25f7299cf6e900900726c675963867a564e7882c3b0` |
| `tasks/routing/todo.md` | [原文 / Source](tasks/routing/todo.md.txt) | `c24c25f5e7e197fb4583d88a9175770b5e7f0022a757fef6589288481e187b91` |

历史任务有 119 个未勾选验收/验证项，模块计划却标为完成。归档保留这种差异；本轮验证不会替这些项补勾，也不证明过去是否获批。

The old module todos contain 119 unchecked acceptance/verification items despite completed plans. This discrepancy remains preserved; present checks do not retroactively complete or approve them.

[归档清单 / Archive manifest](manifest.json) 保存机器可读的来源与校验值。
