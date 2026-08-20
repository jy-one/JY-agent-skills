# JY-agent-skills

跨 Agent Skill 管理仓库，统一管理 Hermes、Claude Code、Codex 的 skills。
**Git 仓库是唯一事实源（source of truth）**——所有 skill 的最终版本都在这里。

- 远端：`git@github.com:jy-one/JY-agent-skills.git`（GitHub，SSH）
- 数据更新：2026-08-20

---

## 目录结构（实际状态）

```
JY-agent-skills/
├── shared/                     # 通用 skills（所有 Agent 可用，两级分类结构）
│   ├── investing-research/     # A股投资分析框架（9个，自建）
│   ├── my-creations/           # 自建策略工具（2个）
│   ├── other/                  # 通用流程类（7个，obra/superpowers）
│   └── software-development/   # 软件开发类（8个，obra/superpowers）
├── claude-code/                # Claude Code / Codex 专用 skills（5个）
├── scripts/                    # 同步 / 备份 / 恢复 / 更新脚本
├── config.yaml                 # Agent 目录与同步配置
├── README.md                   # 本文档
└── SOURCES.md                  # 每个 skill 的来源记录
```

> 注意：`hermes/` 和 `codex/` 目录存在但**为空**（历史遗留），实际 skill 全部放在 `shared/` 下。

---

## Skill 清单（共 31 个）

### shared/investing-research/（9个，全部自建）

- **stock-analysis-base** — 投资分析共享基座：分析技巧、常见陷阱、飞书格式规范、Chat ID 管理。其他分析 skill 依赖此 skill
- **stock-analyzer** — 个股深度分析：公司定位、管理层、财务验证（PEG）、股东博弈、产业链验证、Bull/Bear Case
- **industry-analyzer** — 行业分析：产业链拆解、竞争格局（CR3/CR5）、技术路线、国产替代、周期判断、政策环境
- **industry-stock-analysis** — 行业与上市公司综合分析框架（旧版，已被 industry-analyzer + stock-analyzer 拆分管替）
- **peer-comparator** — 可比公司对比：多维对比、PE 溢价率、业务结构差异
- **news-pulse** — 股价异动快速归因（10分钟搞清"发生了什么"）
- **investment-checklist** — 巴菲特价值投资买入前 Checklist（六关快速筛选）
- **bottleneck-hunter** — 供应链瓶颈猎手：从超级趋势扫描产业链物理瓶颈
- **a-share-direct-data-api** — 东财/腾讯底层 API 直连（a-share-data/tushare 不可用时的兜底数据路径）

### shared/my-creations/（2个，自建策略工具）

- **a-share-etf-momentum-strategy** — A股 ETF 惯性战法：动量效应短线交易策略（含回测脚本）
- **stock-moving-window-calculator** — 股票 N 日滑动窗口收益率计算与阈值预测

### shared/other/（7个，obra/superpowers 6个 + vercel-labs 1个）

- brainstorming、dispatching-parallel-agents、finishing-a-development-branch、
  receiving-code-review、requesting-code-review、verification-before-completion（obra）
- find-skills（vercel-labs）

### shared/software-development/（8个，全部 obra/superpowers）

- executing-plans、subagent-driven-development、systematic-debugging、
  test-driven-development、using-git-worktrees、using-superpowers、
  writing-plans、writing-skills

### claude-code/（5个，自建）

- **claude-session-manager** — Claude Code 会话管理（JSONL 解析、导出、归档、总结）
- **codex-session-manager** — Codex 会话管理
- **codex-cli** — 从其他 Agent 环境调用 Codex CLI 执行任务
- **interactive-input** — 聊天中嵌入交互式 UI 组件（选择题、表单等）
- **mining-session-skills** — 从已完成会话中提炼可复用 skill

---

## 同步机制（重要）

### Hermes：symlink 直连仓库（当前实际方式）

Hermes 的 `~/.hermes/skills/` 下，仓库管理的 skill 是 **符号链接**，直接指向本仓库：

```
~/.hermes/skills/software-development/writing-plans -> ~/JY-agent-skills/shared/software-development/writing-plans/
```

**好处：改仓库源文件 = 改 Hermes 生效文件，无需任何同步步骤。**

### Claude Code / Codex：脚本同步

```bash
# 同步到所有 Agent
./scripts/sync.sh all

# 只同步到 Hermes / Claude / Codex
./scripts/sync.sh hermes
./scripts/sync.sh claude
./scripts/sync.sh codex

# 预览（不实际执行）
./scripts/sync.sh all --dry-run

# 同步前先备份
./scripts/sync.sh all --backup
```

---

## 日常使用流程

### 添加新 Skill

```bash
# 1. 创建分类目录下的 skill 目录（两级结构）
mkdir -p shared/<category>/my-new-skill

# 2. 创建 SKILL.md（frontmatter 必须有 name + description）
cat > shared/<category>/my-new-skill/SKILL.md << 'EOF'
---
name: my-new-skill
description: 技能描述（触发条件、适用场景）
---

# 技能名称
技能内容...
EOF

# 3. 提交到 Git
git add shared/<category>/my-new-skill
git commit -m "添加 my-new-skill"
git push

# 4a. Hermes：建 symlink（或用 ./scripts/sync.sh hermes）
ln -s ~/JY-agent-skills/shared/<category>/my-new-skill ~/.hermes/skills/<category>/my-new-skill

# 4b. 其他 Agent：跑同步脚本
./scripts/sync.sh all
```

### 修改已有 Skill

直接编辑 `shared/<category>/<skill>/` 下的源文件，然后 commit + push。
Hermes 通过 symlink 即时生效；其他 Agent 跑 `./scripts/sync.sh all`。

### 备份与恢复

```bash
# 备份所有 Agent 的 skill 目录
./scripts/backup.sh all

# 列出可用备份
./scripts/restore.sh hermes

# 恢复指定备份
./scripts/restore.sh hermes /path/to/backup.tar.gz
```

备份默认存放在 `~/skill-backups/`，保留最近 5 份。

---

## 已知注意事项

1. **Hermes 侧存在历史断链 symlink**：顶层（非分类目录下）指向 `shared/<skill>/` 的单层 symlink 已失效（仓库已改为两级分类结构），例如 `~/.hermes/skills/brainstorming`、`~/.hermes/skills/writing-plans` 等。实际生效的是 `~/.hermes/skills/<category>/<skill>` 下的链接。清理时确认无遗漏即可删除顶层断链。
2. **a-share-direct-data-api 与 my-creations 在 Hermes 侧是真实目录**（非 symlink），更新后需手动同步到仓库（`cp` 后 commit），或改为 symlink 统一管理。
3. 仓库 `shared/` 下的 skill 中，`a-share-direct-data-api`、`bottleneck-hunter`、`investment-checklist`、`my-creations/*` 为 2026-07 ~ 2026-08 新增，SOURCES.md 已同步更新。

---

## Agent Skill 目录

| Agent | 目录 | 同步方式 |
|-------|------|---------|
| Hermes | `~/.hermes/skills/` | symlink 直连仓库 |
| Claude Code | `~/.claude/skills/` | `./scripts/sync.sh claude` |
| Codex | `~/.codex/skills/` | `./scripts/sync.sh codex` |
