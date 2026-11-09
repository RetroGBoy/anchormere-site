#!/usr/bin/env python3
"""Generate long-tail product landing pages from scripts/longtail_seeds.json.
Each page is a substantive, bilingual (EN/中文) landing page targeting a high-intent
procurement keyword, with internal links, a one-click quote CTA and full SEO/JSON-LD.
Pure standard library; run manually or wire into the nightly workflow."""
import os, json, html
import os as _wa_os, sys as _wa_sys
_wa_sys.path.insert(0, _wa_os.path.dirname(_wa_os.path.abspath(__file__)))
import io_util  # workarea: write_if_changed / selected

ORG_LD = open(os.path.join(os.path.dirname(__file__), "org_entity.json"), encoding="utf-8").read().strip()

# Per-page substantive depth content (single source of truth). Loaded once at
# import time; missing entries are tolerated so a newly added seed never breaks
# the generator (the verifier's 3g gate will catch the gap instead).
_DEPTH_PATH = os.path.join(os.path.dirname(__file__), "longtail_depth.json")
DEPTH = json.load(open(_DEPTH_PATH, encoding="utf-8")) if os.path.exists(_DEPTH_PATH) else {"clusters": {}, "pages": {}}
ORG_ID = json.loads(ORG_LD)["@id"]   # 全站唯一 Organization @id，供 service.provider 串联

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://anchormere.com"

NAV = ('<nav class="mainnav"><div class="container">'
       '<div class="brand" data-zh="Anchormere <small>锚泊 · 中国采购合作伙伴</small>">Anchormere <small>锚泊 · 中国采购合作伙伴</small></div>'
       '<a class="nav" href="index.html" data-zh="首页">Home</a>'
       '<a class="nav" href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a>'
       '<a class="nav" href="cable-management.html" data-zh="线缆管理">Cable Mgmt</a>'
       '<a class="nav" href="consumer-smart-electronics.html" data-zh="消费与智能电子">Consumer</a>'
       '<a class="nav" href="smart-toys-devices.html" data-zh="智能玩具与设备">Toys &amp; Devices</a>'
       '<a class="nav" href="capabilities.html" data-zh="供应能力">Capabilities</a>'
       '<a class="nav" href="certifications.html" data-zh="认证说明">Certifications</a>'
       '<a class="nav" href="about.html" data-zh="关于我们">About</a> <a class="nav" href="faq.html" data-zh="常见问题">FAQ</a>'
       '<a class="nav" href="supply-base.html" data-zh="供应基地">Supply Base</a>'
       '<a class="nav" href="news.html" data-zh="资讯动态">News</a>'
       '<a class="btn-quote" href="contact.html" data-zh="获取报价">Get a Quote</a></div></nav>')

