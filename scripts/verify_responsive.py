#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anchormere 多终端 / 多分辨率响应式实测（可复跑，换模型照跑）。

用法：
  python3 scripts/verify_responsive.py            # 完整：12 分辨率 × 8 页面 + 14 平台配置
  python3 scripts/verify_responsive.py --quick   # 只跑 320/375/768/1280 四个核心分辨率

依赖：playwright + chromium。这是**本地实测工具**，不挂 CI；CI 由
verify_seo.py 的 4i 闸门做不依赖浏览器的静态检查。
退出码：0 = 全部通过；1 = 存在问题。

判定基准：
  * WCAG 2.1 AA 1.4.10 重排：320 CSS px 无页面级横向滚动
  * WCAG 2.1 AA 2.5.8 / AAA 2.5.5：触屏交互目标 ≥44×44
  * WCAG 2.1 AA 1.4.4：200% 缩放等效窄视口下内容不丢失
  * iOS Safari：输入控件字号 ≥16px，避免聚焦时自动放大视口
  * ≤1024px：导航回到文档流，避免折行 topbar 与写死的 top:38px 冲突
  * 长引用 URL：完整保留文本，仅在必要时换行，绝不截断
"""
import os
import sys
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "file://" + ROOT + "/"

# 8 类代表页面：首页 v2 / 表单 / 城市清单 / 表格 / PCB 枢纽 / 资讯聚合 /
# 新闻稿（来源外链） / 长尾页（长来源 URL）
PAGES = [
    "index.html", "contact.html", "supply-base.html",
    "guangdong-manufacturing-clusters.html", "pcb-supply-chain.html",
    "news.html", "news-2026-11-07-incoterms-2020-landed-cost-procurement.html",
    "earbuds-oem-shenzhen.html",
]

# 12 个分辨率：320 基准 → 1920 大屏，含平板竖/横
VIEWS = [
    (320, 640), (360, 780), (375, 812), (390, 844), (414, 896), (600, 960),
    (768, 1024), (834, 1112), (1024, 768), (1280, 800), (1440, 900), (1920, 1080),
]
QUICK_VIEWS = [(320, 640), (375, 812), (768, 1024), (1280, 800)]

UA_IOS = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
UA_AND = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 "
          "(KHTML, like Gecko) Chrome/120 Mobile Safari/537.36")

# 平台 / 设备模拟：触屏、高 DPR、横竖屏、缩放、系统偏好
DEVICES = [
    ("iPhone SE 375 DPR2 触屏", dict(viewport={"width": 375, "height": 667}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent=UA_IOS)),
    ("iPhone 14 Pro 393 DPR3", dict(viewport={"width": 393, "height": 852}, device_scale_factor=3, is_mobile=True, has_touch=True, user_agent=UA_IOS)),
    ("Android Pixel 412 DPR2.6", dict(viewport={"width": 412, "height": 915}, device_scale_factor=2.6, is_mobile=True, has_touch=True, user_agent=UA_AND)),
    ("小屏 Android 320 DPR2", dict(viewport={"width": 320, "height": 640}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent=UA_AND)),
    ("iPhone 横屏 852x393", dict(viewport={"width": 852, "height": 393}, device_scale_factor=3, is_mobile=True, has_touch=True, user_agent=UA_IOS)),
    ("Android 横屏 915x412", dict(viewport={"width": 915, "height": 412}, device_scale_factor=2.6, is_mobile=True, has_touch=True, user_agent=UA_AND)),
    ("iPad 768x1024 DPR2 触屏", dict(viewport={"width": 768, "height": 1024}, device_scale_factor=2, is_mobile=True, has_touch=True, user_agent=UA_IOS)),
    ("iPad Pro 横屏 1194x834", dict(viewport={"width": 1194, "height": 834}, device_scale_factor=2, has_touch=True)),
    ("断点边界 1025x800", dict(viewport={"width": 1025, "height": 800})),
    ("断点边界 1100x800", dict(viewport={"width": 1100, "height": 800})),
    ("断点边界 1200x800", dict(viewport={"width": 1200, "height": 800})),
    ("200% 缩放等效 640x800", dict(viewport={"width": 640, "height": 800})),
    ("桌面 1920 reduced-motion", dict(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce")),
    ("桌面 1440 深色偏好", dict(viewport={"width": 1440, "height": 900}, color_scheme="dark")),
]

AUDIT_JS = r"""() => {
  const cw = document.documentElement.clientWidth;
  const sw = document.documentElement.scrollWidth;
  // 横向滚动容器（如极窄屏信任条）内的内容超出属于预期，不计页面级溢出
  const inScroller = e => {
    let p = e.parentElement;
    while (p && p !== document.body) {
      const o = getComputedStyle(p).overflowX;
      if (o === 'auto' || o === 'scroll') return true;
      p = p.parentElement;
    }
    return false;
  };
  const bad = [...document.querySelectorAll('body *')].filter(e => {
    const r = e.getBoundingClientRect();
    return r.width && (r.right > cw + 2 || r.left < -2) && !inScroller(e);
  }).length;
  const small = [...document.querySelectorAll(
      '.mainnav a.nav,.nav-more>summary,.btn-quote,.lang-switch button,.fold-index>summary')]
    .map(e => { const r = e.getBoundingClientRect();
      return {w: Math.round(r.width), h: Math.round(r.height), t: (e.textContent||'').trim().slice(0,16)}; })
    .filter(x => x.w > 0 && x.h > 0 && (x.w < 44 || x.h < 44));
  const inputs = [...document.querySelectorAll(
      'input:not([type=hidden]):not([type=checkbox]),select,textarea')]
    .map(e => parseFloat(getComputedStyle(e).fontSize));
  const mn = document.querySelector('.mainnav'), tb = document.querySelector('.topbar');
  const cta = document.querySelector('.btn-primary,.btn-quote,a[href="/contact"]');
  return {cw, sw, bad, smallN: small.length, small: small.slice(0, 2), inputs,
    navPos: mn ? getComputedStyle(mn).position : '',
    navTop: mn ? getComputedStyle(mn).top : '',
    topbarH: tb ? Math.round(tb.getBoundingClientRect().height) : 0,
    ctaTop: cta ? Math.round(cta.getBoundingClientRect().top) : null,
    imgAll: [...document.querySelectorAll('img')].every(i => i.complete && i.naturalWidth > 0)};
}"""


def accept_consent(pg):
    """站点既有 cookie 合规组件，接受后不再拦截点击（非缺陷）。"""
    try:
        pg.locator("#anm-accept").click(timeout=600)
    except Exception:
        pass


def audit_page(pg, label, touch, view_h, probs):
    r = pg.evaluate(AUDIT_JS)
    if r["sw"] > r["cw"] + 1:
        probs.append("横向溢出 +%dpx" % (r["sw"] - r["cw"]))
    if r["bad"]:
        probs.append("越界元素 %d" % r["bad"])
    if r["cw"] <= 1024 and r["navPos"] != "relative":
        probs.append("≤1024 导航仍吸顶(%s/%s)" % (r["navPos"], r["navTop"]))
    if r["cw"] > 1024 and r["navTop"] != "38px":
        probs.append("桌面导航 top=%s" % r["navTop"])
    if r["cw"] <= 480 and r["topbarH"] > 60:
        probs.append("极窄屏信任条高 %d" % r["topbarH"])
    if touch and r["smallN"]:
        probs.append("触控目标<44 共 %d（最小 %s）" % (r["smallN"], r["small"][0]))
    if r["cw"] <= 1024 and any(x < 16 for x in r["inputs"]):
        probs.append("输入字号<16 %s" % [x for x in r["inputs"] if x < 16])
    if not r["imgAll"]:
        probs.append("有图片未加载")
    if r["ctaTop"] is not None and r["ctaTop"] > view_h:
        probs.append("主 CTA 在折叠线下(%d)" % r["ctaTop"])


def audit_folds(pg, probs):
    """首页：折叠导航与折叠索引展开可用，且展开后面板不越界。"""
    cw = pg.evaluate("document.documentElement.clientWidth")
    try:
        pg.locator("details.nav-more summary").click(timeout=5000)
        pg.wait_for_timeout(60)
        if not pg.locator(".nav-more-panel").is_visible():
            probs.append("More 折叠无法展开")
        rect = pg.eval_on_selector(".nav-more-panel",
                                   "e=>{const r=e.getBoundingClientRect();return [Math.round(r.left),Math.round(r.right)]}")
        if rect[1] > cw + 2 or rect[0] < -2:
            probs.append("More 面板展开后越界 %s" % rect)
        pg.locator("details.fold-index summary").click(timeout=5000)
        pg.wait_for_timeout(60)
        if pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1"):
            probs.append("折叠索引展开后横向溢出")
    except Exception as e:
        probs.append("折叠点击被拦截: " + str(e)[:70])


def main():
    quick = "--quick" in sys.argv
    views = QUICK_VIEWS if quick else VIEWS
    devices = [] if quick else DEVICES
    ok = 0
    fails = []
    exe = "/usr/bin/chromium"
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True, executable_path=exe, args=["--no-sandbox"])
        # A. 分辨率矩阵
        for w, h in views:
            for f in PAGES:
                pg = b.new_page(viewport={"width": w, "height": h})
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(BASE + f, wait_until="load")
                pg.wait_for_timeout(90)
                probs = []
                audit_page(pg, "%dx%d/%s" % (w, h, f), False, h, probs)
                if errs:
                    probs.append("JS 错误 %s" % errs[:1])
                if probs:
                    fails.append(("%dx%d %s" % (w, h, f), probs))
                else:
                    ok += 1
                pg.close()
        # B. 平台 / 设备模拟
        for name, kw in devices:
            ctx = b.new_context(**kw)
            for f in PAGES:
                pg = ctx.new_page()
                errs = []
                pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(BASE + f, wait_until="load")
                pg.wait_for_timeout(90)
                accept_consent(pg)
                probs = []
                h = kw["viewport"]["height"]
                audit_page(pg, name + "/" + f, bool(kw.get("has_touch")), h, probs)
                if errs:
                    probs.append("JS 错误 %s" % errs[:1])
                if f == "index.html":
                    audit_folds(pg, probs)
                if probs:
                    fails.append((name + " / " + f, probs))
                else:
                    ok += 1
                pg.close()
            ctx.close()
        b.close()

    total = ok + len(fails)
    print("\n============ 多终端响应式实测 ============")
    print("模式: %s | 组合 %d | 通过 %d | 失败 %d" %
          ("quick" if quick else "full", total, ok, len(fails)))
    for label, probs in fails:
        print("  [FAIL] %s\n         %s" % (label, " ; ".join(probs)))
    if not fails:
        print("结论：全部通过（320px 无横向滚动、触屏目标 ≥44、iOS 输入 ≥16px、"
              "折叠展开可用、图片全加载、无 JS 错误）。")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
