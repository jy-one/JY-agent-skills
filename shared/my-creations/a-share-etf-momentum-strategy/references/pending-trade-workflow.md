# 待确认交易机制（确认执行流程）

## 概述

每日14:30扫描脚本输出的买卖建议不再直接操作，而是：

1. **保存到 `pending_trade.json`** — 包含完整的买卖参数（价格、数量、预估盈亏）
2. **等待用户确认** — 用户在群里回复"确认执行"确认操作
3. **执行交易** — 读取pending_trade.json，更新positions.json

## pending_trade.json 结构

```json
{
  "generated_at": "2026-05-07 14:50:26",
  "sh_change": 0.45,
  "buy": {
    "code": "515880",
    "name": "通信ETF国泰",
    "theme": "通信",
    "price": 1.412,
    "buy_price": 1.4134,
    "change": 4.44,
    "qty": 6900,
    "est_cost": 9757.42
  },
  "sell": {
    "code": "159796",
    "name": "电池ETF汇添富",
    "buy_price": 1.1702,
    "sell_price": 1.1558,
    "qty": 8500,
    "cost": 9951.44,
    "sell_net": 9819.67,
    "pnl": -131.77,
    "pnl_pct": -1.32
  },
  "status": "executed"
}
```

### 字段说明

| 字段 | 说明 |
|:---|:---|
| `generated_at` | 扫描生成时间戳 |
| `sh_change` | 上证指数当日涨幅 |
| `buy` | 买入建议（可能为null） |
| `sell` | 卖出建议（可能为null） |
| `status` | `pending`=待确认, `executed`=已执行 |

### buy 字段
| 字段 | 说明 |
|:---|:---|
| `price` | 扫描时的实时价格（未加滑点） |
| `buy_price` | 含滑点的实际买入价（price × 1.001） |
| `qty` | 买入股数（100股整数倍） |
| `est_cost` | 预估买入总成本（含佣金） |

### sell 字段
| 字段 | 说明 |
|:---|:---|
| `sell_price` | 含滑点的卖出价（cur_price × 0.999） |
| `sell_net` | 卖出后的净到手收入（扣佣金） |
| `pnl` | 盈利金额（¥） |
| `pnl_pct` | 盈利百分比 |

## 状态迁移

```
pending → executed（用户确认后执行）
pending → cancelled（用户取消或重新扫描覆盖）
```

## 执行规则

当用户回复"确认执行"时，按以下顺序操作：

### 1. 先卖出
- 读取 pending['sell']
- 计算卖出手续费（万五，最低5元）
- 从 positions.json 中移除该持仓
- 释放资金到可用现金

### 2. 再买入（关键：资金计算陷阱！）

- 使用释放后的资金计算可买股数
- **剩余现金 = 初始资金 - 已持仓成本（含手续费）**
- **可用资金 = 剩余现金 + 卖出净得**
- ⚠️ **不要写成 `INITIAL_CAPITAL + 卖出净得`** —— 初始资金已经花掉了，再加一遍就是双倍计算！
- 计算买入手续费（万五，最低5元）
- 写入新持仓到 positions.json
- 设置初始 high = 买入价

### 3. 更新状态
- pending_trade.json status → "executed"
- 标记 updated_at 时间

## 费用计算标准

与回测一致：

```python
# 卖出
sell_px = cur_price * 0.999       # 滑点0.1%
sell_val = qty * sell_px
sell_comm = max(sell_val * 0.0005, 5)
sell_net = sell_val - sell_comm

# 买入
buy_px = price * 1.001             # 滑点0.1%
buy_qty = int(available / buy_px / 100) * 100
buy_val = buy_qty * buy_px
buy_comm = max(buy_val * 0.0005, 5)
buy_cost = buy_val + buy_comm
```

## 与定时任务的关系

- 定时任务（cron job）只运行扫描脚本，**不执行交易**
- 扫描脚本输出推荐并保存pending，打印"回复 '确认执行' 以执行以上操作"
- 用户在群里看到报告后，手动回复确认
- 由当前对话中的LLM读取pending_trade.json并执行

## 常见问题

**Q: 如果用户没回复确认怎么办？**
A: 下次扫描时pending_trade.json会被新的覆盖，旧的pending状态丢失。但positions.json不受影响，之前的持仓保持不变。

**Q: 可以只确认买入不卖出吗？**
A: 当前设计是"先卖出再买入"的原子操作。如果需要独立操作，可以手动指定。

**Q: 确认执行后价格变了怎么办？**
A: 以pending_trade.json中记录的实时价格（含滑点）为准，确认时不再重新拉行情。
