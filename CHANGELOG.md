# Changelog

本文件按 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的格式只做索引：每个版本一行摘要，
完整说明在 `docs/releases/`（中文）和 `docs/en/releases/`（英文）。版本号遵循[语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

待发行的变更写在 [docs/releases/unreleased.md](docs/releases/unreleased.md)（英文 [docs/en/releases/unreleased.md](docs/en/releases/unreleased.md)），发版时由 `scripts/release-prepare.sh` 生成该版本的发行说明。

## [0.12.0] - 2026-11-24

- 技术方案审查与第二审查者（接口 1.7）。见[中文说明](docs/releases/v0.12.0.md)、[English](docs/en/releases/v0.12.0.md)。

## [0.11.0] - 2026-11-24

- 快照审查的复审（接口 1.6）。见[中文说明](docs/releases/v0.11.0.md)、[English](docs/en/releases/v0.11.0.md)。

## [0.10.0] - 2026-11-22

- 审查发现的严重程度与复审对照上一轮（接口 1.5）。见[中文说明](docs/releases/v0.10.0.md)、[English](docs/en/releases/v0.10.0.md)。

## [0.9.0] - 2026-11-20

- 审查报告新增可复算的补丁指纹（接口 1.4）。见[中文说明](docs/releases/v0.9.0.md)、[English](docs/en/releases/v0.9.0.md)。

## [0.8.6] - 2026-11-18

- Claude 审查后端信任系统明确信任的证书。见[中文说明](docs/releases/v0.8.6.md)、[English](docs/en/releases/v0.8.6.md)。

## [0.8.5] - 2026-11-18

- 修复 Codex 审查全部失败，并说清两类失败原因。见[中文说明](docs/releases/v0.8.5.md)、[English](docs/en/releases/v0.8.5.md)。

## [0.8.4] - 2026-11-04

- 无提交仓库的审查报专用诊断码。见[中文说明](docs/releases/v0.8.4.md)、[English](docs/en/releases/v0.8.4.md)。

## [0.8.3] - 2026-11-04

- 补齐使用者文档缺口。见[中文说明](docs/releases/v0.8.3.md)、[English](docs/en/releases/v0.8.3.md)。

## [0.8.2] - 2026-10-28

- run 命令说明跟上接口 1.3。见[中文说明](docs/releases/v0.8.2.md)、[English](docs/en/releases/v0.8.2.md)。

## [0.8.1] - 2026-10-28

- 文档跟上接口 1.3。见[中文说明](docs/releases/v0.8.1.md)、[English](docs/en/releases/v0.8.1.md)。

## [0.8.0] - 2026-10-27

- 把一个模块整体交给 Codex 做。见[中文说明](docs/releases/v0.8.0.md)、[English](docs/en/releases/v0.8.0.md)。

## [0.7.1] - 2026-10-27

- run 中止时回收 Codex 起的命令。见[中文说明](docs/releases/v0.7.1.md)、[English](docs/en/releases/v0.7.1.md)。

## [0.7.0] - 2026-10-26

- run 超时保留进度，写模式不再改 Codex 用户配置。见[中文说明](docs/releases/v0.7.0.md)、[English](docs/en/releases/v0.7.0.md)。

## [0.6.0] - 2026-10-26

- 可续跑委托，Codex 调用固定不经审批。见[中文说明](docs/releases/v0.6.0.md)、[English](docs/en/releases/v0.6.0.md)。

## [0.5.3] - 2026-10-17

- 发布对外接口说明与审查报告合同。见[中文说明](docs/releases/v0.5.3.md)、[English](docs/en/releases/v0.5.3.md)。

## [0.5.2] - 2026-10-16

- Codex 审查附带行号，修正 README 说明。见[中文说明](docs/releases/v0.5.2.md)、[English](docs/en/releases/v0.5.2.md)。

## [0.5.1] - 2026-10-16

- 修复 Claude Desktop 中 Claude 审查后端被误拒。见[中文说明](docs/releases/v0.5.1.md)、[English](docs/en/releases/v0.5.1.md)。

## [0.5.0] - 2026-10-14

- 双后端只读审查与命令迁移。见[中文说明](docs/releases/v0.5.0.md)、[English](docs/en/releases/v0.5.0.md)。

## [0.4.0] - 2026-10-08

- 早期版本。见[中文说明](docs/releases/v0.4.0.md)、[English](docs/en/releases/v0.4.0.md)。

## [0.3.1] - 2026-08-30

- 历史版本，远端没有对应标签。见[中文说明](docs/releases/v0.3.1.md)、[English](docs/en/releases/v0.3.1.md)。

[Unreleased]: https://github.com/haigeerlab/delegate-plugin/compare/v0.12.0...HEAD
[0.12.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.11.0...v0.12.0
[0.11.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.6...v0.9.0
[0.8.6]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.5...v0.8.6
[0.8.5]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.4...v0.8.5
[0.8.4]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.3...v0.8.4
[0.8.3]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.2...v0.8.3
[0.8.2]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.1...v0.8.2
[0.8.1]: https://github.com/haigeerlab/delegate-plugin/compare/v0.8.0...v0.8.1
[0.8.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/haigeerlab/delegate-plugin/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.5.3...v0.6.0
[0.5.3]: https://github.com/haigeerlab/delegate-plugin/compare/v0.5.2...v0.5.3
[0.5.2]: https://github.com/haigeerlab/delegate-plugin/compare/v0.5.1...v0.5.2
[0.5.1]: https://github.com/haigeerlab/delegate-plugin/compare/v0.5.0...v0.5.1
[0.5.0]: https://github.com/haigeerlab/delegate-plugin/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/haigeerlab/delegate-plugin/releases/tag/v0.4.0
[0.3.1]: docs/releases/v0.3.1.md
