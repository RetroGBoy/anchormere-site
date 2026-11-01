#!/usr/bin/env python3
"""
Anchormere — GA4 过去24小时流量拉取脚本（滚动24h：昨天此刻 → 现在）

前置条件：
  1) pip install google-analytics-data google-auth
  2) 准备一份 GA4 Service Account JSON（需在 GA4 后台为该 property 授予
     "Viewer / 分析员" 角色，并启用 Data API）。
  3) 设置环境变量：
       export GOOGLE_APPLICATION_CREDENTIALS="/path/to/sa.json"
       export GA4_PROPERTY_ID="123456789"   # 数字 property ID，不是 G-XXXX
  4) 运行： python3 scripts/fetch_traffic_ga4.py

说明：GA4 默认最多延迟数小时出数；24h 窗口用 Data API 的 date 区间
（start=昨天此刻, end=今天）近似滚动24小时。
"""
import os
import sys
from datetime import datetime, timedelta, timezone

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, Dimension, Metric, DateRange, OrderBy,
    )
except ImportError:
    sys.exit("缺少依赖：请先运行  pip install google-analytics-data google-auth")


def get_client():
    creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds:
        sys.exit("未设置 GOOGLE_APPLICATION_CREDENTIALS（GA4 service account JSON 路径）")
    return BetaAnalyticsDataClient()


def property_id():
    pid = os.environ.get("GA4_PROPERTY_ID")
    if not pid:
        sys.exit("未设置 GA4_PROPERTY_ID（GA4 后台的数字 property ID，不是 G- 测量 ID）")
    return f"properties/{pid}"


def run_report(client, prop, dimensions, metrics, start, end, limit=20, order_by=None):
    req = RunReportRequest(
        property=prop,
        dimensions=[Dimension(name=d) for d in dimensions],
        metrics=[Metric(name=m) for m in metrics],
        date_ranges=[DateRange(start_date=start, end_date=end)],
        limit=limit,
        offset=0,
    )
    if order_by:
        req.order_bys.append(OrderBy(
            metric=OrderBy.MetricOrderBy(metric_name=order_by),
            desc=True,
        ))
    return client.run_report(req)


def fmt(v):
    try:
        return f"{int(float(v)):,}"
    except Exception:
        return v


def main():
    client = get_client()
    prop = property_id()
    tz = timezone.utc
    now = datetime.now(tz)
    start = (now - timedelta(hours=24)).strftime("%Y-%m-%d")
    end = now.strftime("%Y-%m-%d")
    print(f"查询窗口（UTC）：{start} → {end}（近似滚动24小时）\n")

    # 1) 总体概览
    res = run_report(
        client, prop,
        dimensions=["sessionDefaultChannelGroup", "deviceCategory"],
        metrics=["sessions", "totalUsers", "screenPageViews", "engagedSessions", "bounceRate"],
        start=start, end=end, limit=50,
    )
    print("=== 总体概览（按渠道 × 设备） ===")
    print(f"{'渠道':<22}{'设备':<12}{'会话':>10}{'用户':>10}{'浏览量':>12}{'跳出率':>10}")
    for row in res.rows:
        ch = row.dimension_values[0].value
        dev = row.dimension_values[1].value
        s = fmt(row.metric_values[0].value)
        u = fmt(row.metric_values[1].value)
        pv = fmt(row.metric_values[2].value)
        br = f"{float(row.metric_values[4].value)*100:.1f}%"
        print(f"{ch:<22}{dev:<12}{s:>10}{u:>10}{pv:>12}{br:>10}")

    # 2) 热门页面
    res = run_report(
        client, prop,
        dimensions=["pagePath"],
        metrics=["screenPageViews", "sessions", "averageEngagementTimePerSession"],
        start=start, end=end, limit=15, order_by="screenPageViews",
    )
    print("\n=== 热门页面 Top 15 ===")
    print(f"{'页面路径':<55}{'浏览量':>10}{'会话':>10}{'平均停留':>12}")
    for row in res.rows:
        p = row.dimension_values[0].value
        pv = fmt(row.metric_values[0].value)
        s = fmt(row.metric_values[1].value)
        at = f"{float(row.metric_values[2].value):.0f}s"
        print(f"{p:<55}{pv:>10}{s:>10}{at:>12}")

    # 3) 转化（generate_lead 等）
    for ev in ["generate_lead", "contact_click", "whatsapp_click"]:
        res = run_report(
            client, prop,
            dimensions=["eventName"],
            metrics=["eventCount", "conversions"],
            start=start, end=end, limit=3,
        )
        print(f"\n=== 转化事件：{ev} ===")
        found = False
        for row in res.rows:
            if row.dimension_values[0].value == ev:
                found = True
                print(f"  事件次数(eventCount): {fmt(row.metric_values[0].value)}  |  转化(conversions): {fmt(row.metric_values[1].value)}")
        if not found:
            print("  （该窗口内无此事件数据）")

    print("\n完成。若数字为 0，可能是：(a) GA4 数据延迟；(b) 访客尚未接受 cookie（默认不加载 GA4）；(c) property ID 或权限配置有误。")


if __name__ == "__main__":
    main()