FOOTER = ('<footer><div class="container"><div class="cols">'
          '<div><h4 data-zh="Anchormere 锚泊 · 中国采购合作伙伴">Anchormere 锚泊 · 中国采购合作伙伴</h4>'
          '<ul><li data-zh="中国采购合作伙伴 · OEM · 采购 · 联合制造 · 大湾区">China sourcing partner · OEM · sourcing · joint manufacturing · Greater Bay Area</li>'
          '<li data-zh="中国 · 大湾区">Greater Bay Area, China</li><li>中国广东深圳市光明区特发工业园B座</li></ul></div>'
          '<div><h4 data-zh="产品">Products</h4><ul>'
          '<li><a href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a></li>'
          '<li><a href="cable-management.html" data-zh="线缆管理">Cable Management</a></li>'
          '<li><a href="consumer-smart-electronics.html" data-zh="消费与智能电子">Consumer &amp; Smart Electronics</a></li>'
          '<li><a href="smart-toys-devices.html" data-zh="智能玩具与设备">Smart Toys &amp; Devices</a></li>'
          '<li><a href="supply-base.html" data-zh="供应基地">Supply Base</a></li>'
          '<li><a href="marketplaces.html" data-zh="全球平台">Global Platforms</a></li>'
          '<li><a href="oem-vs-odm.html" data-zh="OEM 与 ODM">OEM vs ODM</a></li>'
          '<li><a href="how-to-find-manufacturer-china.html" data-zh="找工厂指南">Find a Factory</a></li></ul></div>'
          '<div><h4 data-zh="公司">Company</h4><ul>'
          '<li><a href="about.html" data-zh="关于我们">About</a></li><li><a href="capabilities.html" data-zh="供应能力">Capabilities</a></li>'
          '<li><a href="certifications.html" data-zh="认证说明">Certifications</a></li><li><a href="faq.html" data-zh="常见问题">FAQ</a></li>'
          '<li><a href="process.html" data-zh="合作流程">Process</a></li><li><a href="quality.html" data-zh="品质管控">Quality</a></li>'
          '<li><a href="shipping.html" data-zh="包装物流">Shipping</a></li></ul></div>'
          '<div><h4 data-zh="法律">Legal</h4><ul>'
          '<li data-zh="运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）">Operator: 深圳森亚实业有限公司 (Shenzhen Senya Industrial Co., Ltd.)</li>'
          '<li data-zh="商标：Anchormere / Buyeex">Trade mark: Anchormere / Buyeex</li></ul></div>'
          '</div><p style="margin-top:20px;text-align:center;color:var(--on-dark2)" data-zh="© 2026 Anchormere · 由深圳森亚实业有限公司运营">© 2026 Anchormere · Operated by 深圳森亚实业有限公司</p>'
          '<p style="margin-top:6px;text-align:center;color:var(--on-dark2);font-size:12px;opacity:.75" data-zh="最后更新：2026-11-07">Last updated: 2026-11-07</p></div>'
          '<p style="text-align:center;margin-top:10px;font-size:12px"><a href="privacy.html" data-zh="隐私政策">Privacy Policy</a> · <a href="terms.html" data-zh="服务条款">Terms &amp; Conditions</a></p></footer>')

FAQS = [
    ("What is the minimum order quantity (MOQ)?",
     "500 pcs per item. Mixed-SKU consolidation across one shipment is allowed."),
    ("How fast is the quote?",
     "Standard items are quoted within 48 hours by an engineer, with lead time and Incoterms stated up front."),
    ("How can I verify the factory remotely?",
     "By-process photo gallery, recorded shop-floor video, a certificate & document wall, and live inspection by appointment."),
    ("What are the payment terms?",
     "T/T to Shenzhen Senya Industrial Co., Ltd.: 30% deposit to start, 70% before shipment (ship after full payment)."),
    ("Do you handle finished or powered devices?",
     "Yes. We integrate assembled electronics and PCBA, and consolidate finished devices into one shipment with a full export document package."),
]

GA4 = ('<!-- GA4 is loaded consent-gated via assets/consent.js (set GA4_ID there) -->')

# Date of the most recent editorial/engineering review. Surfaced as visible
# text AND WebPage.lastReviewed so the E-E-A-T signal is policy-compliant
# (structured data must match on-page content).
REVIEW_DATE = "2026-11-09"

# ---- Publicly reported case references (single source of truth) -------------
# Real, verifiable cases from Reuters / QIMA / U.S. CBP / public filings, each
# carrying its full source URL in plain text. Rendered into the case-sharing
# block of the long-tail pages whose slug is listed in the data file.
# Industry references only — never presented as Anchormere client projects.
_CASE_DATA = json.load(open(os.path.join(os.path.dirname(__file__), "case_references.json"), encoding="utf-8"))
CASE_BY_SLUG = {}
for _c in _CASE_DATA["cases"]:
    for _sl in _c["slugs"]:
        CASE_BY_SLUG.setdefault(_sl, []).append(_c)
CASE_HUB_SLUG = _CASE_DATA["hub_slug"]
CASE_TOTAL = len(_CASE_DATA["cases"])


# --- SERP display-layer constraints (Google: title ~60 / description ~155 display chars) ---
# Only <title>/meta/og/twitter are clipped. The on-page <h1>, lead paragraph,
# BreadcrumbList and Service.name keep the FULL keyword-rich text, so topical
# coverage and conversion content are never weakened by this display optimization.
def clip_title(t, limit=60):
    t = html.unescape(t)
    if len(t) <= limit:
        return t
    cut = t[:limit]
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:-–—")


