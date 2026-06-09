# 跨 Agent Skill 管理方案

## 🎯 核心思路

**把所有 skill 放在一个 Git 仓库里，用脚本自动同步到各个 Agent 的目录。**

就像你有一个"技能仓库"，各个 Agent 都来这里"取货"，但取货的方式不一样（符号链接、复制、或者直接引用）。

## 📁 目录结构

```
my-agent-skills/                    # Git 仓库根目录
├── .git/                          # Git 版本控制
├── shared/                        # 共享的 skill（所有 agent 都能用）
│   ├── python-security-scan/      # 技能1
│   │   └── SKILL.md
│   ├── cover-design/              # 技能2
│   │   └── SKILL.md
│   └── ...
├── hermes/                        # Hermes 专用 skill
│   ├── etf-momentum-strategy/
│   │   └── SKILL.md
│   └── ...
├── claude-code/                   # Claude Code 专用 skill
│   ├── some-claude-specific-skill/
│   │   └── SKILL.md
│   └── ...
├── codex/                         # Codex 专用 skill
│   └── ...
├── scripts/                       # 同步脚本
│   ├── sync.sh                    # 主同步脚本
│   ├── backup.sh                  # 备份脚本
│   └── restore.sh                 # 恢复脚本
├── config.yaml                    # 配置文件
└── README.md                      # 说明文档
```

## 🚀 快速开始

### 1. 初始化仓库

```bash
# 克隆或创建仓库
cd ~/my-agent-skills
git init

# 添加所有文件
git add .
git commit -m "初始化跨 Agent Skill 管理仓库"
```

### 2. 添加新 Skill

```bash
# 创建共享 skill
mkdir -p shared/my-new-skill
cat > shared/my-new-skill/SKILL.md << 'EOF'
---
name: my-new-skill
description: 我的新技能
version: 1.0.0
---

# 我的新技能

这是技能描述...
EOF

# 提交到 Git
git add shared/my-new-skill
git commit -m "添加 my-new-skill"
```

### 3. 同步到各 Agent

```bash
# 同步到所有 Agent
./scripts/sync.sh all

# 只同步到 Hermes
./scripts/sync.sh hermes

# 预览同步（不实际执行）
./scripts/sync.sh all --dry-run

# 同步前先备份
./scripts/sync.sh all --backup
```

## 🔧 详细用法

### 同步脚本 (sync.sh)

```bash
./scripts/sync.sh [选项] [agent-name]

选项:
    --dry-run       只显示将要执行的操作，不实际执行
    --backup        同步前先备份目标目录
    --force         强制覆盖已存在的符号链接
    --verbose       显示详细信息
    -h, --help      显示帮助信息

Agent 名称:
    hermes          同步到 Hermes
    claude          同步到 Claude Code
    codex           同步到 Codex
    all             同步到所有 Agent（默认）
```

### 备份脚本 (backup.sh)

```bash
# 备份所有 Agent 的 skill 目录
./scripts/backup.sh all

# 只备份 Hermes
./scripts/backup.sh hermes
```

### 恢复脚本 (restore.sh)

```bash
# 列出可用备份
./scripts/restore.sh hermes

# 恢复指定备份
./scripts/restore.sh hermes /path/to/backup.tar.gz
```

## 📋 各 Agent 的 Skill 目录

| Agent | Skill 目录 | 说明 |
|-------|-----------|------|
| Hermes | `~/.hermes/skills/` | Hermes Agent 技能目录 |
| Claude Code | `~/.claude/skills/` | Claude Code 技能目录 |
| Codex | `~/.codex/skills/` | Codex 技能目录 |

## 🔄 工作流程

### 日常开发流程

1. **添加新 skill**
   ```bash
   # 在 shared/ 或 agent 专用目录创建 skill
   mkdir -p shared/my-skill
   # 编辑 SKILL.md
   vim shared/my-skill/SKILL.md
   ```

2. **测试 skill**
   ```bash
   # 先同步到 Hermes 测试
   ./scripts/sync.sh hermes
   # 在 Hermes 中测试 skill
   ```

3. **提交到 Git**
   ```bash
   git add shared/my-skill
   git commit -m "添加 my-skill"
   ```

4. **同步到所有 Agent**
   ```bash
   ./scripts/sync.sh all
   ```

### 团队协作流程

1. **克隆仓库**
   ```bash
   git clone <repo-url> ~/my-agent-skills
   cd ~/my-agent-skills
   ```

2. **同步到本地 Agent**
   ```bash
   ./scripts/sync.sh all
   ```

3. **贡献新 skill**
   ```bash
   # 创建分支
   git checkout -b feature/my-new-skill
   
   # 添加 skill
   mkdir -p shared/my-new-skill
   # 编辑 SKILL.md
   
   # 提交
   git add shared/my-new-skill
   git commit -m "添加 my-new-skill"
   
   # 推送
   git push origin feature/my-new-skill
   
   # 创建 Pull Request
   ```

## ⚠️ 注意事项

