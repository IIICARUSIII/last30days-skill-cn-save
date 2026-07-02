# Fork Branch Sync Guide

本文档记录当前仓库 fork 保存分支的协作约定。后续 Codex 在同步上游前，应先阅读本文件。

## 仓库与分支

- 保存仓库 `origin`：`https://github.com/IIICARUSIII/last30days-skill-cn-save.git`
- 原作者仓库 `upstream`：`https://github.com/Jesseovo/last30days-skill-cn.git`
- 维护分支：`security-hardening`

## 另一台电脑首次 clone

```powershell
git clone https://github.com/IIICARUSIII/last30days-skill-cn-save.git
cd last30days-skill-cn-save
git switch security-hardening
```

如果远端分支还没有本地分支：

```powershell
git switch -c security-hardening origin/security-hardening
```

## 添加 upstream

```powershell
git remote add upstream https://github.com/Jesseovo/last30days-skill-cn.git
git remote -v
```

如果 `upstream` 已存在但地址不对：

```powershell
git remote set-url upstream https://github.com/Jesseovo/last30days-skill-cn.git
```

## 同步原作者更新

先确认本地安全加固改动已经提交或妥善保留：

```powershell
git status --short --branch
```

同步 `upstream/main`：

```powershell
git fetch upstream
git switch security-hardening
git merge upstream/main
```

如果原作者默认分支是 `master`：

```powershell
git fetch upstream
git switch security-hardening
git merge upstream/master
```

合并完成后推送保存分支：

```powershell
git push origin security-hardening
```

## 冲突处理

- 不要用 `git reset --hard` 处理冲突。
- 先保留本地安全加固改动，再逐段合并上游更新。
- 重点复查 cookie 持久化、setup 安装边界、`SKILL.md` 安全说明和相关测试。
- 冲突解决后运行针对性验证，再提交并推送 `security-hardening`。
