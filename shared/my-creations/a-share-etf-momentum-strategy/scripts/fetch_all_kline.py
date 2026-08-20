#!/usr/bin/env python3
"""拉取全市场ETF的2026年3-4月历史K线数据（腾讯API，稳定可靠）"""
import json, urllib.request, ssl, time, os

DATA_DIR = '/home/jy01/etf-data'
KLINE_DIR = os.path.join(DATA_DIR, 'kline')
os.makedirs(KLINE_DIR, exist_ok=True)
ctx = ssl.create_default_context()

# 第一步：从东财clist获取全量ETF列表
all_etfs = {}
for page in range(1, 14):
    url = f'https://push2.eastmoney.com/api/qt/clist/get?pn={page}&pz=100&po=0&fields=f12,f14&fid=f12&fs=b:MK0021,b:MK0022'
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    for k, v in json.loads(resp.read().decode())['data']['diff'].items():
        all_etfs[v['f12']] = v['f14']
    time.sleep(0.3)

# 第二步：腾讯API批量拉取（无需延迟）
def get_prefix(code):
    return 'sh' if code.startswith('5') else 'sz'

success, failed = 0, []
for idx, (code, name) in enumerate(all_etfs.items()):
    fpath = os.path.join(KLINE_DIR, f'{code}.json')
    if os.path.exists(fpath):
        continue
    url = f'https://web.ifzq.gtimg.cn/appstock/app/kline/kline?param={get_prefix(code)}{code},day,2026-03-01,,60'
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        data = json.loads(urllib.request.urlopen(req, context=ctx, timeout=15).read())
        full_code = f'{get_prefix(code)}{code}'
        if 'data' in data and full_code in data['data']:
            klines = data['data'][full_code].get('day', [])
            result = [[k[0], k[1], k[2], k[3], k[4], k[5]] for k in klines if '2026-03-01' <= k[0] <= '2026-04-30']
            if result:
                with open(fpath, 'w') as f:
                    json.dump({'code': code, 'name': name, 'klines': result, 'count': len(result)}, f)
                success += 1
        else:
            failed.append(code)
    except:
        failed.append(code)

# 第三步：构建合并文件
all_data = {}
for code in all_etfs:
    fpath = os.path.join(KLINE_DIR, f'{code}.json')
    if os.path.exists(fpath):
        with open(fpath) as f:
            all_data[code] = json.load(f)
with open(os.path.join(DATA_DIR, 'all_kline_mar_apr.json'), 'w') as f:
    json.dump(all_data, f, ensure_ascii=False)

print(f"OK:{success} Failed:{len(failed)} Total:{sum(d['count'] for d in all_data.values())}条K线")
print(f"合并文件: {os.path.join(DATA_DIR, 'all_kline_mar_apr.json')}")
