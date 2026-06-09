# JY-agent-skills

跨 Agent Skill 管理仓库，统一管理 Hermes、Claude Code、Codex 的 skills。

## 目录结构

```
JY-agent-skills/
├── shared/          # 通用 skills（所有 Agent 都能用）
├── hermes/          # Hermes 专用 skills
├── claude-code/     # Claude Code 专用 skills
├── codex/           # Codex 专用 skills
└── scripts/         # 同步脚本
```

## 使用方法

### 同步到 Agent

```bash
# 同步到所有 Agent
./scripts/sync.sh all

# 只同步到 Hermes
./scripts/sync.sh hermes

# 只同步到 Claude Code
./scripts/sync.sh claude

# 预览同步（不实际执行）
./scripts/sync.sh all --dry-run
```

### 添加新 Skill

```bash
# 1. 创建 skill 目录
mkdir -p shared/my-new-skill

# 2. 创建 SKILL.md
cat > shared/my-new-skill/SKILL.md << 'EOF'
---
name: my-new-skill
description: 技能描述
---

# 技能名称

技能内容...
EOF

# 3. 提交到 Git
git add shared/my-new-skill
git commit -m "添加 my-new-skill"

# 4. 同步到各 Agent
./scripts/sync.sh all
```

### 备份与恢复

```bash
# 备份所有 Agent 的 skill 目录
./scripts/backup.sh all

# 列出可用备份
./scripts/restore.sh hermes

# 恢复指定备份
./scripts/restore.sh hermes /path/to/backup.tar.gz
```

## Skill 目录

| Agent | 目录 |
|-------|------|
| Hermes | `~/.hermes/skills/` |
| Claude Code | `~/.claude/skills/` |
| Codex | `~/.codex/skills/` |
