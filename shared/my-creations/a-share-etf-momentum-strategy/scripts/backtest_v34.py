#!/usr/bin/env python3
"""
V3.4 正式版回测
单日涨幅 + 5%上限 + 大盘过滤(<-1%) + 0.8%卖出缓冲
起始资金1万，手续费万五+滑点0.1%，输出每笔交易对总资金贡献

用法: python3 backtest_v34.py
"""
import json, urllib.request, ssl, time
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

# 上证指数
ctx = ssl.create_default_context()
url = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline?_var=kline_day&param=sh000001,day,,,300"
resp = urllib.request.urlopen(url, timeout=15)
text = resp.read().decode('utf-8').replace('kline_day=', '')
sh_data = json.loads(text)
sh_daily = {}
sh_rows = list(sh_data['data']['sh000001']['day'])
for i, row in enumerate(sh_rows):
    dt = row[0]
    if i == 0: sh_daily[dt] = 0
    else: sh_daily[dt] = (float(row[2]) - float(sh_rows[i-1][2])) / float(sh_rows[i-1][2]) * 100

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
    for theme, kws in THEME_KW.items():
        for kw in kws:
            if kw in name: return theme
    return None

def get_daily_change(code, dt):
    """单日涨幅 = (今收-昨收)/昨收 (不是日内涨幅!)"""
    if code not in etf_info or dt not in etf_info[code]['dc']: return None
    cur = etf_info[code]['dc'][dt]
    dates = sorted(etf_info[code]['dc'].keys())
    idx = dates.index(dt)
    if idx == 0: return None
    prev_c = etf_info[code]['dc'][dates[idx-1]]
    if prev_c <= 0: return None
    return (cur - prev_c) / prev_c * 100

# ====== 策略参数（可调）======
CAPITAL = 10000.0          # 初始资金
SELL_BUFFER = 0.8          # 跌幅<此值继续持有(%)
MAX_DAILY_CHG = 5.0        # 单日涨幅>此值跳过(%)
SH_DROP_LIMIT = -1.0       # 上证指数当日跌幅<此值不开仓(%)

cash = CAPITAL
positions = []
trades = []
total_asset_log = []

for i, dt in enumerate(all_dates):
    # ---- 卖出 ----
    new_pos = []
    sell_log = []
    for pos in positions:
        code = pos['code']
        if code not in etf_info or dt not in etf_info[code]['dc']:
            new_pos.append(pos)
            continue
        cur = etf_info[code]['dc'][dt]
        if cur >= pos['high']:
            pos['high'] = cur; pos['no_high_days'] = 0
            new_pos.append(pos)
        else:
            decline = (pos['high'] - cur) / pos['high'] * 100
            pos['no_high_days'] += 1
            if decline >= SELL_BUFFER:
                sell_px = cur * 0.999                        # 滑点0.1%
                val = pos['qty'] * sell_px
                sell_comm = max(val * 0.0005, 5)             # 佣金万五
                profit = val - sell_comm - pos['cost']       # 净盈利
                cash += val - sell_comm
                pnl_pct = (sell_px - pos['bp']) / pos['bp'] * 100
                trades.append({
                    'buy_dt': pos['bd'], 'sell_dt': dt,
                    'code': code, 'name': pos['name'], 'theme': pos.get('theme',''),
                    'pnl_pct': round(pnl_pct, 2),
                    'contrib_pct': round(profit / CAPITAL * 100, 2),
                    'hold_days': i - pos['bi'], 'month': pos['bd'][:7],
                    'decline': round(decline, 2),
                    'buy_price': round(pos['bp'],3), 'sell_price': round(sell_px,3),
                    'qty': pos['qty'], 'buy_cost': round(pos['cost'],2),
                    'sell_net': round(val - sell_comm,2), 'profit': round(profit,2),
                })
                sell_log.append(f"卖{pos['name']}({pnl_pct:+.1f}%/{profit:+}")
            else:
                new_pos.append(pos)
    positions = new_pos

    # ---- 买入 ----
    buy_log = []
    if len(positions) < 2:
        if not (dt in sh_daily and sh_daily[dt] <= SH_DROP_LIMIT):
            # 板块评分：每组内取单日涨幅最高的ETF为代表
            theme_scores = defaultdict(list)
            for code in etf_info:
                chg = get_daily_change(code, dt)
                if chg is None: continue
                th = get_theme(etf_info[code]['name'])
                if th: theme_scores[th].append(chg)
            theme_best = {th: max(chgs) for th, chgs in theme_scores.items()}
            top10 = set(th for th, _ in sorted(theme_best.items(), key=lambda x: -x[1])[:10])
            # 候选ETF筛选
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
                slots = 2 - len(positions)
                picked = 0
                for idx in range(len(candidates)):
                    if picked >= slots: break
                    chg, bc, bn, th = candidates[idx]
                    if MAX_DAILY_CHG > 0 and chg > MAX_DAILY_CHG: continue   # 5%上限
                    if th and th in [p.get('theme','') for p in positions]: continue
                    bp = etf_info[bc]['dc'][dt] * 1.001                      # 买入滑点0.1%
                    alloc = cash / slots
                    qty = int((alloc - 5) / bp / 100) * 100
                    bv = qty * bp
                    buy_comm = max(bv * 0.0005, 5)
                    cost = bv + buy_comm
                    if qty > 0 and cost <= cash:
                        cash -= cost
                        positions.append({
                            'code': bc, 'name': bn, 'theme': th,
                            'bd': dt, 'bi': i, 'bp': bp, 'qty': qty, 'cost': cost,
                            'high': etf_info[bc]['dc'][dt], 'no_high_days': 0,
                        })
                        picked += 1
                        buy_log.append(f"买{bn}({chg:+.1f}%)")
        else:
            buy_log.append(f"大盘{sh_daily[dt]:+.1f}%不开仓")

    # 每日快照
    pos_value = sum(
        etf_info[p['code']]['dc'].get(dt, p['bp']) * p['qty']
        for p in positions if p['code'] in etf_info and dt in etf_info[p['code']]['dc']
    )
    total_asset_log.append((dt, cash, pos_value, cash + pos_value, sell_log, buy_log))

