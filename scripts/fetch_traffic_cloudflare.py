#!/usr/bin/env python3
"""
Anchormere — Cloudflare Pages 过去24小时流量拉取脚本

前置条件：
  1) pip install requests
  2) 在 Cloudflare 后台获取：
       - Zone ID（站点 anchormere.com 概览页）
       - API Token（My Profile → API Tokens → 创建，授予 Zone:Zone Analytics 读权限）
  3) 设置环境变量：
       export CF_API_TOKEN="你的token"
       export CF_ZONE_ID="你的zone_id"
  4) 运行： python3 scripts/fetch_traffic_cloudflare.py

说明：Cloudflare Analytics 几乎实时（分钟级），比 GA4 更快出数，
但只统计已接受/未拒绝 cookie 之外的所有边缘请求（含爬虫），
因此 PV/请求数通常高于 GA4 的"已同意用户"。
"""
import os
import sys
import json
import time
from datetime import datetime, timezone

try:
    import requests
except ImportError:
    sys.exit("缺少依赖：请先运行  pip install requests")


def main():
    token = os.environ.get("CF_API_TOKEN")
    zone = os.environ.get("CF_ZONE_ID")
    if not token or not zone:
        sys.exit("未设置 CF_API_TOKEN 或 CF_ZONE_ID")

    now = int(time.time())
    since = now - 24 * 3600
    url = f"https://api.cloudflare.com/client/v4/zones/{zone}/analytics/dashboard"
    params = {"since": since, "until": now, "continuous": "true"}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    r = requests.get(url, params=params, headers=headers, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Cloudflare API 返回 {r.status_code}: {r.text[:500]}")
    data = r.json()
    if not data.get("success"):
        sys.exit(f"Cloudflare API 失败：{data.get('errors')}")

    tots = data["result"]["totals"]
    ts = data["result"].get("timeseries", [])

    print("=== Cloudflare 过去24小时（边缘统计，含爬虫） ===")
    print(f"窗口：{datetime.fromtimestamp(since, tz=timezone.utc):%Y-%m-%d %H:%M} → "
          f"{datetime.fromtimestamp(now, tz=timezone.utc):%Y-%m-%d %H:%M} UTC")
    print(f"  总请求数 (requests)      : {tots.get('requests'):,}")
    print(f"  页面浏览量 (pageViews)   : {tots.get('pageViews'):,}")
    print(f"  独立访客 (uniqVisitors)  : {tots.get('uniqVisitors'):,}")
    print(f"  带宽 (bandwidth, MB)     : {tots.get('bandwidth', 0)/1e6:,.1f}")
    print(f"  威胁/拦截 (threats)      : {tots.get('threats'):,}")

    top_paths = data["result"].get("top_paths", [])
    if top_paths:
        print("\n=== 热门路径 Top 10 ===")
        for i, p in enumerate(top_paths[:10], 1):
            print(f"  {i:>2}. {p.get('path'):<55} 浏览量 {p.get('pageViews'):,}")

    top_countries = data["result"].get("top_countries", [])
    if top_countries:
        print("\n=== 访客国家/地区 Top 10 ===")
        for i, c in enumerate(top_countries[:10], 1):
            print(f"  {i:>2}. {c.get('alpha3', c.get('name','?')):<8} 访客 {c.get('uniqVisitors'):,}")

    top_referrers = data["result"].get("top_referers") or data["result"].get("top_referrers", [])
    if top_referrers:
        print("\n=== 来源域名 Top 10 ===")
        for i, rf in enumerate(top_referrers[:10], 1):
            print(f"  {i:>2}. {rf.get('referrer','?'):<45} 浏览量 {rf.get('pageViews'):,}")

    # 逐小时趋势
    if ts:
        print("\n=== 逐小时请求量（UTC） ===")
        for t in ts:
            ts_dt = datetime.fromtimestamp(t.get("min", t.get("when")), tz=timezone.utc)
            print(f"  {ts_dt:%m-%d %H:00}  请求 {t.get('requests'):>8,}  浏览 {t.get('pageViews'):>8,}")

    print("\n完成。提示：pageViews 含所有边缘请求；若数值明显大于 GA4，"
          "属正常（GA4 仅统计已接受 cookie 的真实访客）。")


if __name__ == "__main__":
    main()
