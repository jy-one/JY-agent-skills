#!/usr/bin/env python3
"""V3.4 单仓版 — 详细交易流水表"""
import json, urllib.request, ssl
from collections import defaultdict

DATA_FILE = '/home/jy01/etf-data/all_kline_mar_apr.json'
POOL_FILE = '/home/jy01/etf-data/etf_pool.json'

with open(DATA_FILE) as f: all_data = json.load(f)
with open(POOL_FILE) as f: pool = json.load(f)
pool_codes = set(e['code'] for e in pool['etfs'])

etf_info = {}
for code, info in all_data.items():
    if info['count'] == 0: continue
    dc, dp = {}, {}
    for k in info['klines']:
        dt, c, o, h, l, v = k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
        dc[dt] = c
        dp[dt] = (o, h, l, v)
    etf_info[code] = {'name': info['name'], 'dc': dc, 'dp': dp}

all_dates = sorted(set(d for info in etf_info.values() for d in info['dc']))

ctx = ssl.create_default_context()
url = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline?_var=kline_day&param=sh000001,day,,,300"
resp = urllib.request.urlopen(url, timeout=15)
text = resp.read().decode('utf-8').replace('kline_day=', '')
sh_data = json.loads(text)
sh_prev = list(sh_data['data']['sh000001']['day'])
sh_daily = {}
for i, row in enumerate(sh_prev):
    dt = row[0]
    if i == 0: sh_daily[dt] = 0
    else: sh_daily[dt] = (float(row[2]) - float(sh_prev[i-1][2])) / float(sh_prev[i-1][2]) * 100

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
def get_theme(name):
    for th, kws in THEME_KW.items():
        for kw in kws:
            if kw in name: return th
    return None

def get_daily_change(code, dt):
    if code not in etf_info or dt not in etf_info[code]['dc']: return None
    cur = etf_info[code]['dc'][dt]
    dates = sorted(etf_info[code]['dc'].keys())
    idx = dates.index(dt)
    if idx == 0: return None
    prev_c = etf_info[code]['dc'][dates[idx-1]]
    return None if prev_c <= 0 else (cur - prev_c) / prev_c * 100

# ====== 回测 ======
cash = 10000.0
positions = []
trades = []

for i, dt in enumerate(all_dates):
    # 卖出
    new_pos = []
    for pos in positions:
        code = pos['code']
        if code not in etf_info or dt not in etf_info[code]['dc']:
            new_pos.append(pos); continue
        cur = etf_info[code]['dc'][dt]
        if cur >= pos['high']:
            pos['high'] = cur; pos['no_high_days'] = 0
            new_pos.append(pos)
        else:
            decline = (pos['high'] - cur) / pos['high'] * 100
            pos['no_high_days'] += 1
            if decline >= 0.8:
                sell_px = cur * 0.999
                sell_val = pos['qty'] * sell_px
                sell_comm = max(sell_val * 0.0005, 5)
                sell_net = sell_val - sell_comm
                profit = sell_net - pos['cost']
                cash += sell_net
                pnl = (sell_px - pos['bp']) / pos['bp'] * 100

                # 判断卖出原因
                reason = f"跌{decline:.2f}%触发卖出"
                trades.append({
                    'buy_dt': pos['bd'],
                    'sell_dt': dt,
                    'theme': pos.get('theme', ''),
                    'name': pos['name'],
                    'code': pos['code'],
                    'buy_price': round(pos['bp'], 3),
                    'buy_chg': pos.get('daily_chg', 0),
                    'sell_price': round(sell_px, 3),
                    'buy_amount': round(pos['cost'], 2),
                    'sell_amount': round(sell_net, 2),
                    'pnl_pct': round(pnl, 2),
                    'reason': reason,
                    'hold_days': i - pos['bi'],
                    'month': pos['bd'][:7],
                    'profit': round(profit, 2),
                })
            else:
                new_pos.append(pos)
    positions = new_pos

    # 买入
    if len(positions) < 1:
        if not (dt in sh_daily and sh_daily[dt] <= -1.0):
            theme_scores = defaultdict(list)
            for code in etf_info:
                chg = get_daily_change(code, dt)
                if chg is None: continue
                th = get_theme(etf_info[code]['name'])
                if th: theme_scores[th].append(chg)
            theme_best = {th: max(chgs) for th, chgs in theme_scores.items()}
            top10 = set(th for th, _ in sorted(theme_best.items(), key=lambda x: -x[1])[:10])

            candidates = []
            for code in pool_codes:
                if code not in etf_info or dt not in etf_info[code]['dc']: continue
                if code in [p['code'] for p in positions]: continue
                name = etf_info[code]['name']
                th = get_theme(name)
                if th and th in [p.get('theme','') for p in positions]: continue
                if th and th in top10:
                    chg = get_daily_change(code, dt)
                    if chg is not None: candidates.append((chg, code, name, th))

            if candidates:
                candidates.sort(key=lambda x: -x[0])
                picked = 0
                for idx in range(len(candidates)):
                    if picked >= 1: break
                    chg, bc, bn, th = candidates[idx]
                    if chg > 5.0: continue
                    if th and th in [p.get('theme','') for p in positions]: continue
                    bp = etf_info[bc]['dc'][dt] * 1.001
                    qty = int((cash - 5) / bp / 100) * 100
                    bv = qty * bp
                    buy_comm = max(bv * 0.0005, 5)
                    cost = bv + buy_comm
                    if qty > 0 and cost <= cash:
                        cash -= cost
                        positions.append({
                            'code': bc, 'name': bn, 'theme': th,
                            'bd': dt, 'bi': i, 'bp': bp, 'qty': qty,
                            'cost': cost, 'high': etf_info[bc]['dc'][dt],
                            'no_high_days': 0, 'daily_chg': round(chg, 2),
                        })
                        picked += 1