# 清仓
last_dt = all_dates[-1]
for pos in positions:
    if pos['code'] in etf_info and last_dt in etf_info[pos['code']]['dc']:
        cur = etf_info[pos['code']]['dc'][last_dt]
        sell_px = cur * 0.999
        val = pos['qty'] * sell_px
        comm = max(val * 0.0005, 5)
        profit = val - comm - pos['cost']
        cash += val - comm
        pnl_pct = (sell_px - pos['bp']) / pos['bp'] * 100
        trades.append({
            'sell_dt': last_dt, 'buy_dt': pos['bd'],
            'code': pos['code'], 'name': pos['name'], 'theme': pos.get('theme',''),
            'pnl_pct': round(pnl_pct, 2),
            'contrib_pct': round(profit / CAPITAL * 100, 2),
            'hold_days': all_dates.index(last_dt) - pos['bi'],
            'month': pos['bd'][:7], 'profit': round(profit, 2),
        })

# ====== 输出 ======
final_profit = cash - CAPITAL
final_ret = final_profit / CAPITAL * 100

mar_trades = [t for t in trades if t.get('month','').startswith('2026-03')]
apr_trades = [t for t in trades if t.get('month','').startswith('2026-04')]
mar_profit = sum(t['profit'] for t in mar_trades)
apr_profit = sum(t['profit'] for t in apr_trades)

print("=" * 75)
print("  V3.4 正式版回测 — 资金流水")
print(f"  初始: ¥{CAPITAL:,.0f}  手续费: 万5(最低5)  滑点: 0.1%")
print("=" * 75)

all_t = sorted(trades, key=lambda x: x['buy_dt'])
for i, t in enumerate(all_t, 1):
    emoji = '🟢' if t['profit'] > 0 else '🔴'
    cost_s = f"¥{t.get('buy_cost',0):.0f}" if 'buy_cost' in t else "—"
    print(f"  {emoji} {i:2d} {t['buy_dt']}→{t['sell_dt']} [{t.get('theme','?'):8s}] "
          f"{t['name']:22s} {cost_s:>7s} {t['pnl_pct']:+5.1f}% "
          f"{t.get('profit',0):+7.0f}元 {t.get('contrib_pct',0):+6.2f}% {t.get('hold_days',0):3d}天")

print(f"\n📊 总账")
print(f"  3月: ¥{mar_profit:+,.0f} ({mar_profit/CAPITAL*100:+.2f}%) | {len(mar_trades)}笔")
print(f"  4月: ¥{apr_profit:+,.0f} ({apr_profit/CAPITAL*100:+.2f}%) | {len(apr_trades)}笔")
print(f"  合计: ¥{final_profit:+,.0f} ({final_ret:+.2f}%) | {len(trades)}笔")

print(f"\n{'─'*75}")
print(f"  每日资金曲线")
print(f"{'─'*75}")
print(f"  {'日期':10s} {'现金':>8s} {'持仓':>8s} {'总资产':>10s} {'累计收益':>10s} {'操作':30s}")
for dt, c, pv, t, sells, buys in total_asset_log:
    dr = (t - CAPITAL) / CAPITAL * 100
    ops = ' | '.join(sells[:1] + buys[:1])[:30] if sells or buys else '—'
    print(f"  {dt} {c:>8.2f} {pv:>8.2f} {t:>10.2f} {dr:+9.2f}% {ops:30s}")

print(f"\n  最终: ¥{cash:,.2f}  |  盈利: ¥{final_profit:+,.0f}  |  收益率: {final_ret:+.2f}%")
