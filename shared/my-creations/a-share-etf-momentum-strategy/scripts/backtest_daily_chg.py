#!/usr/bin/env python3
"""
策略 V3.4 回测脚本 — 单日涨幅 + 5%上限 + 大盘过滤器
"""
import json, urllib.request, ssl, time
from collections import defaultdict

DATA_FILE = '/home/jy01/etf-data/all_kline_mar_apr.json'
POOL_FILE = '/home/jy01/etf-data/etf_pool.json'

with open(DATA_FILE) as f:
    all_data = json.load(f)
with open(POOL_FILE) as f:
    pool = json.load(f)

pool_codes = set(e['code'] for e in pool['etfs'])

# 加载ETF数据
etf_info = {}
for code, info in all_data.items():
    if info['count'] == 0:
        continue
    dc, dp = {}, {}
    for k in info['klines']:
        dt, c, o, h, l, v = k[0], float(k[1]), float(k[2]), float(k[3]), float(k[4]), float(k[5])
        dc[dt] = c
        dp[dt] = (o, h, l, v)
    etf_info[code] = {'name': info['name'], 'dc': dc, 'dp': dp}

all_dates = set()
for info in etf_info.values():
    all_dates.update(info['dc'].keys())
trading_dates = sorted(all_dates)

# 上证指数
ctx = ssl.create_default_context()
url = "https://web.ifzq.gtimg.cn/appstock/app/kline/kline?_var=kline_day&param=sh000001,day,,,300"
resp = urllib.request.urlopen(url, timeout=15)
text = resp.read().decode('utf-8').replace('kline_day=', '')
sh_data = json.loads(text)
sh_index = {}
for row in sh_data['data']['sh000001']['day']:
    dt, o, c = row[0], float(row[1]), float(row[2])
    sh_index[dt] = {'open': o, 'close': c}
sh_dates = sorted(sh_index.keys())
sh_daily = {}
for i, dt in enumerate(sh_dates):
    if i == 0:
        sh_daily[dt] = 0
    else:
        prev = sh_dates[i-1]
        sh_daily[dt] = (sh_index[dt]['close'] - sh_index[prev]['close']) / sh_index[prev]['close'] * 100

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
            if kw in name:
                return theme
    return None

def get_daily_change(code, dt):
    """单日涨幅 = (今收 - 昨收) / 昨收 * 100"""
    if code not in etf_info or dt not in etf_info[code]['dc']:
        return None
    cur = etf_info[code]['dc'][dt]
    dates = sorted(etf_info[code]['dc'].keys())
    idx = dates.index(dt)
    if idx == 0:
        return None
    prev_c = etf_info[code]['dc'][dates[idx-1]]
    if prev_c <= 0:
        return None
    return (cur - prev_c) / prev_c * 100

def run_backtest(sell_buffer=0.8, max_daily_chg=5.0, sh_drop_limit=-1.0):
    capital = 10000
    positions, trades = [], []
    
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
                pos['no_high_days'] = 0
                new_positions.append(pos)
            else:
                decline = (pos['high'] - cur) / pos['high'] * 100
                pos['no_high_days'] += 1
                if decline >= sell_buffer:
                    sell_px = cur * 0.999
                    val = pos['qty'] * sell_px
                    comm = max(val * 0.0005, 5)
                    capital += val - comm
                    pnl = (sell_px - pos['bp']) / pos['bp'] * 100
                    trades.append({
                        'buy_dt': pos['bd'], 'sell_dt': dt, 'code': code,
                        'name': pos['name'], 'theme': pos.get('theme', ''),
                        'pnl_pct': round(pnl, 2), 'hold_days': i - pos['bi'],
                        'month': pos['bd'][:7], 'decline': round(decline, 2),
                    })
                else:
                    new_positions.append(pos)
        positions = new_positions
        
        # 买入
        if len(positions) < 2:
            if dt in sh_daily and sh_daily[dt] <= sh_drop_limit:
                continue  # 大盘跌幅太大，不开新仓
            theme_scores = defaultdict(list)
            for code in etf_info:
                chg = get_daily_change(code, dt)
                if chg is None:
                    continue
                th = get_theme(etf_info[code]['name'])
                if th:
                    theme_scores[th].append(chg)
            theme_best = {th: max(chgs) for th, chgs in theme_scores.items()}
            top10 = set(th for th, _ in sorted(theme_best.items(), key=lambda x: -x[1])[:10])
            
            candidates = []
            for code in pool_codes:
                if code not in etf_info or dt not in etf_info[code]['dc']:
                    continue
                if code in [p['code'] for p in positions]:
                    continue
                name = etf_info[code]['name']
                th = get_theme(name)
                if th and th in [p.get('theme','') for p in positions]:
                    continue
                if th and th in top10:
                    chg = get_daily_change(code, dt)
                    if chg is not None:
                        candidates.append((chg, code, name, th))
            
            if candidates:
                candidates.sort(key=lambda x: -x[0])
                slots = 2 - len(positions)
                picked = 0
                for chg, bc, bn, th in candidates:
                    if picked >= slots:
                        break
                    if max_daily_chg > 0 and chg > max_daily_chg:
                        continue
                    if th and th in [p.get('theme','') for p in positions]:
                        continue
                    bp = etf_info[bc]['dc'][dt] * 1.001
                    alloc = capital / slots
                    qty = int((alloc - 5) / bp / 100) * 100
                    bv = qty * bp
                    comm = max(bv * 0.0005, 5)
                    cost = bv + comm
                    if qty > 0 and cost <= capital:
                        capital -= cost
                        positions.append({
                            'code': bc, 'name': bn, 'theme': th,
                            'bd': dt, 'bi': i, 'bp': bp, 'qty': qty,
                            'high': etf_info[bc]['dc'][dt],
                            'no_high_days': 0, 'daily_chg': round(chg, 2),
                        })
                        picked += 1
    
    last_dt = trading_dates[-1]
    for pos in positions:
        if pos['code'] in etf_info and last_dt in etf_info[pos['code']]['dc']:
            cur = etf_info[pos['code']]['dc'][last_dt]
            sell_px = cur * 0.999
            val = pos['qty'] * sell_px
            comm = max(val * 0.0005, 5)
            capital += val - comm
            pnl = (sell_px - pos['bp']) / pos['bp'] * 100
            trades.append({
                'sell_dt': last_dt, 'buy_dt': pos['bd'], 'code': pos['code'],
                'name': pos['name'], 'theme': pos.get('theme', ''),
                'pnl_pct': round(pnl, 2), 'month': pos['bd'][:7],
            })
    
    return (capital - 10000) / 10000 * 100, trades

if __name__ == '__main__':
    ret, trades = run_backtest(0.8, 5.0, -1.0)
    apr = [t for t in trades if t.get('month','').startswith('2026-04')]
    wins = [t for t in apr if t['pnl_pct'] > 0]
    print(f"全期: {ret:+.2f}% | {len(trades)}笔")
    print(f"4月: {sum(t['pnl_pct'] for t in apr):+.2f}% | {len(apr)}笔 | {len(wins)}胜/{len(apr)-len(wins)}负")
    for t in sorted(apr, key=lambda x: x['buy_dt']):
        emoji = '🟢' if t['pnl_pct'] > 0 else '🔴'
        print(f"  {emoji} {t['buy_dt']}→{t['sell_dt']} {t['name']:22s} {t['pnl_pct']:+7.2f}%")
