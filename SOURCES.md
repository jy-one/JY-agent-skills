# Skills 来源记录

记录每个 skill 的来源仓库，方便后续更新和维护。

数据截止：2026-06-24

---

## 已导入仓库

| 仓库 | 地址 | 导入时间 | Skills 数量 |
|------|------|---------|------------|
| sugarforever/01coder-agent-skills | https://github.com/sugarforever/01coder-agent-skills | 2026-06-09 | 22 |
| obra/superpowers | https://github.com/obra/superpowers | 2026-06-09 | 14 |
| vercel-labs/skills | https://github.com/vercel-labs/skills | 2026-06-09 | 1 |
| waditu-tushare/skills@tushare | https://github.com/waditu-tushare/skills | 2026-06-23 | 1（仅本地） |
| shouldnotappearcalm/a-share-skill@a-share-data | https://github.com/shouldnotappearcalm/a-share-skill | 2026-06-23 | 1（仅本地） |

---

## 自建 Skills（6个）

全部属于 investing-research 分类，构成完整的A股投资分析框架。

| Skill | 功能 | 创建时间 |
|-------|------|---------|
| stock-analysis-base | 投资分析共享基座（技巧、陷阱、飞书格式、参考案例） | 2026-06-17 |
| stock-analyzer | 个股深度分析（四大师对抗、镜子测试、PEG、信息评级） | 2026-06-17 |
| industry-analyzer | 行业分析（产业链、竞争格局、技术路线、国产替代） | 2026-06-23 |
| industry-stock-analysis | 行业与上市公司综合分析框架（旧版，已拆分为上述模块） | 2026-06-17 |
| peer-comparator | 可比公司对比分析（PE溢价率、多维对比） | 2026-06-23 |
| news-pulse | 股价异动快速归因（4维侦察：公司/监管/行业/情绪） | 2026-06-23 |

---

## 本地安装 Skills（不在GitHub仓库中）

通过 `npx skills add` 安装到 `~/.hermes/skills/` 的第三方skill。

| Skill | 来源仓库 | 分类 | 功能 |
|-------|---------|------|------|
| tushare | waditu-tushare/skills | research | Tushare数据接口（220+ API，需Token） |
| a-share-data | shouldnotappearcalm/a-share-skill | research | A股实时行情、板块热力图、技术指标（免费） |
| arxiv | hermes官方 | research | arXiv论文搜索 |
| industry-research | hermes官方 | research | 多角度行业信息搜集 |
| polymarket | hermes官方 | research | Polymarket预测市场查询 |
| a-share-etf-momentum-strategy | 自建 | my-creations | A股ETF惯性战法（每日14:30扫描） |
| stock-moving-window-calculator | 自建 | my-creations | 股票N日滑动窗口收益率计算 |

---

## 仓库 Skills 分类明细

### investing-research/（6个）— 自建

| Skill | 功能 | 来源 |
|-------|------|------|
| stock-analysis-base | 投资分析共享基座 | 自建 |
| stock-analyzer | 个股深度分析 | 自建 |
| industry-analyzer | 行业分析 | 自建 |
| industry-stock-analysis | 行业与个股综合分析（旧版框架） | 自建 |
| peer-comparator | 可比公司对比 | 自建 |
| news-pulse | 股价异动归因 | 自建 |

### creative/（5个）— sugarforever/01coder-agent-skills

| Skill | 功能 | 来源 |
|-------|------|------|
| cover-design | 封面设计（HTML/CSS，15种风格模板） | sugarforever |
| cover-image | 封面图片生成（16种设计风格） | sugarforever |
| diagram-to-image | Mermaid图表/Markdown表格转图片 | sugarforever |
| slides-video | 幻灯片驱动的口播视频 | sugarforever |
| video-planner | 视频策划与发布材料准备 | sugarforever |

### software-development/（8个）— obra/superpowers

| Skill | 功能 | 来源 |
|-------|------|------|
| executing-plans | 执行实现计划 | obra |
| subagent-driven-development | 子代理驱动开发 | obra |
| systematic-debugging | 系统化调试 | obra |
| test-driven-development | 测试驱动开发 | obra |
| writing-plans | 编写实现计划 | obra |
| writing-skills | 编写skills | obra |
| using-git-worktrees | Git worktrees隔离开发 | obra |
| using-superpowers | superpowers框架使用指南 | obra |

### productivity/（4个）— sugarforever/01coder-agent-skills

| Skill | 功能 | 来源 |
|-------|------|------|
| promote-post | 推广已发布文章 | sugarforever |
| publish-substack-article | 发布到Substack | sugarforever |
| publish-x-article | 发布到X（Twitter） | sugarforever |
| publish-zsxq-article | 发布到知识星球 | sugarforever |

### social-media/（2个）— sugarforever/01coder-agent-skills

| Skill | 功能 | 来源 |
|-------|------|------|
| share-reading | 分享阅读心得到社交媒体 | sugarforever |
| tweet-insight | 从推文出发深度阅读整理 | sugarforever |

### other/（13个）— 混合来源

| Skill | 功能 | 来源 |
|-------|------|------|
| brainstorming | 创意工作前头脑风暴 | obra |
| dispatching-parallel-agents | 并行任务分发 | obra |
| find-skills | 发现和安装agent skills | vercel-labs |
| finishing-a-development-branch | 完成开发分支 | obra |
| receiving-code-review | 接收代码审查 | obra |
| requesting-code-review | 请求代码审查 | obra |
| verification-before-completion | 完成前验证 | obra |
| add-feishu | 添加飞书频道 | sugarforever |
| fpl-copilot | FPL（梦幻英超）助手 | sugarforever |
| personal-chinese-writing-style | 中文写作风格 | sugarforever |
| subtitle-correction | 字幕校正 | sugarforever |
| nextjs-security-scan | Next.js安全扫描 | sugarforever |
| python-security-scan | Python安全扫描 | sugarforever |
