# v0.3.0 release notes design

历史归档（2026-08-30）：保留当时的文档设计、计划及原始语言，未完成勾选不代表当前状态。本文中的执行步骤和约束仅属于该历史任务；当前使用与文档导航见 [README](../../../README.md) 和 [文档索引](../../README.md)。

## Goal

Create a Chinese, repository-owned source document for the future GitHub Release
of `delegate` v0.3.0.

## Scope

Add `docs/releases/v0.3.0.md`. It will state the product positioning, suitable
work, safety boundaries, installation commands, first-use guidance, and known
limitations. It will link to the existing README and DESIGN document.

## Boundaries

This work creates a reviewable release-body source only. It does not create a
GitHub Release, create or push a tag, push commits, or publish to a directory
or community platform. The document makes no comparative claims about other
projects.

## Verification

Check required sections and local links, then run `/bin/bash scripts/validate.sh`.
