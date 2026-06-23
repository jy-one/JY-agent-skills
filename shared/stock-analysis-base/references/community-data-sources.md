# A股数据获取层 — 社区Skill参考

## 数据源架构

```
数据获取层
├── tushare（需Token）          ← 财务数据、资金流、宏观、公告
│   └── 220+ API接口
├── a-share-data（免费）        ← 实时行情、板块热力图、概念涨跌、技术指标
│   └── 9个Python脚本
├── 东财+腾讯API（现有）        ← ETF扫描专用
│   └── etf_scan_daily.py
└── firecrawl/search（通用）    ← 新闻搜索、网页数据补充
```

## tushare（waditu-tushare/skills@tushare）

**来源**：Tushare Pro官方，5.2K安装，370 GitHub Stars
**安装**：`npx skills add waditu-tushare/skills@tushare -g -y`（若超时，手动下载SKILL.md+references/数据接口.md+scripts/）
**Token**：https://tushare.pro/register 注册获取，`export TUSHARE_TOKEN="your_token"`

### 核心能力
- 个股行情（daily, pro_bar, stk_mins）
- 财务数据（income, balancesheet, cashflow, fina_indicator）
- 估值指标（daily_basic: PE/PB/PS/股息率）
- 资金流（moneyflow, moneyflow_hsgt, hsgt_top10, top_list）
- 板块数据（index_classify, sw_daily, ths_index, ths_member）
- 公告/新闻（anns_d, news, major_news, research_report）
- 宏观数据（cn_cpi, cn_ppi, cn_pmi, cn_gdp, shibor）
- 龙虎榜/涨停（limit_list_d, limit_step, top_inst）

### 常用接口速查
- `stock_basic` — 股票列表
- `trade_cal` — 交易日历
- `daily` / `pro_bar` — 日线行情
- `daily_basic` — 每日估值指标
- `income` — 利润表
- `fina_indicator` — 财务质量指标（ROE/毛利率/净利率）
- `moneyflow_hsgt` — 北向资金
- `sw_daily` — 申万行业涨跌
- `cn_cpi` / `cn_pmi` — 宏观

### 限制
- 部分高级接口需要积分（分钟数据、龙虎榜细节等）
- 频率限制：普通用户200次/分钟
- 免费用户可访问基础行情+财务+估值+北向

## a-share-data（shouldnotappearcalm/a-share-skill@a-share-data）

**来源**：社区开发者，30安装
**安装**：手动下载（npx skills add通常超时），从GitHub API获取目录结构后curl下载
**Token**：不需要，直接从东财/当Invest获取

### 脚本路由
| 脚本 | 用途 | 触发词 |
|------|------|--------|
| `fetch_realtime.py` | 实时行情、北向、龙虎榜、涨跌停、资金流 | 实时、现在、今天 |
| `fetch_history.py` | 历史K线、财务、分红、指数成分 | 最近、走势、K线 |
| `fetch_technical.py` | MA/MACD/KDJ/RSI/BOLL | 技术指标、MACD |
| `fetch_danginvest.py` | 热门行业/概念涨跌幅、板块热力图、成分股、快讯 | 热门、板块、概念 |
| `fetch_sector_info.py` | 个股行业信息（东财） | 行业、属于什么行业 |
| `fetch_stock_events.py` | 业绩、增减持、监管事件 | 事件、公告、增减持 |
| `fetch_ah_stocks.py` | A+H双重上市清单 | A+H |
| `Ashare.py` | 基础工具类 | - |

### 使用示例
```bash
SKILL_DIR="~/.hermes/skills/research/a-share-data"

# 实时行情
python3 $SKILL_DIR/scripts/fetch_realtime.py --quote 600519 --json

# 历史K线
python3 $SKILL_DIR/scripts/fetch_history.py --kline 600519 --start 2025-01-01 --end 2025-03-31 --freq d --json

# 技术指标
python3 $SKILL_DIR/scripts/fetch_technical.py 600519 --freq 1d --count 120 --indicators MA,MACD --json

# 热门概念/行业涨跌幅（先读references/danginvest-api-reference.md）
python3 $SKILL_DIR/scripts/fetch_danginvest.py [参数]

# 个股行业
python3 $SKILL_DIR/scripts/fetch_sector_info.py --no-concepts --json 600519
```

### 关键Pitfall
- `fetch_sector_info.py` 的个股概念字段不稳定，固定加 `--no-concepts`，只查行业
- 市场级概念板块（涨跌幅、热力图、成分股）走 `fetch_danginvest.py`，不是 sector_info
- 历史K线内置多源逻辑：腾讯优先→新浪降级→东财兜底
- 批量拉取默认并行（max_workers=8~12），整批超时30s

### 依赖
```bash
pip install akshare MyTT pandas numpy requests
```

## 东财+腾讯API（现有ETF扫描）

已稳定运行，专用于ETF惯性战法扫描（a-share-etf-momentum-strategy skill）。
- 东财 push2.eastmoney.com — ETF列表+实时排行（易封禁，间隔≥0.3s）
- 腾讯 qt.gtimg.cn — 实时行情（稳定）
- 腾讯 web.ifzq.gtimg.cn — K线（稳定）

## 工具选择指南

| 需求 | 优先用 | 原因 |
|------|--------|------|
| 财务数据（三表、ROE、毛利率） | tushare | 结构化、标准化 |
| 估值对比（PE/PB/股息率） | tushare | daily_basic一次拉齐 |
| 北向资金、龙虎榜 | tushare | 接口稳定 |
| 宏观数据（CPI/PMI/社融） | tushare | 唯一可靠源 |
| 实时行情快查 | a-share-data | 免费、无需Token |
| 概念板块涨跌幅 | a-share-data | fetch_danginvest免费 |
| 板块热力图 | a-share-data | 唯一有热力图的 |
| 技术指标 | a-share-data | 内置MA/MACD/KDJ/RSI/BOLL |
| 公告/新闻搜索 | firecrawl | 网页搜索更灵活 |
| ETF扫描 | 东财+腾讯 | 已有稳定脚本 |

## 安装Pitfall

`npx skills add` 对这两个skill经常超时。手动安装流程：

1. GitHub API获取目录：`curl -sL "https://api.github.com/repos/<owner>/<repo>/contents/<skill-dir>"`
2. 逐文件下载：`curl -sL "https://raw.githubusercontent.com/..." -o <target>`
3. `raw.githubusercontent.com` 被MCP fetch工具屏蔽（robots.txt），必须用terminal curl
4. 大文件（如tushare的85KB数据接口.md）可能需要多次重试
5. 下载完用 `skill_view(name)` 验证
