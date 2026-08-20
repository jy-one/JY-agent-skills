# Skills 来源记录（SOURCES.md）

记录每个 skill 的来源仓库，方便后续更新和维护。

- 数据更新：2026-08-20
- 仓库当前共 **31 个 skill**：shared/ 26 个 + claude-code/ 5 个

---

## 来源总览

### 1. 自建 Skills（16个）

| 分类 | 数量 | Skill |
|------|------|-------|
| investing-research | 9 | stock-analysis-base、stock-analyzer、industry-analyzer、industry-stock-analysis、peer-comparator、news-pulse、investment-checklist、bottleneck-hunter、a-share-direct-data-api |
| my-creations | 2 | a-share-etf-momentum-strategy、stock-moving-window-calculator |
| claude-code | 5 | claude-session-manager、codex-session-manager、codex-cli、interactive-input、mining-session-skills |

### 2. 导入仓库（15个）

| 来源仓库 | 分类 | 数量 | Skill |
|----------|------|------|-------|
| obra/superpowers | other | 6 | brainstorming、dispatching-parallel-agents、finishing-a-development-branch、receiving-code-review、requesting-code-review、verification-before-completion |
| obra/superpowers | software-development | 8 | executing-plans、subagent-driven-development、systematic-debugging、test-driven-development、using-git-worktrees、using-superpowers、writing-plans、writing-skills |
| vercel-labs/skills | other | 1 | find-skills |

---

## 自建 Skills 明细

### investing-research/（9个，A股投资分析框架）

| Skill | 功能 | 创建时间 |
|-------|------|---------|
| stock-analysis-base | 投资分析共享基座（技巧、陷阱、飞书格式、参考案例） | 2026-06-17 |
| stock-analyzer | 个股深度分析（四大师对抗、镜子测试、PEG、信息评级） | 2026-06-17 |
| industry-analyzer | 行业分析（产业链、竞争格局、技术路线、国产替代） | 2026-06-23 |
| industry-stock-analysis | 行业与上市公司综合分析框架（旧版，已拆分） | 2026-06-17 |
| peer-comparator | 可比公司对比（PE溢价率、多维对比） | 2026-06-23 |
| news-pulse | 股价异动快速归因 | 2026-06-23 |
| investment-checklist | 巴菲特买入前六关快速筛选 | 2026-07 |
| bottleneck-hunter | 供应链瓶颈猎手（超级趋势→物理瓶颈） | 2026-07 |
| a-share-direct-data-api | 东财/腾讯底层API直连兜底数据源 | 2026-07 |

### my-creations/（2个，自建策略工具）

| Skill | 功能 | 创建时间 |
|-------|------|---------|
| a-share-etf-momentum-strategy | A股ETF惯性战法（动量效应短线交易，含回测脚本） | 2026-05 |
| stock-moving-window-calculator | 股票N日滑动窗口收益率计算与阈值预测 | 2026-06 |

### claude-code/（5个，Claude Code / Codex 专用）

| Skill | 功能 | 创建时间 |
|-------|------|---------|
| claude-session-manager | Claude Code 会话管理（JSONL解析、导出、归档） | 2026-06 |
| codex-session-manager | Codex 会话管理（导出、归档、总结） | 2026-06 |
| codex-cli | 从其他 Agent 调用 Codex CLI 执行任务 | 2026-06 |
| interactive-input | 聊天中嵌入交互式 UI 组件 | 2026-06 |
| mining-session-skills | 从已完成会话中提炼可复用 skill | 2026-06 |

---

## 已移除 Skills（17个）

2026-06-24 从仓库中移除，来源为 sugarforever/01coder-agent-skills。
如需使用，直接从原仓库安装：`npx skills@latest add sugarforever/01coder-agent-skills`

- **creative/**：cover-design、cover-image、diagram-to-image、slides-video、video-planner
- **productivity/**：promote-post、publish-substack-article、publish-x-article、publish-zsxq-article
- **social-media/**：share-reading、tweet-insight
- **other/**：add-feishu、fpl-copilot、personal-chinese-writing-style、subtitle-correction、nextjs-security-scan、python-security-scan

> 注意：Hermes 侧顶层仍有指向这些 skill 的**断链 symlink**（如 `~/.hermes/skills/cover-design`），因仓库改为两级分类结构后未清理，实际不生效。

---

## 本地安装记录（历史，已清理）

以下 skill 曾通过 `npx skills add` 安装到 `~/.hermes/skills/`，**2026-08 核查时已不存在**（Hermes 升级/清理时移除），数据源能力已由自建 a-share-direct-data-api 替代：

- ~~tushare~~（waditu-tushare/skills，需 Token）
- ~~a-share-data~~（shouldnotappearcalm/a-share-skill）
- ~~arxiv~~、~~industry-research~~、~~polymarket~~（hermes 官方 research 类）

---

## 常用命令

```bash
# 更新自 SOURCES.md 记录的上游仓库的 skills（实验性）
./scripts/update.sh --dry-run

# 同步到所有 Agent
./scripts/sync.sh all

# 备份 / 恢复
./scripts/backup.sh all
./scripts/restore.sh hermes
```
