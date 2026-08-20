#!/usr/bin/env python3
"""拉取东财全量ETF + 按指定主题筛选，构建标的池"""
import json, urllib.request, ssl, time, os

DATA_DIR = '/home/jy01/etf-data'
os.makedirs(DATA_DIR, exist_ok=True)

ctx = ssl.create_default_context()

THEMES = {
    '商业航天': ['航天', '航空航天', '空天', '商业航天', '卫星'],
    '通信': ['通信'],
    '芯片': ['芯片'],
    '半导体': ['半导体', '集成电路'],
    '人工智能': ['人工智能', 'AI', '机器人', '机器狗', '科创AI'],
    '新能源': ['新能源'],
    '储能': ['储能'],
    '电池': ['电池', '锂电', '锂电池'],
    'A500': ['A500', '中证A500'],
    '科创': ['科创50', '科创100', '科创200', '科创综指'],
    '创业板': ['创业板ETF', '创业板50'],
}

EXCLUDE = ['货币', '债券', '国债', '可转债', '商品', '黄金', '纳指', '标普',
           '日经', '德国', '法国', '美股', '添利', '添益', '快钱', '日利']

print("拉取东财全量ETF...")
all_etfs = {}

for page in range(1, 14):
    url = f'https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=100&po=0&fields=f12,f14,f2,f3,f5,f6&fid=f12&fs=b:MK0021,b:MK0022'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    try:
        resp = urllib.request.urlopen(req, context=ctx, timeout=15)
        data = json.loads(resp.read().decode())
        for k, v in data['data']['diff'].items():
            code = v['f12']
            name = v['f14']
            all_etfs[code] = {
                'code': code, 'name': name,
                'price': (v.get('f2') or 0) / 1000,
                'change': (v.get('f3') or 0) / 100,
                'volume': v.get('f5') or 0,
                'amount': v.get('f6') or 0,
            }
        print(f"  页{page:2d}: {len(data['data']['diff']):3d}只", flush=True)
    except Exception as e:
        print(f"  页{page}: ❌ {str(e)[:50]}", flush=True)
    time.sleep(0.3)

print(f"共获取 {len(all_etfs)} 只ETF\n")

pool = {}
for code, etf in all_etfs.items():
    name = etf['name']
    if any(kw in name for kw in EXCLUDE):
        continue
    matched = False
    for theme, keywords in THEMES.items():
        for kw in keywords:
            if kw in name:
                pool.setdefault(theme, []).append((code, name, etf['amount']))
                matched = True
                break
        if matched:
            break

result = []
for theme in THEMES:
    etfs = sorted(pool.get(theme, []), key=lambda x: -x[2])
    picks = etfs[:min(2, len(etfs))]
    for code, name, amount in picks:
        result.append({
            'code': code, 'name': name, 'theme': theme,
            'amount': amount, 'price': all_etfs[code]['price'],
            'change': all_etfs[code]['change'],
            'rank': 1 if picks[0][0] == code else 2,
        })
    vol = f'{picks[0][2]/1e8:.2f}亿' if picks else '-'
    print(f"  {theme:8s}: {len(etfs):2d}只匹配 -> {len(picks):d}只 | TOP1={picks[0][1] if picks else '-'} ({vol})")

output = {
    'created_at': '2026-05-06',
    'source': '东财全量1205只ETF',
    'total_count': len(result),
    'themes': list(THEMES.keys()),
    'etfs': result,
}
path = os.path.join(DATA_DIR, 'etf_pool.json')
with open(path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n标的池: {len(result)} 只ETF，已保存: {path}")
