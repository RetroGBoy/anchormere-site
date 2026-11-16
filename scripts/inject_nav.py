#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站主导航收敛注入器 · 单一数据源 / 幂等 / 可逆 / 零 JS
========================================================
对应 modules.json 的 engine 模块（scripts/*.py 与 scripts/*.json 已被 glob 覆盖）。

需求：菜单里非核心（非主营 / 非主城市）入口可折叠，主体内容更突出。
做法：primary 外露并视觉加权，其余入口收进原生 <details>/<summary>。
  * 折叠项在 DOM 中仍是真实 <a href> 链接 → 爬虫可见、站内入链不减、
    孤儿页检测照常通过，关键词覆盖与转化路径零损失。
  * 原生 details：零 fetch、零第三方脚本、键盘 / 读屏可用、无 CLS 风险。
  * BEGIN/END 标记块整段替换；内容不变时 io_util.write_final 跳过写盘。
  * 生成器（longtail.py / news_digest.py / build_briefings.py / seo_inject.py）
    仍输出旧 NAV，但本注入器在 CI 的 Normalize 之后兜底，每日新闻页不回退。
  * --rollback 渲染一份「全部平铺且不带标记」的等价 nav，链接一条不少。

用法：python3 scripts/inject_nav.py [--rollback]
"""
import os
import re
import sys
import json
import html as html_lib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_util

ROOT = io_util.ROOT
CONFIG = os.path.join(ROOT, "scripts", "nav_source.json")
BEGIN = "<!-- NAV:BEGIN -->"
END = "<!-- NAV:END -->"
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)
NAV_RE = re.compile(r'<nav\b[^>]*class="[^"]*\bmainnav\b[^"]*"[^>]*>.*?</nav>\n?', re.S)
PROTECTED = {"index.html", "contact.html"}


def esc(v):
    return html_lib.escape(str(v), quote=True)


def esc_html_attr(v):
    """data-zh 允许合法的 HTML 内联标签（如 <small>），只转义 & 与双引号。

    lang.js 把 data-zh 的值当作 innerHTML 写入；若用通用 esc() 把 <small>
    转成 &lt;small&gt;，中文模式下 brand 会显示成字面文本而不是小字标签。
    """
    return str(v).replace("&", "&amp;").replace('"', "&quot;")


def load():
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def validate(c):
    errs = []
    items = list(c.get("primary") or []) + list(c.get("more") or []) + [c.get("cta") or {}]
    if not items or not all(items):
        return ["primary / more / cta 不得为空"]
    seen = set()
    for it in items:
        h, en, zh = it.get("href"), it.get("en"), it.get("zh")
        if not h or not h.startswith("/") or h.endswith(".html"):
            errs.append("href 必须是 clean URL（/ 开头、无 .html）：%r" % h)
        if not en or not zh:
            errs.append("缺 en / zh：%r" % it)
        if h in seen:
            errs.append("重复 href：%s" % h)
        seen.add(h)
    if not c.get("more_label_en") or not c.get("more_label_zh"):
        errs.append("缺 More 折叠标签的双语文本")
    return errs


def link(it, cls="nav"):
    return '<a class="%s" href="%s" data-zh="%s">%s</a>' % (
        cls, esc(it["href"]), esc(it["zh"]), esc(it["en"]))


def render(c, flat=False, marker=True):
    parts = [
        '<nav class="mainnav"><div class="container">',
        '<div class="brand" data-zh="%s">%s</div>' % (esc_html_attr(c["brand_zh"]), c["brand_en"]),
    ]
    for it in c["primary"]:
        parts.append(link(it))
    if flat:
        for it in c["more"]:
            parts.append(link(it))
    else:
        parts.append('<details class="nav-more"><summary data-zh="%s">%s</summary>'
                     % (esc(c["more_label_zh"]), esc(c["more_label_en"])))
        parts.append('<div class="nav-more-panel">')
        for it in c["more"]:
            parts.append(link(it))
        parts.append('</div></details>')
    parts.append(link(c["cta"], "nav btn-quote"))
    parts.append('</div></nav>')
    body = "".join(parts)
    if not marker:
        return body + "\n"
    return BEGIN + "\n" + body + "\n" + END + "\n"


def inject(text, block):
    """已注入 → 整块替换；未注入 → 替换第一个 mainnav。"""
    if BLOCK_RE.search(text):
        return BLOCK_RE.sub(lambda _m: block, text, count=1)
    m = NAV_RE.search(text)
    if not m:
        return None
    return text[:m.start()] + block + text[m.end():]


def strip(text):
    return BLOCK_RE.sub("", text)


def targets(pages):
    if "*" in pages:
        return io_util.expand(["*.html"])
    out = []
    for p in pages:
        name = p if p.endswith(".html") else p + ".html"
        if os.path.isfile(os.path.join(ROOT, name)):
            out.append(name)
        else:
            print("  ! 白名单页面不存在，跳过:", name)
    return sorted(set(out))


def main():
    c = load()
    errs = validate(c)
    if errs:
        print("nav: 数据源校验失败，拒绝写盘：")
        for e in errs:
            print("  -", e)
        return 1

    pages = c.get("pages") or []
    if not pages:
        print("nav: pages 为空 → 零读取、零写盘")
        return 0

    rollback = "--rollback" in sys.argv[1:]
    block = render(c, flat=rollback, marker=not rollback)
    names = targets(pages)
    allow_protected = bool(c.get("allow_protected"))
    changed = skipped = 0
    for name in names:
        if not io_util.selected(name):
            continue
        if name in PROTECTED and not allow_protected:
            print("  ! protected 核心页已跳过:", name)
            continue
        text = io_util.read_text(name)
        out = strip(text) if rollback else inject(text, block)
        if out is None:
            print("  ! 未找到 <nav class=\"mainnav\">，跳过:", name)
            skipped += 1
            continue
        if io_util.write_final(os.path.join(ROOT, name), out):
            changed += 1
    act = "平铺还原" if rollback else "折叠导航注入"
    print("nav: %s → %d 页写入 / %d 页目标 / %d 页跳过"
          % (act, changed, len(names), skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