### 1. 符号链接 vs 复制

**符号链接（推荐）**
- ✅ 修改源文件立即生效
- ✅ 节省磁盘空间
- ❌ 源文件删除后链接失效

**复制**
- ✅ 独立副本，互不影响
- ❌ 修改需要重新同步
- ❌ 占用更多磁盘空间

### 2. 格式兼容性

不同 Agent 的 skill 格式可能略有差异：

| 字段 | Hermes | Claude Code | Codex |
|------|--------|-------------|-------|
| 文件名 | SKILL.md | SKILL.md | SKILL.md |
| 元数据 | YAML frontmatter | YAML frontmatter | YAML frontmatter |
| 描述格式 | Markdown | Markdown | Markdown |

**建议**：共享 skill 使用通用格式，避免 Agent 特定的语法。

### 3. 版本控制

```bash
# 查看 skill 变更历史
git log --oneline shared/my-skill/

# 回滚到某个版本
git checkout <commit-hash> -- shared/my-skill/

# 查看某个 skill 的修改
git diff shared/my-skill/
```

### 4. 冲突解决

如果多人同时修改同一个 skill：

```bash
# 拉取最新代码
git pull origin main

# 解决冲突
# 编辑冲突文件，保留需要的版本

# 提交解决
git add .
git commit -m "解决冲突"
```

## 🛠️ 高级用法

### 1. 自动同步（Git Hook）

```bash
# 创建 post-merge hook
cat > .git/hooks/post-merge << 'EOF'
#!/bin/bash
echo "自动同步 skill..."
./scripts/sync.sh all
EOF
chmod +x .git/hooks/post-merge
```

### 2. 定时同步（Cron）

```bash
# 每小时同步一次
0 * * * * cd ~/my-agent-skills && git pull && ./scripts/sync.sh all
```

### 3. 监控变更（inotifywait）

```bash
# 安装 inotify-tools
sudo apt install inotify-tools

# 监控 shared 目录变化
while inotifywait -e modify -e create -e delete shared/; do
    ./scripts/sync.sh all
done
```

## 📊 方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Git 仓库 + 符号链接** | 简单、版本可控、可复用 | 需要自己维护同步脚本 | ⭐⭐⭐⭐⭐ |
| **Claude Code Marketplace** | 有标准、可分享 | 只适用于 Claude Code | ⭐⭐⭐ |
| **cc-switch 扩展** | 你已经在用了 | 需要改代码，且 cc-switch 管 MCP 不管 skill | ⭐⭐ |
| **自建 Skill Registry** | 完全可控 | 开发成本高 | ⭐⭐ |

## 🎯 实际建议

### 短期方案（立即可用）

1. **使用当前仓库结构**
   - `shared/` 放共享 skill
   - `hermes/`、`claude-code/`、`codex/` 放专用 skill

2. **使用同步脚本**
   - `./scripts/sync.sh all` 同步到所有 Agent

3. **使用备份脚本**
   - `./scripts/backup.sh all` 定期备份

### 长期方案（逐步完善）

1. **添加 Git Hook**
   - 自动同步，减少手动操作

2. **添加 CI/CD**
   - 自动测试 skill 格式
   - 自动生成文档

3. **添加 Web UI**
   - 可视化管理 skill
   - 在线编辑 SKILL.md

## 📝 示例：添加一个新 Skill

### 1. 创建 skill 目录

```bash
mkdir -p shared/my-awesome-skill
```

### 2. 创建 SKILL.md

```bash
cat > shared/my-awesome-skill/SKILL.md << 'EOF'
---
name: my-awesome-skill
description: 我的超棒技能
version: 1.0.0
author: Your Name
tags: [utility, automation]
---

# 我的超棒技能

## 功能描述

这是一个超棒的技能，可以帮你完成很多事情。

## 使用方法

1. 步骤一
2. 步骤二
3. 步骤三

## 示例

```bash
# 示例命令
echo "Hello, World!"
```

## 注意事项

- 注意事项1
- 注意事项2
EOF
```

### 3. 测试 skill

```bash
# 同步到 Hermes
./scripts/sync.sh hermes

# 在 Hermes 中测试
hermes skills list | grep my-awesome-skill
```

### 4. 提交到 Git

```bash
git add shared/my-awesome-skill
git commit -m "添加 my-awesome-skill"
git push origin main
```

### 5. 同步到所有 Agent

```bash
./scripts/sync.sh all
```

## 🎉 总结

**Git 仓库 + 脚本同步** 是最简单、最可靠的跨 Agent skill 管理方案：

1. ✅ **版本可控** - Git 管理所有变更
2. ✅ **可复用** - 一次编写，多处使用
3. ✅ **可协作** - 团队共享 skill
4. ✅ **可回滚** - 随时恢复到任意版本
5. ✅ **可扩展** - 支持任意数量的 Agent

**核心就一句话：把 skill 当代码管理，用脚本自动同步。**

行，咱就这么办。需要我帮你初始化仓库，或者添加具体的 skill，随时说。
