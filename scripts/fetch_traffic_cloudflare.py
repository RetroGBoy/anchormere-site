#!/usr/bin/env python3
"""
Anchormere — Cloudflare 流量拉取脚本（GraphQL Analytics, 天级分组）

前置条件：
  1) pip install requests
  2) Cloudflare 后台获取 Zone ID 与 Analytics:Read 权限的 API Token（限定 anchormere.com zone）
  3) 环境变量 CF_API_TOKEN / CF_ZONE_ID
  4) 运行： python3 scripts/fetch_traffic_cloudflare.py

实现说明（重要）：
  - 当前 zone 为 Free 套餐，GraphQL Analytics 仅支持 date 维度，且无可靠的逐小时数据集。
  - 故用 httpRequests1dGroups 按天(date)分组，取最近数日明细。
  - Cloudflare Analytics 通常有数小时~半天延迟，最新「完整分析日」即网站最近约24h流量的可靠近似。
  - 真人/机器人、热门路径/国家/来源等维度需 Pro+ 套餐，请到 Cloudflare UI 或 GA4(Consent Mode v2)补充。
  - uniques 为指纹近似；threats 为被拦截/威胁请求数。
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
    date_geq = datetime.fromtimestamp(now - 3 * 86400, tz=timezone.utc).strftime("%Y-%m-%d")
    date_leq = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%d")

    url = "https://api.cloudflare.com/client/v4/graphql"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    query = """
    query GetAnalytics($zone: String!, $since: String!, $until: String!, $limit: Int!) {
      viewer {
        zones(filter: { zoneTag: $zone }) {
          daily: httpRequests1dGroups(
            limit: $limit
            filter: { date_geq: $since, date_leq: $until }
          ) {
            dimensions { date }
            sum { requests pageViews bytes threats }
            uniq { uniques }
          }
        }
      }
    }
    """
    payload = {
        "query": query,
        "variables": {"zone": zone, "since": date_geq, "until": date_leq, "limit": 100},
    }
    r = requests.post(url, json=payload, headers=headers, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Cloudflare GraphQL 返回 HTTP {r.status_code}: {r.text[:500]}")
    data = r.json()
    if data.get("errors"):
        sys.exit(f"Cloudflare GraphQL 错误：{json.dumps(data['errors'], ensure_ascii=False)}")
    zones = data.get("data", {}).get("viewer", {}).get("zones", [])
    if not zones:
        sys.exit("未找到该 zone（zone id 错误或 token 无该 zone 的 Analytics 读权限）")
    days = zones[0].get("daily") or []

    def g(obj, *path, default=0):
        cur = obj
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return cur

    def fnum(v):
        try:
            return f"{int(float(v)):,}"
        except Exception:
            return str(v)

    def parse_day(v):
        try:
            return str(v)
        except Exception:
            return ""

    rows = []
    for d in days:
        day = parse_day(d.get("dimensions", {}).get("date"))
        rows.append({
            "day": day,
            "requests": int(float(g(d, "sum", "requests"))),
            "pageViews": int(float(g(d, "sum", "pageViews"))),
            "bytes": float(g(d, "sum", "bytes", default=0)),
            "threats": int(float(g(d, "sum", "threats"))),
            "uniques": int(float(g(d, "uniq", "uniques"))),
        })
    rows.sort(key=lambda x: x["day"])

    print("=== Cloudflare 流量报告（真实边缘流量）===")
    print(f"查询窗口：{date_geq} → {date_leq} UTC（最近数日，天级）")
    print(f"注：Cloudflare Analytics 通常延迟数小时~半天，『最新完整分析日』即最近约24h 可靠近似\n")

    if rows:
        latest = rows[-1]
        print("=== ⭐ 最新完整分析日（≈ 过去24小时，受 Analytics 延迟）===")
        print(f"  日期 (UTC)        : {latest['day']}")
        print(f"  请求数 (requests)  : {fnum(latest['requests'])}")
        print(f"  页面浏览量 (PV)    : {fnum(latest['pageViews'])}")
        print(f"  独立访客 (近似)    : {fnum(latest['uniques'])}")
        print(f"  带宽 (GB)         : {latest['bytes']/1e9:,.2f}")
        print(f"  威胁/拦截         : {fnum(latest['threats'])}")

        last2 = rows[-2:]
        if len(last2) == 2:
            print("\n=== 近两日合计 ===")
            print(f"  日期              : {last2[0]['day']} + {last2[1]['day']}")
            print(f"  请求数            : {fnum(sum(r['requests'] for r in last2))}")
            print(f"  页面浏览量        : {fnum(sum(r['pageViews'] for r in last2))}")
            print(f"  独立访客(各日近似): {fnum(last2[0]['uniques'])} + {fnum(last2[1]['uniques'])}")
            print(f"  威胁/拦截         : {fnum(sum(r['threats'] for r in last2))}")

        print("\n=== 逐日趋势 ===")
        print(f"{'日期':<14}{'请求':>10}{'浏览量':>10}{'独立访客':>12}{'拦截':>8}")
        for r in rows:
            print(f"{r['day']:<14}{fnum(r['requests']):>10}{fnum(r['pageViews']):>10}{fnum(r['uniques']):>12}{fnum(r['threats']):>8}")

    print("\n完成。Free 套餐 GraphQL 仅支持 date 维度；热门路径/国家/来源/真人机器人等明细")
    print("请到 Cloudflare 控制台 Analytics 查看，或用 GA4（已部署 Consent Mode v2）补充维度。")


if __name__ == "__main__":
    main()