def clip_desc(d, limit=155):
    d = html.unescape(d)
    if len(d) <= limit:
        return d
    cut = d[:limit]
    # Prefer a sentence boundary if it is reasonably close, else word boundary.
    sentences = [m.end() for m in __import__("re").finditer(r"[.!?]\s", cut)]
    if sentences and sentences[-1] >= limit * 0.55:
        return cut[:sentences[-1]].strip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut.rstrip(" ,;:-–—")


def build_page(seed, all_seeds):
    slug = seed["slug"]
    url = SITE + "/" + slug
    en_t = seed["en_title"]
    zh_t = seed["zh_title"]
    en_lede = seed["en_lede"]
    zh_lede = seed["zh_lede"]
    kw = seed["kw"]
    # SERP display layer: prefer hand-tuned seed overrides, else auto-clip.
    # en_t / en_lede (full text) still drive h1, lead, BreadcrumbList, Service.name.
    serp_t = seed.get("serp_title") or clip_title(en_t)
    serp_d = seed.get("serp_desc") or clip_desc(en_lede)
    # Fold platform-sourced association terms into the meta keywords (LSI coverage).
    related_en = [en for en, zh in seed.get("related", [])]
    kw_full = (kw + ", " + ", ".join(related_en)) if related_en else kw
    rel = "".join(
        f'<span class="tag" data-zh="{html.escape(zh)}">{html.escape(en)}</span>'
        for en, zh in seed.get("related", []))
    mother_href, mother_label = seed["mother"]
    caps = "".join(
        f'<li><span data-zh="{html.escape(zh)}">{html.escape(en)}</span></li>' for en, zh in seed["caps"])
    # Case-sharing block: (1) leading brand names as market context (no supply
    # implication), (2) verifiable public cases with full source URLs.
    cases = seed.get("cases", [])
    if cases:
        cases_html = "".join(
            f'<div class="card"><div class="brand" data-zh="{html.escape(zh_b)}">{html.escape(en_b)}</div>'
            f'<p data-zh="{html.escape(zh_d)}">{html.escape(en_d)}</p></div>'
            for en_b, zh_b, en_d, zh_d in cases)
        brand_block = (f'  <div class="cases">{cases_html}</div>\n'
            '  <p class="rel-note" data-zh="以上品牌与型号仅作品类与市场需求参考，与本公司无关联、无合作或供应关系；商标归各自所有者所有。">The brands and models above are referenced only as category and market context. They are not affiliated with, endorsed by, or supplied by Anchormere; all trademarks belong to their respective owners.</p>\n')
        h2 = ('  <h2 data-zh="案例分享 · 品类与头部品牌参考">Case sharing &middot; categories &amp; leading brands</h2>\n'
              '  <p class="cn" lang="zh-CN">案例分享 · 品类与头部品牌参考（市场认知，非合作背书）</p>\n')
    else:
        brand_block = ""
        h2 = ('  <h2 data-zh="公开案例参考 · 附来源网址">Publicly reported case references &middot; with sources</h2>\n'
              '  <p class="cn" lang="zh-CN">公开案例参考 · 附来源网址</p>\n')

    refs = CASE_BY_SLUG.get(slug, [])[:2]
    if refs:
        li = []
        for c in refs:
            u = html.escape(c["source_url"], quote=True)
            li.append(
                '<li class="case-ref">'
                f'<b><a href="{u}" target="_blank" rel="noopener noreferrer">{html.escape(c["en_title"])}</a></b>'
                f'<span class="cn" lang="zh-CN">{html.escape(c["zh_title"])}</span>'
                f'<p>{html.escape(c["en_summary"])}</p>'
                f'<p class="cn" lang="zh-CN">{html.escape(c["zh_summary"])}</p>'
                f'<p class="takeaway"><b>Buyer takeaway &middot; 采购启示：</b>{html.escape(c["en_lesson"])}</p>'
                f'<p class="src">Source URL: <a href="{u}" target="_blank" rel="noopener noreferrer">{u}</a>'
                f' &middot; {html.escape(c["source"])} &middot; {html.escape(c["date"])}</p>'
                '</li>')
        ref_block = (
            '  <div class="case-refs">\n'
            '    <h3 data-zh="公开报道的真实案例（附来源网址）">Publicly reported cases (with source URLs)</h3>\n'
            '    <p class="cn" lang="zh-CN">公开报道的真实案例（附来源网址）</p>\n'
            f'    <ul>{"".join(li)}</ul>\n'
            '    <p class="rel-note" data-zh="以下案例引自公开报道、官方裁定或上市公司披露，仅作行业参考，并非 Anchormere 的客户项目、合作关系或背书；「采购启示」为本站对公开事实的解读。">These cases are drawn from public reporting, official rulings or public filings. They are industry references, NOT Anchormere client projects, partnerships or endorsements; the buyer takeaways are our interpretation of public facts.</p>\n'
            f'    <p class="all-cases"><a href="{CASE_HUB_SLUG}.html" data-zh="查看全部 {CASE_TOTAL} 条公开案例参考 →">View all {CASE_TOTAL} public case references →</a></p>\n'
            '  </div>\n')
    else:
        ref_block = ""

    if cases or refs:
        case_section = ('<section class="l2"><div class="container">\n'
                        + h2 + brand_block + ref_block + '</div></section>')
    else:
        case_section = ""
    specs = "".join(
        f'<tr><td>{html.escape(en_p)}</td>'
        f'<td data-zh="{html.escape(zh_v)}">{html.escape(en_v)}</td></tr>'
        for en_p, en_v, zh_v in seed["specs"])
    # Site-wide generic FAQ + platform-sourced buyer questions + category-specific
    # expertise FAQ (the latter makes each page's answer set genuinely distinct,
    # which is what AI answer engines actually quote).
    rel_qa = seed.get("related_qa", [])
    ex = seed.get("expertise", {})
    ex_faq = [(f[0], f[1], f[2], f[3]) for f in ex.get("faq", [])]
    all_qa = [(q, a, "", "") for q, a in FAQS + rel_qa] + ex_faq
    qa = "".join(
        f'<div class="qa"><h3 data-zh="{html.escape(qz, quote=True)}">{html.escape(q)}</h3>'
        f'<p data-zh="{html.escape(az, quote=True)}">{html.escape(a)}</p></div>'
        for q, a, qz, az in all_qa)
    faq = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                      "mainEntity": [{"@type": "Question", "name": q,
                                      "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a, _, _ in all_qa]},
                     ensure_ascii=False)
    # B2B 采购服务不是可标价零售商品：改用 Service 实体承载主题信号。
    # Google 产品摘要对 @type=Product 强制要求 offers / review / aggregateRating；
    # 本站为询价制、无固定价格与评价体系，虚构这些字段既违反 Search Essentials，
    # 又会把站点重新误归类为"电商/购物"（方案 A 要消除的正是这一点）。
    # 关键词仍保留在 name/description/serviceType；实体链经 provider @id 串联
    # 全站唯一 Organization，BreadcrumbList / FAQPage / WebPage 不受影响。
    prod = json.dumps({
        "@context": "https://schema.org", "@type": "Service", "name": en_t,
        "serviceType": "Greater Bay Area OEM sourcing",
        "provider": {"@id": ORG_ID},
        "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
        "description": seed["en_intro"]}, ensure_ascii=False)
    org = ORG_LD
    bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Products", "item": SITE + "/supply-base"},
        {"@type": "ListItem", "position": 3, "name": html.escape(en_t), "item": url}]}, ensure_ascii=False)

    # ---- Related sourcing topics: contextual internal links deepen subject<->keyword weight ----
    cl = seed.get("cluster")
    if cl == "knowledge":
        # Knowledge guides act as hubs → link to all capability (service) pages.
        rel_links = [s for s in all_seeds if s.get("cluster") == "capability"]
    else:
        rel_links = [s for s in all_seeds if s.get("cluster") == cl and s["slug"] != seed["slug"]]
        rel_links += [s for s in all_seeds if s.get("cluster") == "knowledge"]
    rel_links = rel_links[:8]
    rel_links_html = "".join(
        f'<a class="card rel-topic" href="{s["slug"]}.html" data-zh="{html.escape(s["zh_title"], quote=True)}">{html.escape(s["en_title"])}</a>'
        for s in rel_links)
    related_section = ('<section class="l2"><div class="container">\n'
        '  <h2 data-zh="相关采购主题">Related sourcing topics</h2>\n'
        '  <p class="cn">相关采购主题 · 同主体下更多长尾专题</p>\n'
        f'  <div class="rel-topics">{rel_links_html}</div>\n'
        '</div></section>')

    # ---- Buyer's guides by role: stable, deterministic internal links that guide
    #      every long-tail reader toward the buyer-persona enhancement pages
    #      (Amazon sellers, procurement agents, importers, hardware startups,
    #      factory verification). NOT subject to the [:8] cluster rotation, so each
    #      persona page always receives full link equity from the whole cluster. ----
    bg = [s for s in all_seeds if s.get("buyer_guide") and s["slug"] != slug]
    bg_html = "".join(
        f'<a class="card rel-topic" href="{s["slug"]}.html" data-zh="{html.escape(s["zh_title"], quote=True)}">{html.escape(s["en_title"])}</a>'
        for s in bg)
    buyer_guide_section = ('<section class="l2"><div class="container">\n'
        '  <h2 data-zh="按你的采购场景选指南">Guides for your buying scenario</h2>\n'
        '  <p class="cn">按你的采购场景选指南 · 同主体下的买家攻略</p>\n'
        '  <p class="lead" data-zh="无论你是以品牌卖家、采购代理、进口商、硬件创业者还是风控买家的身份来到这里，下面这些针对具体买家角色的专题，都能把你的需求落到可执行步骤。">Whether you arrived as a brand seller, procurement agent, importer, hardware founder or a risk-conscious buyer, these role-specific guides turn your intent into concrete next steps.</p>\n'
        f'  <div class="rel-topics">{bg_html}</div>\n'
        '</div></section>')

    website = json.dumps({
        "@context": "https://schema.org", "@type": "WebSite",
        "name": "Anchormere", "url": SITE, "inLanguage": ["en", "zh"],
        "publisher": {"@type": "Organization", "name": "Anchormere", "url": SITE},
        "about": {"@type": "Organization", "name": "Anchormere", "url": SITE},
        "potentialAction": {"@type": "SearchAction",
            "target": {"@type": "EntryPoint",
                       "urlTemplate": "https://www.google.com/search?q=site:anchormere.com+{search_term_string}"},
            "query-input": "required name=search_term_string"}}, ensure_ascii=False)

    # ---- Category-specific expertise: the substantive, non-templated part of
    #      every page. ~10 unique bilingual statements per page, none shared with
    #      other pages -> removes the "scaled content" pattern while keeping all
    #      keywords, h1, CTAs and the conversion path untouched. ----
    ex = seed.get("expertise", {})
    if ex:
        is_service = cl in ("capability", "knowledge")
        if is_service:
            h2_en, h2_zh = "How the engagement works", "合作如何推进"
            h3s = [("What we do, step by step", "我们逐步做什么"),
                   ("What to prepare as a buyer", "买家需要准备什么"),
                   ("How we verify &amp; report", "我们如何核验与留档")]
        else:
            h2_en, h2_zh = "Engineering &amp; sourcing notes", "工程与采购要点"
            h3s = [("Process &amp; technical notes", "工艺与技术要点"),
                   ("Buyer checklist", "买家核对清单"),
                   ("QC &amp; inspection focus", "质检与验厂重点")]

        def li_rows(rows):
            return "".join(
                f'<li><span data-zh="{html.escape(zh, quote=True)}">{html.escape(en)}</span></li>'
                for en, zh in rows)

        expertise_section = (
            '<section class="l2"><div class="container">\n'
            f'  <h2 data-zh="{h2_zh}">{h2_en}</h2>\n'
            f'  <p class="cn">{h2_zh}</p>\n'
            f'  <p class="lead" data-zh="{html.escape(ex.get("zh_intro", ""), quote=True)}">{html.escape(ex.get("en_intro", ""))}</p>\n'
            f'  <h3 data-zh="{h3s[0][1]}">{h3s[0][0]}</h3><ul class="check">{li_rows(ex.get("process", []))}</ul>\n'
            f'  <h3 data-zh="{h3s[1][1]}">{h3s[1][0]}</h3><ul class="check">{li_rows(ex.get("buyer", []))}</ul>\n'
            f'  <h3 data-zh="{h3s[2][1]}">{h3s[2][0]}</h3><ul class="check">{li_rows(ex.get("qc", []))}</ul>\n'
            f'  <p class="rel-note" data-zh="本页工程要点由 Anchormere 采购工程组于 {REVIEW_DATE} 复核，反映大湾区供应基地与当期适用标准；具体规格以询价时按贵方图纸确认的版本为准。">'
            f'Reviewed by the Anchormere sourcing desk on {REVIEW_DATE}. These notes reflect the Greater Bay Area supplier base and the standards current at review; specifications are confirmed against your drawing at RFQ.</p>\n'
            '</div></section>')
    else:
        expertise_section = ""

    # ---- Category-specific depth: the E-E-A-T core of each page --------------
    # Rendered from longtail_depth.json. Every statement in this block is unique
    # to this page (not a keyword-substituted template), which is what removes
    # the "scaled content" pattern. Standards are cited as PUBLIC references for
    # the buyer to verify with their supplier — never as certifications we hold.
    dp = DEPTH.get("pages", {}).get(slug)
    depth_section = ""
    depth_citations = []
    if dp:
        cl_meta = DEPTH.get("clusters", {}).get(dp.get("cluster"), {})
        # Page-level heading: 36 distinct h2 values, so no two long-tail pages
        # share the same section skeleton. Falls back to the cluster heading only
        # if a newly added seed has no depth entry yet (verifier 3g catches it).
        page_h2 = dp.get("h2") or [cl_meta.get("h2", "Engineering & sourcing depth"),
                                  cl_meta.get("zh", "工程与采购深度要点")]
        h2_en, h2_zh = page_h2[0], page_h2[1]
        term_rows = "".join(
            f'<tr><td><b>{html.escape(t_en)}</b><br><span class="cn" lang="zh-CN">{html.escape(t_zh)}</span></td>'
            f'<td data-zh="{html.escape(t_zhd, quote=True)}">{html.escape(t_end)}<br>'
            f'<span class="cn" lang="zh-CN">{html.escape(t_zhd)}</span></td></tr>'
            for t_en, t_end, t_zh, t_zhd in dp.get("terms", []))
        note_rows = "".join(
            f'<li><span data-zh="{html.escape(zh, quote=True)}">{html.escape(en)}</span></li>'
            for en, zh in dp["notes"])
        std_rows = "".join(
            f'<tr><td>{html.escape(code)}</td><td>{html.escape(scope)}</td></tr>'
            for code, scope in dp["standards"])
        depth_citations = [code for code, _ in dp["standards"]]
        scen_en, scen_zh = dp["scenario"]
        chk_en, chk_zh = dp["checklist"]
        depth_section = (
            '<section class="l2 depth"><div class="container">\n'
            f'  <h2 data-zh="{html.escape(h2_zh, quote=True)}">{html.escape(h2_en)}</h2>\n'
            f'  <p class="cn">{html.escape(h2_zh)}</p>\n'
            '  <p class="lead" data-zh="以下要点按品类整理自公开的工程规范与买家常见失效模式；规格数字为行业典型区间，最终以贵方图纸、目标市场与询价确认的版本为准。">These notes are compiled per category from public engineering standards and the failure modes buyers most often meet. Figures are typical industry ranges; the binding version is the one confirmed against your drawing, target market and RFQ.</p>\n'
            f'  <ul class="check depth-notes">{note_rows}</ul>\n'
            f'  <h3 data-zh="报价阶段的一个真实取舍">A real trade-off at RFQ stage</h3>\n'
            f'  <p class="depth-scenario" data-zh="{html.escape(scen_zh, quote=True)}">{html.escape(scen_en)}</p>\n'
            f'  <h3 data-zh="可核验的公开标准 / 规范（编辑性引用）">Public standards you can verify (editorial references)</h3>\n'
            '  <table class="spec-table depth-standards"><thead><tr><th data-zh="标准 / 规范">Standard / reference</th><th data-zh="适用范围（供买方核对）">Scope (for buyer verification)</th></tr></thead>'
            f'    <tbody>{std_rows}</tbody></table>\n'
            '  <p class="rel-note" data-zh="以上为公开标准与规范的编辑性引用，供买方要求供应商提供相应证据；Anchormere 不主张持有其中任何认证，也不代表原标准机构。内容产出与核验方式见编辑标准页。">These are editorial references to public standards, listed so buyers can ask their supplier for the matching evidence. Anchormere does not claim to hold any of these certifications and does not represent the issuing bodies. How we produce and verify content is documented on our <a href="editorial-standards.html" data-zh="编辑与核验标准">editorial standards</a> page.</p>\n'
            f'  <h3 data-zh="本页品类术语">Category terms used on this page</h3>\n'
            '  <table class="spec-table depth-terms"><thead><tr><th data-zh="术语">Term</th><th data-zh="含义（本站口径）">Meaning (as used here)</th></tr></thead>'
            f'    <tbody>{term_rows}</tbody></table>\n'
            f'  <h3 data-zh="下单前值得做的一项核验">One check worth running before you commit</h3>\n'
            f'  <p class="depth-check" data-zh="{html.escape(chk_zh, quote=True)}">{html.escape(chk_en)}</p>\n'
            '</div></section>')
        defined_terms = json.dumps({
            "@context": "https://schema.org", "@type": "DefinedTermSet",
            "name": h2_en, "url": url + "#terms",
            "inLanguage": "en",
            "hasDefinedTerm": [
                {"@type": "DefinedTerm", "name": t[0],
                 "description": t[1], "inDefinedTermSet": url + "#terms"}
                for t in dp.get("terms", [])]}, ensure_ascii=False)
    else:
        defined_terms = ""

    # E-E-A-T: an explicit, visible review statement mirrored in structured data.
    # lastReviewed + reviewedBy are valid WebPage properties (no invented author
    # or founding date, no fabricated sameAs links).
    webpage = json.dumps({
        "@context": "https://schema.org", "@type": "WebPage",
        "@id": url + "#webpage", "url": url, "name": en_t,
        "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
        "inLanguage": "en", "lastReviewed": REVIEW_DATE, "dateModified": REVIEW_DATE,
        "reviewedBy": {"@type": "Organization", "name": "Anchormere sourcing desk",
                       "url": SITE,
                       "description": "In-house sourcing engineering desk; reviews technical notes, standards scope and typical-value disclaimers."},
        "publisher": {"@type": "Organization", "name": "Anchormere", "url": SITE},
        "about": {"@type": "Thing", "name": en_t},
        "citation": [{"@type": "CreativeWork", "name": c} for c in depth_citations],
        "isBasedOn": {"@type": "WebPage", "url": SITE + "/editorial-standards"},
    }, ensure_ascii=False)

    ld_terms_block = (f'<script type="application/ld+json">{defined_terms}</script>'
                      if defined_terms else "")

    doc = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(serp_t)}</title>
