#!/usr/bin/env python3
"""参数化回测引擎：22只池子 × 板块TOP10交叉 × 可调卖出缓冲 × 板块分散"""
import json
from collections import defaultdict

DATA_FILE = '/home/jy01/etf-data/all_kline_mar_apr.json'
POOL_FILE = '/home/jy01/etf-data/etf_pool.json'

with open(DATA_FILE) as f:
    all_data = json.load(f)
with open(POOL_FILE) as f:
    pool = json.load(f)

pool_codes = set(e['code'] for e in pool['etfs'])

# 构建全市场ETF信息
etf_info = {}
for code, info in all_data.items():
    if info['count'] == 0:
        continue
    dc = {}
    dp = {}
    for k in info['klines']:
        dt, c, o, h, l, v = k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
        dc[dt] = c
        dp[dt] = (o, h, l, v)
    etf_info[code] = {'name': info['name'], 'dc': dc, 'dp': dp}

trading_dates = sorted(set(d for info in etf_info.values() for d in info['dc']))

THEME_KW = {
    '芯片': ['芯片'], '半导体': ['半导体', '集成电路'], '人工智能': ['人工智能', 'AI', '机器人', '科创AI'],
    '商业航天': ['卫星', '航天', '航空航天'], '新能源': ['新能源'], '储能': ['储能'],
    '电池': ['电池', '锂电'], '通信': ['通信'],
    'A500': ['A500'], '科创': ['科创50', '科创100', '科创200', '科创综指'],
    '创业板': ['创业板ETF', '创业板50'],
    '信创': ['信创'], '软件': ['软件'], '军工': ['军工', '国防'],
    '证券': ['证券', '券商'], '光伏': ['光伏'], '红利': ['红利ETF', '红利低波'],
    '消费': ['消费', '食品', '酒'], '医疗': ['医疗', '医药', '创新药'],
    '银行': ['银行'], '化工': ['化工'], '有色': ['有色', '稀土', '黄金'],
    '地产': ['房地产', '地产'], '传媒': ['传媒', '游戏'],
    '煤炭': ['煤炭'], '电力': ['电力'], '汽车': ['汽车'], '养殖': ['养殖', '农业'],
}

def get_intraday(code, dt):
    if code not in etf_info or dt not in etf_info[code]['dp']:
        return None
    o = etf_info[code]['dp'][dt][0]
    c = etf_info[code]['dc'][dt]
    return (c - o) / o * 100 if o > 0 else None

def get_theme(name):
    for theme, kws in THEME_KW.items():
        for kw in kws:
            if kw in name:
                return theme
    return None

def backtest(sell_buffer=0.0, diff_sector=True):
    """运行回测
    sell_buffer: 卖出缓冲阈值(%)。0=原始版(不新高即卖), 0.8=当前策略
    diff_sector: 是否限制两只持仓不同板块
    """
    capital = 10000
    positions = []
    trades = []

    for i, dt in enumerate(trading_dates):
        # 卖出
        new_positions = []
        for pos in positions:
            code = pos['code']
            if code not in etf_info or dt not in etf_info[code]['dc']:
                new_positions.append(pos)
                continue
            cur = etf_info[code]['dc'][dt]
            if cur >= pos['high']:
                pos['high'] = cur
                new_positions.append(pos)
            else:
                decline = (pos['high'] - cur) / pos['high'] * 100
                if decline < sell_buffer:
                    new_positions.append(pos)
                else:
                    sell_px = cur * 0.999
                    val = pos['qty'] * sell_px
                    comm = max(val * 0.0005, 5)
                    capital += val - comm
                    pnl = (sell_px - pos['bp']) / pos['bp'] * 100
                    trades.append({'buy_dt': pos['bd'], 'sell_dt': dt, 'code': code,
                        'name': pos['name'], 'theme': pos.get('theme', ''),
                        'pnl_pct': round(pnl, 2), 'hold_days': i - pos['bi'], 'month': pos['bd'][:7]})
        positions = new_positions

        # 买入
        if len(positions) < 2:
            theme_scores = defaultdict(list)
            for code in etf_info:
                chg = get_intraday(code, dt)
                if chg is None: continue
                th = get_theme(etf_info[code]['name'])
                if th:
                    theme_scores[th].append(chg)
            top10 = set()
            for th, sc in sorted({th: max(c) for th, c in theme_scores.items()}.items(), key=lambda x: -x[1])[:10]:
                top10.add(th)

            candidates = []
            for code in pool_codes:
                if code not in etf_info or dt not in etf_info[code]['dc']: continue
                if code in [p['code'] for p in positions]: continue
                name = etf_info[code]['name']
                th = get_theme(name)
                if diff_sector and th and th in [p.get('theme','') for p in positions]: continue
                if th and th in top10:
                    chg = get_intraday(code, dt)
                    if chg is not None:
                        candidates.append((chg, code, name, th))

            if candidates:
                candidates.sort(key=lambda x: -x[0])
                slots = 2 - len(positions)
                for idx in range(min(slots, len(candidates))):
                    chg, bc, bn, th = candidates[idx]
                    bp = etf_info[bc]['dc'][dt] * 1.001
                    alloc = capital / slots
                    qty = int((alloc - 5) / bp / 100) * 100
                    if qty > 0:
                        bv = qty * bp
                        comm = max(bv * 0.0005, 5)
                        cost = bv + comm
                        if cost <= capital:
                            capital -= cost
                            positions.append({'code': bc, 'name': bn, 'theme': th,
                                'bd': dt, 'bi': i, 'bp': bp, 'qty': qty, 'high': etf_info[bc]['dc'][dt]})

    # 清仓
    for pos in positions:
        if pos['code'] in etf_info and trading_dates[-1] in etf_info[pos['code']]['dc']:
            cur = etf_info[pos['code']]['dc'][trading_dates[-1]]
            sell_px = cur * 0.999
            val = pos['qty'] * sell_px
            capital += val - max(val * 0.0005, 5)
            pnl = (sell_px - pos['bp']) / pos['bp'] * 100
            trades.append({'sell_dt': trading_dates[-1], 'code': pos['code'], 'name': pos['name'],
                'theme': pos.get('theme',''), 'pnl_pct': round(pnl, 2), 'month': pos['bd'][:7]})

    ret = (capital - 10000) / 10000 * 100
    return ret, trades

if __name__ == '__main__':
    import sys
    buffer = float(sys.argv[1]) if len(sys.argv) > 1 else 0.8
    diff = sys.argv[2].lower() != 'false' if len(sys.argv) > 2 else True
    ret, trades = backtest(buffer, diff)
    wins = [t for t in trades if t['pnl_pct'] > 0]
    print(f"缓冲={buffer}% 板块分散={diff}")
    print(f"全期: {ret:+.2f}% | {len(trades)}笔 | 胜率{len(wins)/len(trades)*100:.0f}%")
    apr = [t for t in trades if t['buy_dt'].startswith('2026-04')]
    print(f"4月:  {sum(t['pnl_pct'] for t in apr):+.2f}% | {len(apr)}笔")
