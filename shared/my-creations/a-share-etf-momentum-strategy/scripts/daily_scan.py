#!/usr/bin/env python3
"""
ETF动量策略每日扫描脚本
交易日14:30执行
数据源：腾讯行情API
V2.0 - 加入待确认交易机制（用户确认后才执行）
"""
import json, os, sys
import urllib.request, ssl, time
from datetime import datetime

POOL_FILE = '/home/jy01/etf-data/etf_pool.json'
POSITIONS_FILE = '/home/jy01/etf-data/positions.json'
PENDING_TRADE_FILE = '/home/jy01/etf-data/pending_trade.json'
INITIAL_CAPITAL = 10000  # 起始资金
COMMISSION_RATE = 0.0005  # 万五
MIN_COMMISSION = 5  # 最低5元
SLIPPAGE = 0.001  # 滑点0.1%
ctx = ssl.create_default_context()

with open(POOL_FILE) as f:
    pool = json.load(f)
pool_codes = {e['code']: e for e in pool['etfs']}
pool_list = [(e['code'], e['name'], e['theme']) for e in pool['etfs']]

now = datetime.now()
print(f"📡 扫描时间: {now.strftime('%Y-%m-%d %H:%M')}")
print(f"📦 跟踪板块: {len(pool['themes'])}个主题")
print()

# ====== 查询各板块ETF实时涨幅 ======
stime = time.time()

pool_data = {}
for code, name, theme in pool_list:
    prefix = 'sh' if code.startswith('5') else 'sz'
    url = f'https://qt.gtimg.cn/q={prefix}{code}'
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        text = resp.read().decode('gbk')
        parts = text.split('~')
        if len(parts) > 40:
            price = float(parts[3]) if parts[3] else 0
            prev_close = float(parts[4]) if parts[4] else 0
            change = float(parts[32]) if parts[32] else 0
            high = float(parts[33]) if parts[33] else 0
            low = float(parts[34]) if parts[34] else 0
            volume = float(parts[6]) if parts[6] else 0
            amount = float(parts[37]) if parts[37] else 0
            pool_data[code] = {
                'code': code, 'name': name, 'theme': theme,
                'price': price, 'change': change, 'high': high,
                'low': low, 'volume': volume, 'amount': amount,
                'prev_close': prev_close,
            }
    except:
        pass
    time.sleep(0.05)

elapsed = time.time() - stime

if not pool_data:
    print("❌ 所有数据源均不可用")
    sys.exit(1)

# ====== 排序 ======
sorted_pool = sorted(pool_data.values(), key=lambda x: -x['change'])

print(f"\n📊 板块实时涨幅排行（数据源: 腾讯行情，耗时{elapsed:.1f}s）")
print("=" * 65)
print(f"  {'#':>2s} {'板块':10s} {'领涨ETF':22s} {'涨幅':>7s} {'现价':>7s} {'成交额':>10s}")
print(f"  {'─'*2} {'─'*10} {'─'*22} {'─'*7} {'─'*7} {'─'*10}")

for i, e in enumerate(sorted_pool, 1):
    vol = f"{e['amount']/1e8:.2f}亿" if e['amount'] >= 1e8 else f"{e['amount']/1e4:.0f}万"
    print(f"  {i:2d} {e['theme']:10s} {e['name']:22s} {e['change']:+6.2f}% {e['price']:7.3f} {vol:>10s}")

# ====== 买入推荐（涨幅最高的1只ETF，全仓）======
print()
print("=" * 65)
print("🎯 买入推荐（单仓）")
print("=" * 65)

# 大盘过滤
sh_change = 0
try:
    sh_resp = urllib.request.urlopen('https://qt.gtimg.cn/q=sh000001', timeout=10)
    sh_text = sh_resp.read().decode('gbk')
    sh_parts = sh_text.split('~')
    if len(sh_parts) > 32:
        sh_change = float(sh_parts[32]) if sh_parts[32] else 0
except:
    pass

buy_rec = None
sell_rec = None

if sh_change <= -1.0:
    print(f"  ⚠️ 上证指数跌幅{sh_change:.1f}% ≥1%，今日不开新仓")
else:
    for e in sorted_pool:
        if e['change'] > 5.0:
            continue
        buy_rec = e
        break

    if buy_rec:
        vol = f"{buy_rec['amount']/1e8:.2f}亿" if buy_rec['amount'] >= 1e8 else f"{buy_rec['amount']/1e4:.0f}万"
        print(f"  ✅ 全仓买入 {buy_rec['code']} {buy_rec['name']:20s} | 涨幅{buy_rec['change']:+6.2f}% | 成交{vol:>10s} | {buy_rec['theme']}")
    else:
        print(f"  ⚠️ 今日无适合买入的标的（所有候选涨幅>5%）")

# ====== 持仓检查 ======
print()
print("=" * 65)
print("💼 持仓检查")
print("=" * 65)