<meta name="title-zh" content="{html.escape(zh_t)}">
<meta name="description" content="{html.escape(serp_d)}">
<meta name="desc-zh" content="{html.escape(zh_lede)}">
<meta name="keywords" content="{html.escape(kw_full)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Anchormere">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{html.escape(serp_t)}">
<meta property="og:description" content="{html.escape(serp_d)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/img/warehouse.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(serp_t)}">
<meta name="twitter:description" content="{html.escape(serp_d)}">
<meta name="twitter:image" content="{SITE}/assets/img/warehouse.jpg">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/consent.css">
<script defer src="assets/consent.js"></script>
<script type="application/ld+json">{org}</script>
<script type="application/ld+json">{website}</script>
<script type="application/ld+json">{bc}</script>
<script type="application/ld+json">{faq}</script>
<script type="application/ld+json">{prod}</script>
<script type="application/ld+json">{webpage}</script>
{ld_terms_block}
</head><body>
<div class="topbar"><span data-zh="⚓ <b>48 小时报价</b>">⚓ <b>48h quote</b></span><span data-zh="🏭 <b>20+ 家认证工厂</b>">🏭 <b>20+ vetted factories</b></span><span data-zh="📦 <b>500 件起订</b>">📦 <b>500 pcs MOQ</b></span><span data-zh="📑 <b>完整出口单证</b>">📑 <b>Full export docs</b></span></div>
{NAV}
<section class="l1"><div class="container">
  <div class="crumb"><a href="index.html" data-zh="首页">Home</a> / <a href="supply-base.html" data-zh="供应基地">Products</a> / <span>{html.escape(en_t)}</span></div>
  <div class="eyebrow" data-zh="大湾区 OEM 采购">Greater Bay Area OEM sourcing</div>
  <h1 data-zh="{html.escape(zh_t)}">{html.escape(en_t)}</h1>
  <p class="lead" data-zh="{html.escape(zh_lede)}">{html.escape(en_lede)}</p>
  <p class="cn">{html.escape(zh_lede)}</p>
