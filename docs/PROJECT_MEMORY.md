# PROJECT_MEMORY

## 2026-07-02 14:05:45

- 中文版 Playwright cookie 持久化必须默认关闭；只有 `LAST30DAYS_CN_PERSIST_COOKIES` 为 `1`、`true`、`yes`、`y` 或 `on` 时，才允许读写 `browser_cookies`。
- cookie 目录和文件权限应在 POSIX 环境尽量收紧到目录 `0700`、文件 `0600`；其他平台跳过 chmod。
- `scripts/lib/crawler_bridge.py` 是本地测试导入的开发副本，`skills/last30days/scripts/lib/crawler_bridge.py` 是可安装 Skill 载荷副本；安全边界改动需要同步两处。

## 2026-07-02 14:28:34

- `origin` 应指向保存仓库 `https://github.com/IIICARUSIII/last30days-skill-cn-save.git`。
- `upstream` 应指向原作者仓库 `https://github.com/Jesseovo/last30days-skill-cn.git`。
- 长期维护分支为 `security-hardening`。
- 后续同步上游更新前，Codex 应先阅读 `docs/FORK_BRANCH_SYNC_GUIDE.md`。
