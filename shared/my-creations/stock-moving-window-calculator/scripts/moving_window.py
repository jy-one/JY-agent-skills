#!/usr/bin/env python3
"""
A股移动窗口涨幅计算器
用法: python moving_window.py <stock_code> [--window 30] [--threshold 200]
"""

import argparse
import requests
import json
import sys
from datetime import datetime


def get_kline_data(stock_code, days=60):
    """获取A股K线数据"""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={stock_code},day,,,{days},qfq"
    try:
        response = requests.get(url, timeout=10)
        data = json.loads(response.text)
        
        if data.get('code') != 0:
            print(f"API错误: {data.get('msg', '未知错误')}")
            return []
        
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
    except Exception as e:
        print(f"获取数据失败: {e}")
        return []


def calc_moving_window_return(records, window=30):
    """计算移动窗口涨幅"""
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


def predict_trigger_threshold(records, window=30, threshold=200, limit_up=10):
    """预测明天触发阈值所需涨幅"""
    if len(records) < window + 1:
        return {'error': f'数据不足，需要至少{window + 1}天，当前{len(records)}天'}
    
    today = records[-1]
    today_price = today['close']
    
    # 明天的窗口基准日
    tomorrow_base_idx = len(records) - window
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


def analyze_stock(stock_code, window=30, threshold=200, limit_up=10):
    """完整分析流程"""
    print(f"\n{'='*80}")
    print(f"股票移动窗口分析: {stock_code.upper()}")
    print(f"{'='*80}\n")
    
    # 获取数据
    print(f"正在获取K线数据...")
    records = get_kline_data(stock_code, days=90)
    
    if not records:
        print("❌ 获取数据失败")
        return None
    
    print(f"✅ 获取到 {len(records)} 天数据")
    print(f"   数据范围: {records[0]['date']} 至 {records[-1]['date']}")
    
    # 计算窗口涨幅
    records = calc_moving_window_return(records, window)
    
    # 显示当前状态
    today = records[-1]
    print(f"\n{'─'*80}")
    print(f"当前状态（{today['date']}）")
    print(f"{'─'*80}")
    print(f"今日收盘价: {today['close']:.2f}元")
    
    if today.get(f'return_{window}d') is not None:
        print(f"{window}日涨幅: {today[f'return_{window}d']:.2f}%")
        print(f"基准日: {today[f'base_date_{window}d']}")
        print(f"基准价: {today[f'base_price_{window}d']:.2f}元")
    else:
        print(f"⚠️ 数据不足{window}天，无法计算{window}日涨幅")
    
    # 预测触发阈值
    print(f"\n{'─'*80}")
    print(f"触发阈值预测")
    print(f"{'─'*80}")
    
    result = predict_trigger_threshold(records, window, threshold, limit_up)
    
    if 'error' in result:
        print(f"❌ {result['error']}")
        return records
    
    print(f"明日窗口基准日: {result['tomorrow_base_date']}")
    print(f"明日基准价: {result['tomorrow_base_price']:.2f}元")
    print(f"触发{threshold}%涨幅目标价: {result['target_price']:.2f}元")
    print(f"明日需要涨幅: {result['required_return']:.2f}%")
    print(f"明日涨停价: {result['limit_up_price']:.2f}元")
    print(f"明日跌停价: {result['limit_down_price']:.2f}元")
    
    print(f"\n{'─'*80}")
    if result['can_trigger']:
        print(f"✅ 明天可以触发{window}日{threshold}%异动")
        print(f"   只需涨{result['required_return']:.2f}%即可")
    else:
        print(f"❌ 明天无法触发{window}日{threshold}%异动")
        print(f"   需要涨{result['required_return']:.2f}%，超过{limit_up}%涨跌停限制")
        print(f"   距离目标还差: {result['gap']:.2f}元")
    print(f"{'─'*80}")
    
    # 显示最近5天窗口涨幅
    print(f"\n最近5天{window}日窗口涨幅:")
    print(f"{'日期':<12} {'收盘价':<10} {f'{window}日涨幅':<12} {'基准日':<12} {'基准价':<10}")
    print(f"{'─'*60}")
    
    for r in records[-5:]:
        if r.get(f'return_{window}d') is not None:
            print(f"{r['date']:<12} {r['close']:<10.2f} {r[f'return_{window}d']:<12.2f} {r[f'base_date_{window}d']:<12} {r[f'base_price_{window}d']:<10.2f}")
        else:
            print(f"{r['date']:<12} {r['close']:<10.2f} {'N/A':<12} {'N/A':<12} {'N/A':<10}")
    
    return records


def main():
    parser = argparse.ArgumentParser(description='A股移动窗口涨幅计算器')
    parser.add_argument('stock_code', help='股票代码，如 sh600396 或 sz000001')
    parser.add_argument('--window', type=int, default=30, help='窗口天数（默认30）')
    parser.add_argument('--threshold', type=float, default=200, help='目标涨幅百分比（默认200）')
    parser.add_argument('--limit-up', type=float, default=10, help='涨跌停限制百分比（默认10）')
    
    args = parser.parse_args()
    
    # 执行分析
    records = analyze_stock(
        args.stock_code,
        window=args.window,
        threshold=args.threshold,
        limit_up=args.limit_up
    )
    
    if records:
        print(f"\n分析完成。")


if __name__ == '__main__':
    main()