</div></section>
<section class="l2"><div class="container">
  <h2 data-zh="为什么在大湾区做">Why build it in the Greater Bay Area</h2>
  <p class="cn">为什么在大湾区做</p>
  <p class="lead" data-zh="{html.escape(zh_intro := seed['zh_intro'])}">{html.escape(seed['en_intro'])}</p>
</div></section>
<section class="l1"><div class="container">
  <h2 data-zh="我们能整合的能力">What we integrate</h2>
  <p class="cn">我们能整合的能力</p>
  <ul class="check">{caps}</ul>
</div></section>
{case_section}
<section class="l2"><div class="container">
  <h2 data-zh="典型规格与时效">Typical specs &amp; lead times</h2>
  <p class="cn">典型规格与时效</p>
  <table class="spec-table"><thead><tr><th data-zh="项目">Parameter</th><th data-zh="说明">Detail</th></tr></thead><tbody>{specs}</tbody></table>
</div></section>
{expertise_section}
{depth_section}
<section class="l1"><div class="container">
  <h2 data-zh="常见问题">FAQ</h2>
  <p class="cn">常见问题</p>
  <div class="faq">{qa}</div>
</div></section>
<section class="l2"><div class="container">
  <h2 data-zh="跨平台关联检索词">Related searches across platforms</h2>
  <p class="cn">跨平台关联检索词 · Google / Bing / Baidu / 1688 / Alibaba / Amazon</p>
  <div class="tags">{rel}</div>
  <p class="rel-note" data-zh="以上为买家在海外搜索引擎与 B2B 平台（Google、Bing、百度、1688、Alibaba、Amazon、Made-in-China）实际使用的关联检索词，已整合进本页以提升相关性与收录覆盖。">These are the association terms buyers actually type across search engines and B2B platforms (Google, Bing, Baidu, 1688, Alibaba, Amazon, Made-in-China) — folded into this page to broaden relevance and indexing coverage.</p>
