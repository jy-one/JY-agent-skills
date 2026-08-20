---
name: stock-moving-window-calculator
description: "Use when calculating stock N-day moving window returns, predicting trigger thresholds, or analyzing momentum signals for A-share stocks."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [stock, momentum, a-share, moving-window, calculator]
    related_skills: [a-share-etf-momentum-strategy]
---

# A股移动窗口涨幅计算器

## Overview

计算A股股票的N日移动窗口涨幅，支持预测触发指定涨幅阈值所需的单日涨跌幅。核心解决**滚动窗口基准日漂移**导致的计算陷阱。

## When to Use

- 计算股票30日、20日、10日等移动窗口涨幅
- 预测明天需要涨多少才能触发某个涨幅阈值（如200%异动）
- 分析动量信号强度
- 验证滚动窗口计算逻辑

## Don't Use For

- ETF实时行情获取（用ETF扫描脚本）
- 回测策略执行（用回测脚本）

## 核心概念：滚动窗口陷阱

**问题**：30日涨幅是滚动窗口，每天基准日都不同。

```
今天（06-04）基准日：04-20，价格7.39元，30日涨幅197.29%
明天（06-05）基准日：04-21，价格8.13元，目标价24.39元
```

**关键**：明天的基准日比今天**后移一天**，基准价可能更高，导致目标价水涨船高。

## 使用方法

### 1. 获取K线数据

```python
import requests
import json

def get_kline_data(stock_code, days=60):
    """
    获取A股K线数据
    stock_code: 股票代码，如 'sh600396' 或 'sz000001'
    days: 获取天数
    """
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},day,,,{days},qfq"
    response = requests.get(url)
    data = json.loads(response.text)
    
    kline_data = data['data'][stock_code]['qfqday']
    records = []
    for item in kline_data:
        date_str, open_str, close_str, high_str, low_str, vol_str = item
        records.append({
            'date': date_str,
            'open': float(open_str),
            'close': float(close_str),
            'high': float(high_str),
            'low': float(low_str),
            'volume': float(vol_str)
        })
    return records
```

### 2. 计算移动窗口涨幅

```python
def calc_moving_window_return(records, window=30):
    """
    计算移动窗口涨幅
    records: K线数据列表
    window: 窗口天数（如30表示30日涨幅）
    
    返回: 包含窗口涨幅的记录列表
    """
    for i in range(len(records)):
        if i >= window:
            base_price = records[i - window]['close']
            current_price = records[i]['close']
            records[i][f'return_{window}d'] = (current_price - base_price) / base_price * 100
            records[i][f'base_date_{window}d'] = records[i - window]['date']
            records[i][f'base_price_{window}d'] = base_price
        else:
            records[i][f'return_{window}d'] = None
            records[i][f'base_date_{window}d'] = None
            records[i][f'base_price_{window}d'] = None
    return records
```

### 3. 预测触发阈值所需涨幅

```python
def predict_trigger_threshold(records, window=30, threshold=200, limit_up=10):
    """
    预测明天需要涨多少才能触发指定涨幅阈值
    
    records: K线数据列表
    window: 窗口天数
    threshold: 目标涨幅百分比（如200表示200%涨幅）
    limit_up: 涨跌停限制百分比（A股默认10%）
    
    返回: 字典包含计算结果
    """
    today = records[-1]
    today_price = today['close']
    
    # 明天的窗口基准日
    tomorrow_base_idx = len(records) - window
    if tomorrow_base_idx < 0:
        return {'error': '数据不足'}
    
    tomorrow_base = records[tomorrow_base_idx]
    tomorrow_base_price = tomorrow_base['close']
    
    # 计算目标价
    target_price = tomorrow_base_price * (1 + threshold / 100)
    
    # 计算所需涨幅
    required_return = (target_price - today_price) / today_price * 100
    
    # 涨停价
    limit_up_price = today_price * (1 + limit_up / 100)
    limit_down_price = today_price * (1 - limit_up / 100)
    
    # 判断是否可达
    can_trigger = required_return <= limit_up
    
    return {
        'today_price': today_price,
        'tomorrow_base_date': tomorrow_base['date'],
        'tomorrow_base_price': tomorrow_base_price,
        'target_price': target_price,
        'required_return': required_return,
        'limit_up_price': limit_up_price,
        'limit_down_price': limit_down_price,
        'can_trigger': can_trigger,
        'gap': target_price - limit_up_price if not can_trigger else 0
    }
```

### 4. 完整示例

```python
# 华电辽能(600396) 30日200%异动预测
stock_code = 'sh600396'
window = 30
threshold = 200

# 获取数据
records = get_kline_data(stock_code, days=60)

# 计算窗口涨幅
records = calc_moving_window_return(records, window)

# 预测触发阈值
result = predict_trigger_threshold(records, window, threshold)

print(f"股票: {stock_code}")
print(f"今日收盘价: {result['today_price']:.2f}元")
print(f"明日窗口基准日: {result['tomorrow_base_date']}")
print(f"明日基准价: {result['tomorrow_base_price']:.2f}元")
print(f"触发{threshold}%涨幅目标价: {result['target_price']:.2f}元")
print(f"明日需要涨幅: {result['required_return']:.2f}%")
print(f"明日涨停价: {result['limit_up_price']:.2f}元")
print(f"能否触发: {'✅ 可以' if result['can_trigger'] else '❌ 不能'}")

if not result['can_trigger']:
    print(f"距离目标还差: {result['gap']:.2f}元")
```

## 输出格式

```
股票: sh600396
今日收盘价: 21.97元
明日窗口基准日: 2026-04-21
明日基准价: 8.13元
触发200%涨幅目标价: 24.39元
明日需要涨幅: 11.02%
明日涨停价: 24.17元
能否触发: ❌ 不能
距离目标还差: 0.22元
```

## Common Pitfalls

1. **忽略滚动窗口**：明天的基准日比今天后移一天，基准价可能不同。
2. **数据不足**：窗口期需要至少N+1天数据，建议获取60天以上。
3. **涨跌停限制**：A股普通股涨跌停10%，ST股5%，北交所30%。
4. **复权处理**：使用前复权(qfq)数据，避免除权除息影响。
5. **节假日跳过**：K线数据自动跳过非交易日，但窗口天数按交易日计算。

## Verification Checklist

- [ ] 确认股票代码格式正确（sh/sz前缀）
- [ ] 确认窗口天数与需求匹配
- [ ] 确认涨跌停限制设置正确
- [ ] 验证基准日计算逻辑
- [ ] 检查数据完整性

## 扩展用法

### 多窗口分析

```python
# 同时计算多个窗口
windows = [5, 10, 20, 30]
for w in windows:
    records = calc_moving_window_return(records, w)
```

### 动量信号强度

```python
def calc_momentum_score(records):
    """
    计算动量综合得分
    """
    today = records[-1]
    score = 0
    
    # 5日动量权重30%
    if today.get('return_5d'):
        score += today['return_5d'] * 0.3
    
    # 10日动量权重30%
    if today.get('return_10d'):
        score += today['return_10d'] * 0.3
    
    # 20日动量权重40%
    if today.get('return_20d'):
        score += today['return_20d'] * 0.4
    
    return score
```
