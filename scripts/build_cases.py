#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the public case-reference hub page from scripts/case_references.json.

The hub collects real, publicly reported sourcing / customs cases (Reuters,
QIMA, U.S. CBP rulings, listed-company filings) and shows each one's full
source URL in plain text. It is an editorial reference, NOT a portfolio of
Anchormere clients: the disclaimer is rendered prominently and mirrored in
structured data, so neither readers nor answer engines can misread it as an
endorsement or a customer list.

Design constraints (workarea incremental system):
  * single source of truth = scripts/case_references.json (no hard-coded cases)
  * writes only through io_util.write_final -> html_finalize.normalize (idempotent)
  * honours io_util.selected() so the incremental plan controls the scope
  * nav/footer/organisation entities reused from longtail.py + org_entity.json
"""
import os, sys, json, html

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import io_util
import longtail  # reuse NAV / FOOTER / REVIEW_DATE / clip_* / ORG_ID / SITE

ROOT = longtail.ROOT
SITE = longtail.SITE
ORG_ID = longtail.ORG_ID
REVIEW_DATE = "2026-11-08"
HUB_SLUG = "sourcing-case-studies"
URL = SITE + "/" + HUB_SLUG


def esc(s):
    return html.escape(str(s), quote=True)


def case_card(c, all_seeds_titles):
    """One case: facts, buyer takeaway, full source URL in plain text, internal links."""
    src = (f'<p class="src">Source URL: '
           f'<a href="{esc(c["source_url"])}" target="_blank" rel="noopener noreferrer">{esc(c["source_url"])}</a></p>')
    if c.get("source_url_alt"):
        src += (f'<p class="src alt">Additional source URL: '
                f'<a href="{esc(c["source_url_alt"])}" target="_blank" rel="noopener noreferrer">{esc(c["source_url_alt"])}</a></p>')
    links = []
    for sl in c["slugs"]:
        title = all_seeds_titles.get(sl)
        if title:
            links.append(f'<a href="{esc(sl)}.html">{esc(title)}</a>')
    rel = ('<p class="rel-links" data-zh="相关采购主题：">Related sourcing topics: '
           + ' · '.join(links) + '</p>') if links else ''
    return f'''<article class="case-card" id="{esc(c["id"])}">
  <div class="case-meta">{esc(c["date"])} &middot; {esc(c["source"])}</div>
  <h3>{esc(c["en_title"])}</h3>
  <p class="cn" lang="zh-CN">{esc(c["zh_title"])}</p>
  <p>{esc(c["en_summary"])}</p>
  <p class="cn" lang="zh-CN">{esc(c["zh_summary"])}</p>
  <p class="takeaway"><b>Buyer takeaway &middot; 采购启示：</b>{esc(c["en_lesson"])}</p>
  <p class="cn takeaway" lang="zh-CN"><b>采购启示：</b>{esc(c["zh_lesson"])}</p>
  {src}
  {rel}
</article>'''


def build():
    data = json.load(open(os.path.join(_HERE, "case_references.json"), encoding="utf-8"))
    seeds = json.load(open(os.path.join(ROOT, "scripts", "longtail_seeds.json"), encoding="utf-8"))
    titles = {s["slug"]: s["en_title"] for s in seeds}
    cases = data["cases"]
    groups = data["groups"]
    disc = data["disclaimer"]

    # ---- group sections ----
    sections = []
    for g in groups:
        items = [c for c in cases if c["group"] == g["id"]]
        if not items:
            continue
        cards = "\n".join(case_card(c, titles) for c in items)
        sections.append(f'''<section class="l2"><div class="container">
  <h2 data-zh="{esc(g["zh"])}">{esc(g["en"])}</h2>
  <p class="cn" lang="zh-CN">{esc(g["zh"])}</p>
  <div class="case-list">{cards}</div>
</div></section>''')
    sections_html = "\n".join(sections)

    # ---- JSON-LD ----
    org = open(os.path.join(_HERE, "org_entity.json"), encoding="utf-8").read().strip()
    website = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": "Anchormere", "url": SITE, "inLanguage": ["en", "zh"],
        "publisher": {"@id": ORG_ID}, "about": {"@id": ORG_ID},
    }, ensure_ascii=False)
    bc = json.dumps({
        "@context": "https://schema.org", "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "Sourcing case references", "item": URL},
        ],
    }, ensure_ascii=False)
    has_part = [{
        "@type": "CreativeWork", "name": c["en_title"], "description": c["en_summary"],
        "publisher": {"@id": ORG_ID},
        "citation": {"@type": "CreativeWork", "name": c["source"], "url": c["source_url"]},
    } for c in cases]
    collection = json.dumps({
        "@context": "https://schema.org", "@type": "CollectionPage",
        "@id": URL + "#collection", "name": "Publicly reported China sourcing case references",
        "description": disc["en"], "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
        "publisher": {"@id": ORG_ID}, "numberOfItems": len(cases), "hasPart": has_part,
    }, ensure_ascii=False)
    faq = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Are these Anchormere client projects?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. Every case is drawn from public reporting, an official ruling or a public company filing. They are industry references, not Anchormere clients, partners or endorsements."}},
            {"@type": "Question", "name": "Why does every case show a full source URL?",
             "acceptedAnswer": {"@type": "Answer", "text": "So buyers and answer engines can verify the facts at the original source. We do not claim another company's project as our own work."}},
            {"@type": "Question", "name": "How do I apply these cases to my own RFQ?",
             "acceptedAnswer": {"@type": "Answer", "text": "Use them as prompts for landed-cost modelling, HTS classification, country-of-origin analysis and supplier audits. Send a photo or part number and an engineer replies within 48 hours."}},
        ],
    }, ensure_ascii=False)
    webpage = json.dumps({
        "@context": "https://schema.org", "@type": "WebPage",
        "@id": URL + "#webpage", "url": URL,
        "name": "Publicly reported China sourcing case references",
        "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
        "inLanguage": "en", "lastReviewed": REVIEW_DATE,
        "reviewedBy": {"@type": "Organization", "name": "Anchormere sourcing desk", "url": SITE},
        "publisher": {"@id": ORG_ID},
    }, ensure_ascii=False)

    serp_t = "Sourcing Case References | China+1 & HTS Cases"
    serp_d = ("Publicly reported China sourcing cases — Shein's Vietnam reversal, QIMA inspection "
              "data, CBP HTS rulings — each with its full source URL.")
    kw = ("China sourcing case study, China+1 case study, HTS classification ruling, "
          "country of origin e-bike, landed cost examples, OEM supply chain cases")

    toc = " · ".join(
        f'<a href="#{esc(g["id"])}">{esc(g["en"])}</a>' for g in groups
        if any(c["group"] == g["id"] for c in cases))

    doc = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(serp_t)}</title>
<meta name="title-zh" content="公开采购案例参考 · 附完整来源">
<meta name="description" content="{esc(serp_d)}">
<meta name="desc-zh" content="公开报道的中国采购、关税归类与订单回流案例，逐条保留完整来源网址，供核验与参考。">
<meta name="keywords" content="{esc(kw)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{URL}">
<link rel="alternate" hreflang="en" href="{URL}">
<link rel="alternate" hreflang="x-default" href="{URL}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Anchormere">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{esc(serp_t)}">
<meta property="og:description" content="{esc(serp_d)}">
<meta property="og:url" content="{URL}">
<meta property="og:image" content="{SITE}/assets/img/warehouse.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(serp_t)}">
<meta name="twitter:description" content="{esc(serp_d)}">
<meta name="twitter:image" content="{SITE}/assets/img/warehouse.jpg">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/consent.css">
<script defer src="assets/consent.js"></script>
<script type="application/ld+json">{org}</script>
<script type="application/ld+json">{website}</script>
<script type="application/ld+json">{bc}</script>
<script type="application/ld+json">{collection}</script>
<script type="application/ld+json">{faq}</script>
<script type="application/ld+json">{webpage}</script>
</head><body>
{longtail.NAV}
<main>
<section class="l1"><div class="container">
  <div class="eyebrow" data-zh="采购情报 · 公开案例参考">Sourcing intelligence &middot; public case references</div>
  <h1 data-zh="公开报道的采购案例，以及对你的询价意味着什么">Publicly reported sourcing cases — and what they mean for your RFQ</h1>
  <p class="lead" data-zh="下面每一条都来自公开报道、监管机构裁定或上市公司披露，并附完整来源网址明文。我们保留原文事实与出处，只补充一段采购启示，方便你在做落地成本、归类、原产地与验厂决策时对照。">{esc(disc["en"])}</p>
  <p class="cn" lang="zh-CN">{esc(disc["zh"])}</p>
  <div class="callout"><b data-zh="口径说明：">Editorial note: </b><span data-zh="本站不把这些案例表述为自己的客户、合作或供应关系；案例中的公司、品牌与商标归各自所有者所有。">None of these cases is presented as an Anchormere client, partner or supplier relationship. All company names and trademarks belong to their respective owners.</span></div>
  <p class="toc">{toc}</p>
  <p class="rel-note" data-zh="共 {len(cases)} 条 · 最后更新 {REVIEW_DATE} · 由 Anchormere 采购工程组复核">{len(cases)} cases &middot; last updated {REVIEW_DATE} &middot; reviewed by the Anchormere sourcing desk</p>
</div></section>
{sections_html}
<section class="l2"><div class="container">
  <h2 data-zh="关于这些案例的常见问题">Questions about these case references</h2>
  <p class="cn" lang="zh-CN">关于这些案例的常见问题</p>
  <div class="qa">
    <h3 data-zh="这些是 Anchormere 的客户案例吗？">Are these Anchormere client projects?</h3>
    <p data-zh="不是。所有案例均来自公开报道、官方裁定或上市公司披露，仅作行业参考，不代表 Anchormere 的客户、合作伙伴或背书关系。">No. Every case is drawn from public reporting, an official ruling or a public company filing. They are industry references, not Anchormere clients, partners or endorsements.</p>
    <h3 data-zh="为什么每条都写明完整来源网址？">Why does every case show a full source URL?</h3>
    <p data-zh="为了让买家与 AI 答案引擎都能回到原始出处核验事实。我们不会把别人的项目写成自己的业绩。">So buyers and answer engines can verify the facts at the original source. We do not claim another company's project as our own work.</p>
    <h3 data-zh="怎么把这些案例用到我的询价上？">How do I apply these cases to my own RFQ?</h3>
    <p data-zh="把它们当作落地成本建模、HTS 归类、原产地分析与供应商审核的检查清单。发一张照片或一个料号，工程师 48 小时内回复。">Use them as prompts for landed-cost modelling, HTS classification, country-of-origin analysis and supplier audits. Send a photo or a part number and an engineer replies within 48 hours.</p>
  </div>
</div></section>
<section class="dark"><div class="container" style="text-align:center">
  <div class="eyebrow" style="color:var(--brass)" data-zh="下一步">Next step</div>
  <h2 style="color:#fff" data-zh="把别人的经验，变成你自己的落地成本表">Turn public cases into your own landed-cost sheet</h2>
  <p class="cn" lang="zh-CN">把别人的经验，变成你自己的落地成本表</p>
  <p style="color:var(--on-dark2);max-width:640px;margin:14px auto 0" data-zh="告诉我们目标市场、产品类别与料号，我们会在报价前书面确认归类、所需单证、成本与交期。">Tell us the destination market, product category and part number — we confirm classification, documents, cost and lead time in writing before quoting.</p>
  <p style="margin-top:16px"><a class="btn-primary" href="contact.html" data-zh="获取报价">Get a Quote</a> <a class="btn-ghost" href="china-landed-cost-2026.html" data-zh="查看落地成本指南">Landed cost guide →</a></p>
</div></section>
</main>
{longtail.FOOTER}
<a class="wa-float" href="https://wa.me/8619068984158" data-zh="💬 WhatsApp 咨询">💬 WhatsApp</a>
<script defer src="assets/lang.js"></script>
</body></html>'''
    return doc


def main():
    if not io_util.selected(HUB_SLUG + ".html"):
        print("  (skipped by workarea selection)")
        return
    p = os.path.join(ROOT, HUB_SLUG + ".html")
    io_util.write_final(p, build())
    print("  ✓", HUB_SLUG)


if __name__ == "__main__":
    main()
