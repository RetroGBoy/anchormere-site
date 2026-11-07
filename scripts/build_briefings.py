#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Anchormere sourcing briefings — HTML renderer.

Reads scripts/briefings.json (the single content source) and renders one
dated news post per briefing as news-YYYY-MM-DD-<slug>.html.

Design notes
------------
* Every briefing carries outbound, editorially cited links to public standards
  bodies / government sources. Each link's **full URL is printed verbatim** in
  the visible "Sources & references" block as a source attribution.
* Every briefing carries a "Key terms" glossary of domain-specific terms,
  also exposed as schema.org DefinedTermSet for search engines and AI systems.
* The Article JSON-LD carries `citation` for every external reference.
* Files are named news-<date>-<slug>.html so the daily CI (news_digest.py
  -> scan_articles / rebuild_indexes) and build_sitemap.py pick them up
  automatically. Nothing here is a one-off page edit that CI can overwrite.

Pure standard library. Run: python3 scripts/build_briefings.py
"""
import os
import re
import json
import html
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SITE = "https://anchormere.com"

DATA = json.load(open(os.path.join(HERE, "briefings.json"), encoding="utf-8"))
ORG_LD = open(os.path.join(HERE, "org_entity.json"), encoding="utf-8").read().strip()
SOURCES = DATA["sources"]
GLOSSARY = DATA["glossary"]
PUBLISHED = DATA["published"]

PLACEHOLDER = re.compile(r"\[\[([A-Za-z0-9_]+)(?:\|([^\]]+))?\]\]")

TOPBAR = '<div class="topbar"><span data-zh="⚓ <b>48 小时报价</b>">⚓ <b>48h quote</b></span><span data-zh="🏭 <b>20+ 家认证工厂</b>">🏭 <b>20+ vetted factories</b></span><span data-zh="📦 <b>500 件起订</b>">📦 <b>500 pcs MOQ</b></span><span data-zh="📑 <b>完整出口单证</b>">📑 <b>Full export docs</b></span></div>'

NAV = '''<nav class="mainnav"><div class="container">
  <div class="brand" data-zh="Anchormere <small>锚泊 · 中国采购合作伙伴</small>">Anchormere <small>锚泊 · 中国采购合作伙伴</small></div>
  <a class="nav" href="index.html" data-zh="首页">Home</a><a class="nav" href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a>
  <a class="nav" href="cable-management.html" data-zh="线缆管理">Cable Mgmt</a><a class="nav" href="capabilities.html" data-zh="供应能力">Capabilities</a>
  <a class="nav" href="certifications.html" data-zh="认证说明">Certifications</a>
  <a class="nav" href="about.html" data-zh="关于我们">About</a>  <a class="nav" href="faq.html" data-zh="常见问题">FAQ</a>
  <a class="nav" href="supply-base.html" data-zh="供应基地">Supply Base</a>
  <a class="nav" href="news.html" data-zh="资讯动态">News</a>
  <a class="btn-quote" href="contact.html" data-zh="获取报价">Get a Quote</a>
</div></nav>'''

FOOTER = '''<footer><div class="container">
  <div class="cols">
    <div><h4 data-zh="Anchormere 锚泊 · 中国采购合作伙伴">Anchormere 锚泊 · 中国采购合作伙伴</h4><ul><li data-zh="中国采购合作伙伴 · OEM · 采购 · 联合制造 · 大湾区">China sourcing partner · OEM · sourcing · joint manufacturing · Greater Bay Area</li><li data-zh="中国 · 大湾区">Greater Bay Area, China</li><li>中国广东深圳市光明区特发工业园B座</li></ul></div>
    <div><h4 data-zh="产品">Products</h4><ul><li><a href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a></li><li><a href="cable-management.html" data-zh="线缆管理">Cable Management</a></li><li><a href="consumer-smart-electronics.html" data-zh="消费与智能电子">Consumer &amp; Smart Electronics</a></li><li><a href="smart-toys-devices.html" data-zh="智能玩具与设备">Smart Toys &amp; Devices</a></li><li><a href="supply-base.html" data-zh="供应基地">Supply Base</a></li></ul></div>
    <div><h4 data-zh="公司">Company</h4><ul><li><a href="about.html" data-zh="关于我们">About</a></li><li><a href="capabilities.html" data-zh="供应能力">Capabilities</a></li><li><a href="certifications.html" data-zh="认证说明">Certifications</a></li><li><a href="faq.html" data-zh="常见问题">FAQ</a></li>
    <li><a href="process.html" data-zh="合作流程">Process</a></li><li><a href="quality.html" data-zh="品质管控">Quality</a></li><li><a href="shipping.html" data-zh="包装物流">Shipping</a></li></ul></div>
    <div><h4 data-zh="法律">Legal</h4><ul><li data-zh="运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）">Operator: 深圳森亚实业有限公司 (Shenzhen Senya Industrial Co., Ltd.)</li><li data-zh="商标：Anchormere / Buyeex">Trade mark: Anchormere / Buyeex</li></ul></div>
  </div>
  <p style="margin-top:20px;text-align:center;color:var(--on-dark2)" data-zh="© 2026 Anchormere · 由深圳森亚实业有限公司运营">© 2026 Anchormere · Operated by 深圳森亚实业有限公司</p>
  <p style="margin-top:6px;text-align:center;color:var(--on-dark2);font-size:12px;opacity:.75" data-zh="最后更新：DATE">Last updated: DATE</p>
</div><p style="text-align:center;margin-top:10px;font-size:12px"><a href="privacy.html" data-zh="隐私政策">Privacy Policy</a> · <a href="terms.html" data-zh="服务条款">Terms &amp; Conditions</a></p>
</footer>
<a class="wa-float" href="https://wa.me/8619068984158" data-zh="💬 WhatsApp 咨询">💬 WhatsApp</a>
<script defer src="assets/lang.js"></script>
</body></html>'''

URL_STYLE = ("font-size:12px;color:var(--slate);word-break:break-all;"
             "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace")
TERM_STYLE = ("background:var(--paper2);border-left:3px solid var(--brass);"
              "padding:10px 14px;margin:10px 0;border-radius:0 6px 6px 0")
POINT_STYLE = "border-bottom:1px solid rgba(0,0,0,.06);padding:14px 0"


def esc(t):
    return html.escape(t, quote=False)


def esc_attr(t):
    return html.escape(t, quote=True)


def link_for(key, label):
    """Resolve [[key|label]]: authoritative outbound link, or in-page glossary anchor."""
    label_e = esc(label)
    if key in SOURCES:
        s = SOURCES[key]
        return (f'<a href="{esc_attr(s["url"])}" target="_blank" '
                f'rel="noopener noreferrer" title="{esc_attr(s["name"])}">{label_e}</a>')
    g = GLOSSARY[key]
    return (f'<a class="gloss-ref" href="#term-{esc_attr(key)}" '
            f'title="{esc_attr(g["term"])}">{label_e}</a>')


def render_text(text):
    """Escape plain text and resolve [[key|label]] placeholders into links."""
    out, last = [], 0
    for m in PLACEHOLDER.finditer(text):
        out.append(esc(text[last:m.start()]))
        key = m.group(1)
        label = m.group(2) or (SOURCES.get(key, {}).get("name")
                               or GLOSSARY.get(key, {}).get("term") or key)
        out.append(link_for(key, label))
        last = m.end()
    out.append(esc(text[last:]))
    return "".join(out)


def collect_source_keys(b):
    """All outbound keys actually cited in the body, plus the declared source list."""
    keys, seen = [], set()
    def add(k):
        if k in SOURCES and k not in seen:
            seen.add(k)
            keys.append(k)
    for p in b["points"]:
        for k in p[4]:
            add(k)
        for txt in (p[2], p[3]):
            for k in PLACEHOLDER.findall(txt):
                add(k[0])
    for k in b["sources"]:
        add(k)
    return keys


def build_points(b):
    rows = []
    for i, p in enumerate(b["points"], 1):
        h_en, h_zh, en, zh, _refs = p
        rows.append(
            f'  <div style="{POINT_STYLE}">\n'
            f'    <h3 style="font-size:17px;margin:0 0 6px">{i:02d}. {esc(h_en)}'
            f'<span class="cn" style="display:block;font-size:13px;font-weight:400;color:var(--slate)">{esc(h_zh)}</span></h3>\n'
            f'    <p style="margin:0 0 4px">{render_text(en)}</p>\n'
            f'    <p class="cn" style="margin:0">{render_text(zh)}</p>\n'
            f'  </div>\n'
        )
    return "".join(rows)


def build_terms(b, page_url):
    rows = []
    for k in b["terms"]:
        g = GLOSSARY[k]
        rows.append(
            f'  <div id="term-{esc_attr(k)}" style="{TERM_STYLE}">\n'
            f'    <b>{esc(g["term"])}</b>\n'
            f'    <p style="margin:4px 0 0">{esc(g["en"])}</p>\n'
            f'    <p class="cn" style="margin:3px 0 0">{esc(g["zh"])}</p>\n'
            f'  </div>\n'
        )
    ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "DefinedTermSet",
        "name": f"Key terms — {b['title_en']}",
        "inLanguage": "en",
        "url": page_url + "#key-terms",
        "hasDefinedTerm": [
            {"@type": "DefinedTerm", "name": GLOSSARY[k]["term"],
             "description": GLOSSARY[k]["en"],
             "url": page_url + f"#term-{k}",
             "inDefinedTermSet": {"@type": "DefinedTermSet", "url": page_url + "#key-terms"}}
            for k in b["terms"]
        ],
    }, ensure_ascii=False)
    return "".join(rows), ld


def build_sources(keys):
    """Visible source attributions: publisher + clickable title + full URL printed verbatim."""
    rows = []
    for i, k in enumerate(keys, 1):
        s = SOURCES[k]
        u = esc(s["url"])
        ua = esc_attr(s["url"])
        rows.append(
            f'  <li style="margin:0 0 12px">\n'
            f'    <b>{i:02d}</b> · {esc(s["name"])} <span class="cn">（{esc(s["zh"])}）</span><br>\n'
            f'    <a href="{ua}" target="_blank" rel="noopener noreferrer">{esc(s["title"])}</a><br>\n'
            f'    <span style="{URL_STYLE}">Source URL: '
            f'<a href="{ua}" target="_blank" rel="noopener noreferrer"><code>{u}</code></a></span>\n'
            f'  </li>\n'
        )
    return "".join(rows)


def build_internal(b):
    return " · ".join(
        f'<a href="{esc_attr(f)}">{esc(label)}</a>' for f, label in b["internal"]
    )


def build_article_ld(b, page_url, keys, word_count):
    about = [k.strip() for k in b["keywords"].split(",") if k.strip()][:6]
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": b["title_en"],
        "alternativeHeadline": b["title_zh"],
        "description": b["desc_en"],
        "keywords": b["keywords"],
        "articleSection": "Sourcing briefing",
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "wordCount": word_count,
        "datePublished": PUBLISHED,
        "dateModified": PUBLISHED,
        "author": {"@type": "Organization", "name": "Anchormere", "url": SITE},
        "publisher": {"@type": "Organization", "name": "Anchormere", "url": SITE},
        "mainEntityOfPage": page_url,
        "about": [{"@type": "Thing", "name": a} for a in about],
        "citation": [
            {"@type": "CreativeWork", "name": SOURCES[k]["title"],
             "url": SOURCES[k]["url"],
             "publisher": {"@type": "Organization", "name": SOURCES[k]["name"]}}
            for k in keys
        ],
    }, ensure_ascii=False)


def build_webpage_ld(b, page_url):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "url": page_url,
        "name": b["title_en"],
        "inLanguage": "en",
        "lastReviewed": PUBLISHED,
        "reviewedBy": {"@type": "Organization", "name": "Anchormere sourcing desk"},
        "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
    }, ensure_ascii=False)


def build_breadcrumb_ld(b, page_url):
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "News & Insights", "item": SITE + "/news"},
            {"@type": "ListItem", "position": 3, "name": b["title_en"], "item": page_url},
        ],
    }, ensure_ascii=False)


def render(b):
    slug = f"news-{PUBLISHED}-{b['slug']}"
    filename = slug + ".html"
    page_url = f"{SITE}/{slug}"
    keys = collect_source_keys(b)
    points_html = build_points(b)
    terms_html, terms_ld = build_terms(b, page_url)
    sources_html = build_sources(keys)
    internal_html = build_internal(b)
    word_count = len(" ".join(p[2] for p in b["points"]).split()) + \
                 len(" ".join(GLOSSARY[k]["en"] for k in b["terms"]).split())
    desc_zh = f"{b['title_zh']}——10 项可核对要点，附官方来源网址标注与专有名词释义。"
    serp_t = esc_attr(b["serp_title"])
    serp_d = esc_attr(b["desc_en"])

    article_ld = build_article_ld(b, page_url, keys, word_count)
    webpage_ld = build_webpage_ld(b, page_url)
    crumb_ld = build_breadcrumb_ld(b, page_url)

    doc = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{serp_t} | Anchormere</title>
<meta name="title-zh" content="{esc_attr(b['title_zh'])}">
<meta name="card-title" content="{esc_attr(b['title_en'])}">
<meta name="card-title-zh" content="{esc_attr(b['title_zh'])}">
<meta name="content-kind" content="briefing">
<meta name="keywords" content="{esc_attr(b['keywords'])}">
<meta name="description" content="{serp_d}">
<meta name="desc-zh" content="{esc_attr(desc_zh)}">
<link rel="canonical" href="{page_url}">
<link rel="alternate" hreflang="en" href="{page_url}">
<link rel="alternate" hreflang="x-default" href="{page_url}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Anchormere">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="zh_CN">
<meta property="og:title" content="{serp_t} | Anchormere">
<meta property="og:description" content="{serp_d}">
<meta property="og:url" content="{page_url}">
<meta property="og:image" content="{SITE}/assets/img/office-team.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{serp_t} | Anchormere">
<meta name="twitter:description" content="{serp_d}">
<meta name="twitter:image" content="{SITE}/assets/img/office-team.jpg">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/consent.css">
<script type="application/ld+json">
{article_ld}
</script>
<script type="application/ld+json">{ORG_LD}</script>
<script type="application/ld+json">{crumb_ld}</script>
<script type="application/ld+json">{terms_ld}</script>
<script type="application/ld+json">{webpage_ld}</script>
<script defer src="assets/consent.js"></script>
</head><body>
{TOPBAR}
{NAV}
<section class="l1"><div class="container">
  <div class="crumb"><a href="index.html" data-zh="首页">Home</a> / <a href="news.html" data-zh="资讯动态">News</a> / <span data-zh="采购情报简报">Sourcing briefing</span></div>
  <div class="eyebrow" data-zh="采购情报简报 · 发布于 {PUBLISHED} · 附外链来源与专有名词">Sourcing briefing · published {PUBLISHED} · cited sources &amp; glossary</div>
  <h1 data-zh="{esc_attr(b['title_zh'])}">{esc(b['title_en'])}</h1>
  <p class="cn">{esc(b['title_zh'])}</p>
  <p class="lead" data-zh="{esc_attr(b['intro_zh'])}">{esc(b['intro_en'])}</p>
  <p class="cn">{esc(b['intro_zh'])}</p>

  <h2 data-zh="十项核查要点">The ten checks</h2>
{points_html}
  <h2 data-zh="对你的询盘意味着什么">What this means for your RFQ</h2>
  <p data-zh="{esc_attr(b['angle_zh'])}">{esc(b['angle_en'])}</p>
  <p class="cn">{esc(b['angle_zh'])}</p>
  <p data-zh="继续阅读相关页面：">Related pages: {internal_html}</p>

  <h2 id="key-terms" data-zh="专有名词释义">Key terms</h2>
  <p data-zh="以下为本文涉及的行业专有名词，按公开标准与通行用法释义，供 RFQ 沟通时统一口径。">Domain terms used above, defined against public standards and common trade usage so your RFQ speaks the same language as the factory.</p>
{terms_html}
  <h2 data-zh="来源与外链网址标注">Sources &amp; references</h2>
  <p data-zh="以下外部链接为对公开标准机构与政府来源的编辑性引用。为便于独立核验，每条均标注完整链接网址（Source URL）。">The outbound links above are editorial citations to public standards bodies and government sources. Each full link URL is printed below as a source attribution so your team can verify it independently.</p>
  <ol style="padding-left:20px">
{sources_html}  </ol>
  <p class="review-note" style="color:var(--slate);font-size:13px;margin-top:18px" data-zh="由 Anchormere 采购编辑组复核 · {PUBLISHED}">Reviewed by the Anchormere sourcing desk · {PUBLISHED}</p>
  <p style="color:var(--slate);font-size:12px" data-zh="外部链接归属原发布方，Anchormere 与其无隶属关系，亦不主张其背书；名词释义为买家参考摘要，具体规格与适用标准请以 RFQ 阶段的现行官方文本为准。">External links remain the property of their publishers; Anchormere is not affiliated with, nor endorsed by, any cited body. Definitions are buyer-facing summaries — confirm current official texts and final specifications at RFQ.</p>
  <div style="background:var(--paper2);border-left:4px solid var(--brass);padding:14px 18px;margin:18px 0;border-radius:0 8px 8px 0">
    <b data-zh="需要一份对应你产品的规格与合规清单？">Need a spec and compliance checklist for your product?</b> <span data-zh="发送品类与目的市场，我们将在 48 小时内返回整合报价与单证清单。">Send the category and destination market and we'll return a consolidated quote and document checklist within 48h.</span> <a href="contact.html" data-zh="获取报价 →">Get a quote →</a>
  </div>
</div></section>
{FOOTER.replace('DATE', PUBLISHED)}
'''
    return filename, doc


def main():
    written = []
    for b in DATA["briefings"]:
        filename, doc = render(b)
        with open(os.path.join(ROOT, filename), "w", encoding="utf-8") as f:
            f.write(doc)
        written.append(filename)
        print(f"  + {filename} ({len(doc)} bytes)")
    print(f"Done. {len(written)} briefing pages written.")
    return written


if __name__ == "__main__":
    main()