if os.path.exists(POSITIONS_FILE):
    with open(POSITIONS_FILE) as f:
        pos_data = json.load(f)
    positions = pos_data.get('holdings', [])
else:
    positions = []

if not positions:
    print("  📭 当前无持仓")
else:
    for pos in positions:
        code = pos['code']
        if code in pool_data:
            cur = pool_data[code]['price']
            high = pos.get('high', pos['buy_price'])

            if cur >= high:
                pos['high'] = cur
                pos['no_high_days'] = 0
                status = '✅ 持有（创新高）'
            else:
                pos['no_high_days'] = pos.get('no_high_days', 0) + 1
                decline = (high - cur) / high * 100
                if decline < 0.8:
                    status = f'⏳ 持有（跌{decline:.1f}%<0.8%，缓冲中）'
                else:
                    status = '❌ 建议卖出'
                    sell_rec = {
                        'code': pos['code'],
                        'name': pos['name'],
                        'buy_price': pos['buy_price'],
                        'cur_price': cur,
                        'high': high,
                        'decline': decline,
                        'qty': pos['qty'],
                        'cost': pos['cost'],
                    }

            chg = (cur - pos['buy_price']) / pos['buy_price'] * 100
            print(f"  {status} | {code} {pos['name']:20s} | 买入{pos['buy_price']:.3f} | 当前{cur:.3f} | 收益{chg:+6.2f}%")

# ====== 保存待确认交易 ======
pending = {
    'generated_at': str(datetime.now()),
    'sh_change': sh_change,
    'buy': None,
    'sell': None,
    'status': 'pending'
}

if buy_rec:
    available = INITIAL_CAPITAL
    if sell_rec:
        available = INITIAL_CAPITAL + sell_rec['qty'] * sell_rec['cur_price'] * (1 - COMMISSION_RATE - SLIPPAGE)
    buy_price = buy_rec['price'] * (1 + SLIPPAGE)
    buy_qty = int(available / buy_price / 100) * 100
    buy_cost = buy_qty * buy_price * (1 + COMMISSION_RATE)
    if buy_cost - buy_qty * buy_price * COMMISSION_RATE < MIN_COMMISSION:
        buy_cost = buy_qty * buy_price + MIN_COMMISSION

    pending['buy'] = {
        'code': buy_rec['code'],
        'name': buy_rec['name'],
        'theme': buy_rec['theme'],
        'price': buy_rec['price'],
        'buy_price': round(buy_price, 4),
        'change': buy_rec['change'],
        'qty': buy_qty,
        'est_cost': round(buy_cost, 2),
    }

if sell_rec:
    sell_price = sell_rec['cur_price'] * (1 - SLIPPAGE)
    sell_income = sell_rec['qty'] * sell_price
    sell_fee = sell_income * COMMISSION_RATE
    if sell_fee < MIN_COMMISSION:
        sell_fee = MIN_COMMISSION
    sell_net = sell_income - sell_fee
    pnl = sell_net - sell_rec['cost']
    pnl_pct = (sell_net - sell_rec['cost']) / sell_rec['cost'] * 100

    pending['sell'] = {
        'code': sell_rec['code'],
        'name': sell_rec['name'],
        'buy_price': sell_rec['buy_price'],
        'sell_price': round(sell_price, 4),
        'qty': sell_rec['qty'],
        'cost': sell_rec['cost'],
        'sell_net': round(sell_net, 2),
        'pnl': round(pnl, 2),
        'pnl_pct': round(pnl_pct, 2),
    }

with open(PENDING_TRADE_FILE, 'w') as f:
    json.dump(pending, f, ensure_ascii=False, indent=2)

if os.path.exists(POSITIONS_FILE):
    with open(POSITIONS_FILE, 'w') as f:
        json.dump({'holdings': positions, 'updated_at': str(datetime.now())}, f, ensure_ascii=False, indent=2)

# ====== 待确认操作提示 ======
print()
print("=" * 65)
print("📋 待确认操作")
print("=" * 65)
has_pending = False
if pending['sell']:
    has_pending = True
    s = pending['sell']
    print(f"  🔴 卖出 {s['code']} {s['name']:20s} | {s['qty']}股 | 预估盈亏{s['pnl_pct']:+6.2f}%（¥{s['pnl']:+.0f}）")
if pending['buy']:
    has_pending = True
    b = pending['buy']
    print(f"  🟢 买入 {b['code']} {b['name']:20s} | {b['qty']}股 @ {b['buy_price']:.4f} | 预估成本¥{b['est_cost']:.0f}")
if has_pending:
    print("  ➡️ 回复 '确认执行' 以执行以上操作")
else:
    print("  📭 今日无待执行操作")

print()
print("=" * 65)
print(f"✅ 扫描完成（数据源: 腾讯行情）")
print("=" * 65)
