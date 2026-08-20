#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""腾讯行情批量查询脚本 — 从 qt.gtimg.cn 拉实时行情（2026-08-17验证）
用法:
  python3 fetch_tencent_quotes.py sh600598 sz000998 sh601952 ...
输出:
  code name price chg_pct mcap_yi (总市值单位: 亿元)
字段索引: f[1]=名称 f[2]=代码 f[3]=现价 f[32]=涨跌幅% f[38]=换手率 f[39]=PE f[45]=总市值(亿) f[46]=PB
"""
import re, sys, urllib.request

def fetch_quotes(codes):
    """codes: list of 'sh600598' style market-prefixed codes"""
    url = "https://qt.gtimg.cn/q=" + ",".join(codes)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    raw = urllib.request.urlopen(req, timeout=15).read().decode("gbk", errors="ignore")
    out = []
    for m in re.finditer(r'v_(\w+)="([^"]+)"', raw):
        f = m.group(2).split("~")
        if len(f) > 46:
            out.append({
                "code": f[2],
                "name": f[1],
                "price": f[3],
                "chg_pct": f[32],
                "turnover": f[38],
                "pe": f[39],
                "mcap_yi": f[45],
                "pb": f[46],
            })
    return out

if __name__ == "__main__":
    codes = sys.argv[1:]
    if not codes:
        print("usage: fetch_tencent_quotes.py sh600598 sz000998 ...")
        sys.exit(1)
    for item in fetch_quotes(codes):
        print(f"{item['code']} {item['name']} 现价:{item['price']} 涨跌%:{item['chg_pct']} 总市值(亿):{item['mcap_yi']} PE:{item['pe']} PB:{item['pb']}")