</div></section>
{related_section}
{buyer_guide_section}
<section class="dark"><div class="container" style="text-align:center">
  <div class="eyebrow" style="color:var(--brass)" data-zh="下一步">Next step</div>
  <h2 style="color:#fff" data-zh="发一张照片或一个料号，48 小时内工程师回复">Send a photo or a part number — an engineer replies within 48h</h2>
  <p class="cn">发一张照片或一个料号，48 小时内工程师回复</p>
  <p style="color:var(--on-dark2);max-width:620px;margin:14px auto 0" data-zh="或先回到母品类页，看清我们能整合的全部范围。">Or return to the parent category page to see the full scope we integrate.</p>
  <p style="margin-top:16px"><a class="btn-primary" href="contact.html" data-zh="获取报价">Get a Quote</a> <a class="btn-ghost" href="{mother_href}" data-zh="查看母品类">{html.escape(mother_label)} →</a></p>
</div></section>
{FOOTER}
<a class="wa-float" href="https://wa.me/8619068984158" data-zh="💬 WhatsApp 咨询">💬 WhatsApp</a>
<script defer src="assets/lang.js"></script>
</body></html>"""
    return doc


def main():
    seeds = json.load(open(os.path.join(ROOT, "scripts", "longtail_seeds.json"), encoding="utf-8"))
    n = 0
    for s in seeds:
        if not io_util.selected(s["slug"] + ".html"):
            continue
        p = os.path.join(ROOT, s["slug"] + ".html")
        io_util.write_final(p, build_page(s, seeds))
        n += 1
        print("  ✓", s["slug"])
    print(f"generated {n} long-tail pages")


if __name__ == "__main__":
    main()