# 清仓
last_dt = all_dates[-1]
for pos in positions:
    if pos['code'] in etf_info and last_dt in etf_info[pos['code']]['dc']:
        cur = etf_info[pos['code']]['dc'][last_dt]
        sell_px = cur * 0.999
        sell_val = pos['qty'] * sell_px
        sell_comm = max(sell_val * 0.0005, 5)
        sell_net = sell_val - sell_comm
        profit = sell_net - pos['cost']
        cash += sell_net
        pnl = (sell_px - pos['bp']) / pos['bp'] * 100
        trades.append({
            'buy_dt': pos['bd'],
            'sell_dt': last_dt,
            'theme': pos.get('theme', ''),
            'name': pos['name'],
            'code': pos['code'],
            'buy_price': round(pos['bp'], 3),
            'buy_chg': pos.get('daily_chg', 0),
            'sell_price': round(sell_px, 3),
            'buy_amount': round(pos['cost'], 2),
            'sell_amount': round(sell_net, 2),
            'pnl_pct': round(pnl, 2),
            'reason': '期末强制清仓',
            'hold_days': all_dates.index(last_dt) - pos['bi'],
            'month': pos['bd'][:7],
            'profit': round(profit, 2),
        })

# ====== 输出 ======
all_trades = sorted(trades, key=lambda x: x['buy_dt'])
total_profit = cash - 10000
total_ret = total_profit / 10000 * 100

# 表头
print("=" * 145)
print("  V3.4 单仓版 — 3~4月完整交易明细")
print(f"  初始资金: ¥10,000 | 手续费: 万五(最低5元) | 滑点: 0.1% | 单日涨幅+5%上限+大盘过滤+0.8%卖出")
print("=" * 145)

# 列定义
cols = ['买入日', '卖出日', '主题', 'ETF名称', '买入价', '买入当日涨幅',
        '卖出价', '买入金额', '卖出金额', '持有收益率', '卖出原因']
wids = [10, 10, 8, 22, 9, 10, 9, 10, 10, 8, 18]
hdr = '  '.join(f'{c:>{w}}' if i > 0 else f'{c:<{w}}' for i, (c, w) in enumerate(zip(cols, wids)))
sep = '  '.join('─' * w for w in wids)
print(f"  {sep}")
print(f"  {hdr}")
print(f"  {sep}")

wins = []
losses = []
for i, t in enumerate(all_trades, 1):
    em = '🟢' if t['profit'] > 0 else '🔴'
    gains = f"{t['buy_chg']:+.2f}%"
    vals = [
        t['buy_dt'],
        t['sell_dt'],
        t.get('theme', '?'),
        t['name'],
        f"{t['buy_price']:.3f}",
        gains,
        f"{t['sell_price']:.3f}",
        f"¥{t['buy_amount']:>7.0f}",
        f"¥{t['sell_amount']:>7.0f}",
        f"{t['pnl_pct']:+.2f}%",
        t['reason'],
    ]
    row = '  '.join(f'{v:>{w}}' if j > 0 else f'{v:<{w}}' for j, (v, w) in enumerate(zip(vals, wids)))
    print(f"  {em} {row}")
    if t['profit'] > 0: wins.append(t)
    else: losses.append(t)

avg_win = sum(t['profit'] for t in wins)/len(wins) if wins else 0
avg_loss = sum(t['profit'] for t in losses)/len(losses) if losses else 0

print(f"  {sep}")
print(f"\n📊 汇总")
print(f"  总交易: {len(all_trades)}笔 | 胜率: {len(wins)/len(all_trades)*100:.0f}% ({len(wins)}胜/{len(losses)}负)")
print(f"  总盈利: ¥{total_profit:+,.2f} | 总收益率: {total_ret:+.2f}%")
print(f"  平均盈利: +¥{avg_win:.0f} | 平均亏损: -¥{-avg_loss:.0f}")

# 按月汇总
mar = [t for t in all_trades if t.get('month','').startswith('2026-03')]
apr = [t for t in all_trades if t.get('month','').startswith('2026-04')]
mar_p = sum(t['profit'] for t in mar)
apr_p = sum(t['profit'] for t in apr)
print(f"  3月: ¥{mar_p:+,.0f} ({mar_p/10000*100:+.2f}%) | {len(mar)}笔")
print(f"  4月: ¥{apr_p:+,.0f} ({apr_p/10000*100:+.2f}%) | {len(apr)}笔")
print(f"  {'='*60}")

print(f"\n💡 卖出原因分析")
reasons = defaultdict(lambda: {'cnt': 0, 'profit': 0.0})
for t in all_trades:
    r = t['reason']
    reasons[r]['cnt'] += 1
    reasons[r]['profit'] += t['profit']
for r, d in sorted(reasons.items(), key=lambda x: -x[1]['profit']):
    print(f"  {r:30s}: {d['cnt']:2d}笔 | 合计¥{d['profit']:+,.0f}")
