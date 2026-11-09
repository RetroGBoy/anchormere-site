#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the editorial standards / content-verification page.

This is the site's E-E-A-T trust hub. It documents, in plain language and in
structured data, how Anchormere's sourcing content is produced and checked:

  * who writes and reviews it (Experience / Expertise),
  * what evidence we cite and how (Authoritativeness),
  * what we deliberately do NOT claim (Trust),
  * how typical values, public standards and corrections are handled.

Everything stated here is verifiable on this site — no external credentials,
no client list, no certification claims, no invented author biographies. That
constraint is deliberate: the user has decided not to supply company
certifications or external profile URLs, so the trust signal must be built
from disclosure and provenance rather than from borrowed authority.

Design constraints (workarea incremental system):
  * single source of truth = longtail_depth.json for counts and standard policy
  * writes only through io_util.write_final -> html_finalize.normalize
  * honours io_util.selected() so the incremental plan controls scope
  * NAV / FOOTER / entities reused from longtail.py + org_entity.json
"""
import os, sys, json, html

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import io_util
import longtail

ROOT = longtail.ROOT
SITE = longtail.SITE
ORG_ID = longtail.ORG_ID
REVIEW_DATE = "2026-11-09"
SLUG = "editorial-standards"
URL = SITE + "/" + SLUG


def esc(s):
    return html.escape(str(s), quote=True)


def build():
    depth = json.load(open(os.path.join(_HERE, "longtail_depth.json"), encoding="utf-8"))
    cases = json.load(open(os.path.join(_HERE, "case_references.json"), encoding="utf-8"))
    page_n = len(depth["pages"])
    note_n = sum(len(v["notes"]) for v in depth["pages"].values())
    std_n = sum(len(v["standards"]) for v in depth["pages"].values())
    term_n = sum(len(v.get("terms", [])) for v in depth["pages"].values())
    case_n = len(cases["cases"])
    policy = depth["policy"]

    # ---- Evidence ledger: what the site actually contains, with numbers ----
    ledger = [
        ("Category-specific engineering notes", "品类专属工程笔记",
         f"{note_n} notes across {page_n} sourcing pages; every note is written for one category and is not repeated elsewhere.",
         f"{page_n} 个采购主题页共 {note_n} 条笔记，每条按品类单独撰写，不在其他页面重复。"),
        ("Decision scenarios", "报价决策场景",
         f"{page_n} worked RFQ trade-offs, each describing a real constraint conflict rather than a generic benefit statement.",
         f"{page_n} 个询价阶段的真实取舍算例，描述具体约束冲突，而非笼统的优势表述。"),
        ("Public standard references", "公开标准引用",
         f"{std_n} editorial citations (IEC, ISO, IPC, FCC/CE, Incoterms, HS/GRI) with their scope stated in plain language.",
         f"{std_n} 条编辑性引用（IEC / ISO / IPC / FCC-CE / Incoterms / HS-GRI），并写明适用范围。"),
        ("Category glossaries", "品类术语表",
         f"{term_n} defined terms rendered as DefinedTermSet structured data, so answer engines can resolve our terminology.",
         f"{term_n} 条术语以 DefinedTermSet 结构化数据标注，便于答案引擎解析本站用语。"),
        ("Public case references", "公开案例参考",
         f"{case_n} publicly reported cases, each with its full Source URL printed in plain text on the case hub and on the pages that cite it.",
         f"{case_n} 条公开报道案例，案例枢纽页与引用它的页面均印出完整 Source URL 明文。"),
        ("Review metadata", "复核元数据",
         f"A visible review line plus WebPage.lastReviewed / reviewedBy / dateModified on all {page_n} sourcing pages, kept in sync by the verifier.",
         f"全部 {page_n} 个采购主题页含可见复核署名，与 WebPage.lastReviewed / reviewedBy / dateModified 成对一致，由验证器校验。"),
    ]
    ledger_rows = "\n".join(
        f'<tr><td><b>{esc(k)}</b><br><span class="cn" lang="zh-CN">{esc(kz)}</span></td>'
        f'<td data-zh="{esc(vz)}">{esc(v)}<br><span class="cn" lang="zh-CN">{esc(vz)}</span></td></tr>'
        for k, kz, v, vz in ledger)

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
            {"@type": "ListItem", "position": 2, "name": "Editorial standards", "item": URL},
        ],
    }, ensure_ascii=False)
    webpage = json.dumps({
        "@context": "https://schema.org", "@type": "AboutPage",
        "@id": URL + "#webpage", "url": URL,
        "name": "Editorial standards & content verification",
        "description": "How Anchormere produces, sources, reviews and corrects its China sourcing content — including what it deliberately does not claim.",
        "isPartOf": {"@type": "WebSite", "name": "Anchormere", "url": SITE},
        "inLanguage": "en", "lastReviewed": REVIEW_DATE, "dateModified": REVIEW_DATE,
        "reviewedBy": {"@type": "Organization", "name": "Anchormere sourcing desk", "url": SITE},
        "publisher": {"@id": ORG_ID},
        "about": {"@id": ORG_ID},
    }, ensure_ascii=False)
    faq = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": "Who writes and reviews this content?",
             "acceptedAnswer": {"@type": "Answer", "text": "The Anchormere sourcing desk — an in-house sourcing engineering team — writes the category notes and reviews them against public standards, supplier processes and typical buyer RFQs. Each sourcing page carries a visible review date."}},
            {"@type": "Question", "name": "Do you hold the certifications you mention?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. Standards such as IEC, ISO, IPC, FCC, CE and Incoterms are cited as public references for buyers to verify with their chosen supplier. Anchormere does not claim to hold any certification and does not represent the issuing bodies."}},
            {"@type": "Question", "name": "Are the case studies your own clients?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. All public case references come from reporting, official rulings or public filings, and each carries its full source URL. They are industry references, not Anchormere clients, partners or endorsements."}},
            {"@type": "Question", "name": "Are the specifications and figures binding?",
             "acceptedAnswer": {"@type": "Answer", "text": "No. MOQ, lead times, tolerances, wattage and cost figures are typical industry ranges for orientation. The binding values are those confirmed in writing against your drawing, target market and RFQ."}},
            {"@type": "Question", "name": "How do I report an error or request a correction?",
             "acceptedAnswer": {"@type": "Answer", "text": "Use the contact form, quoting the page URL and the sentence in question. We review the claim against the cited source and either correct the page or explain why it stands."}},
        ],
    }, ensure_ascii=False)

    serp_t = "Editorial Standards | How We Verify Sourcing Content"
    serp_d = ("How Anchormere produces, sources, reviews and corrects its China sourcing content — "
              "public standards, source URLs, typical-value disclaimers and what we do not claim.")
    kw = ("editorial standards, content verification, sourcing content methodology, "
          "public standards references, E-E-A-T, typical value disclaimer, correction policy")

    doc = f'''<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(serp_t)}</title>
<meta name="title-zh" content="编辑与核验标准 · 内容如何产出">
<meta name="description" content="{esc(serp_d)}">
<meta name="desc-zh" content="Anchormere 采购内容如何产出、引用、复核与更正：公开标准、来源网址、典型值口径，以及我们明确不主张的事项。">
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
<script type="application/ld+json">{webpage}</script>
<script type="application/ld+json">{faq}</script>
</head><body>
{longtail.NAV}
<main>
<section class="l1"><div class="container">
  <div class="eyebrow" data-zh="编辑标准 · 内容核验">Editorial standards &middot; content verification</div>
  <h1 data-zh="这些内容是怎么来的，我们凭什么这么说">How this content is produced — and what we do not claim</h1>
  <p class="lead" data-zh="采购决策值得可核验的信息。这一页说明我们的内容由谁写、依据什么、谁复核、出现错误如何更正，以及我们明确不主张的东西——因为把不确定的说成确定，比信息不足更伤买家。">Sourcing decisions deserve checkable information. This page states who writes our content, what it is based on, who reviews it, how errors are corrected, and what we deliberately do not claim — because presenting the uncertain as certain hurts buyers more than an incomplete answer does.</p>
  <p class="cn" lang="zh-CN">采购决策值得可核验的信息。这一页说明内容由谁写、依据什么、谁复核、如何更正，以及我们明确不主张的事项。</p>
  <p class="rel-note" data-zh="最后更新 {REVIEW_DATE} · 由 Anchormere 采购工程组复核 · 适用范围：全站采购主题页面">Last updated {REVIEW_DATE} &middot; reviewed by the Anchormere sourcing desk &middot; scope: all sourcing-topic pages</p>
</div></section>

<section class="l2"><div class="container">
  <h2 data-zh="可核验的内容台账">What you can actually verify on this site</h2>
  <p class="cn" lang="zh-CN">可核验的内容台账</p>
  <p class="lead" data-zh="下表不是承诺，而是本站当前实际包含、且可以在页面上逐条点开核对的内容。数字化台账随数据源自动更新。">The table below is not a promise but a ledger of what the site currently contains and what you can open and check page by page. The counts are generated from our data sources, not hand-written.</p>
  <table class="spec-table"><thead><tr><th data-zh="类型">Asset</th><th data-zh="当前数量与说明">What is on the site</th></tr></thead>
  <tbody>{ledger_rows}</tbody></table>
</div></section>

<section class="l1"><div class="container">
  <h2 data-zh="四条编辑原则">Four editorial rules we hold to</h2>
  <p class="cn" lang="zh-CN">四条编辑原则</p>
  <ul class="check">
    <li><span data-zh="按品类写，不按关键词套：每个采购主题页的工程笔记、决策场景、术语与标准清单都是为该品类单独撰写的，不做主词替换。">Write per category, not per keyword: the engineering notes, decision scenario, glossary and standard list on each sourcing page are written for that category alone — not produced by swapping a head term.</span></li>
    <li><span data-zh="引用公开来源并保留出处：公开案例逐条印出完整 Source URL 明文；标准与规范只作编辑性引用，并写明适用范围。">Cite public sources and keep the trail: public cases print their full Source URL in plain text; standards are cited editorially with their scope stated.</span></li>
    <li><span data-zh="数字标明口径：MOQ、交期、公差、功率与成本均为行业典型区间，约束版本以图纸、目标市场与书面询价确认为准。">Label every number: MOQ, lead time, tolerance, wattage and cost figures are typical industry ranges; the binding version is confirmed against the drawing, target market and written RFQ.</span></li>
    <li><span data-zh="不冒领：不把公开案例写成客户项目，不主张持有任何认证，不编造评价、价格、客户名或团队履历。">Claim nothing borrowed: public cases are not our client projects, we claim no certification, and we invent no reviews, prices, customer names or staff biographies.</span></li>
  </ul>
</div></section>

<section class="l2"><div class="container">
  <h2 data-zh="我们明确不主张的事">What this site does not claim</h2>
  <p class="cn" lang="zh-CN">我们明确不主张的事</p>
  <p class="lead" data-zh="把边界写清楚，是让内容可信的一部分。以下均为当前事实，不是待补的占位。">Stating the boundary is part of being credible. The following are current facts, not placeholders waiting to be filled.</p>
  <ul class="check">
    <li><span data-zh="不主张持有 ISO、IEC、UL、CE、FCC 等任何认证；这些标准名只作为买方要求供应商提供证据时的公开依据。">We do not claim to hold ISO, IEC, UL, CE, FCC or any other certification. Those names appear only as public references a buyer can ask a supplier to evidence.</span></li>
    <li><span data-zh="不展示客户案例、合作伙伴名单或业绩背书；站内公开案例均来自公开报道，并保留完整来源网址。">We show no client portfolio, partner list or performance endorsement. Public cases come from reporting and keep their full source URLs.</span></li>
    <li><span data-zh="不提供公司资质文件，也不设预留板块或占位字段；主体信息以页面 footer 与 Organization 实体中已披露的内容为限。">We provide no company certification documents and maintain no reserved section or placeholder for them. Entity information is limited to what is already disclosed in the footer and the Organization entity.</span></li>
    <li><span data-zh="不虚构作者履历、团队成员姓名或外部机构链接；复核主体统一标注为 Anchormere sourcing desk。">We invent no author biographies, named staff or external profile links. The review body is disclosed uniformly as the Anchormere sourcing desk.</span></li>
  </ul>
  <p class="rel-note" data-zh="结构化数据同样遵守以上边界：本站不声明 Product / Offer / aggregateRating 等零售实体与评价，避免被误归类为电商商品页。">The same boundary applies to structured data: the site declares no Product / Offer / aggregateRating retail entities or ratings, so it is not misclassified as an e-commerce product page.</p>
</div></section>

<section class="l1"><div class="container">
  <h2 data-zh="更正与反馈">Corrections and feedback</h2>
  <p class="cn" lang="zh-CN">更正与反馈</p>
  <p class="lead" data-zh="如果你发现某条事实、标准适用范围或典型值与来源不符，请通过询盘表单附上页面网址与具体句子。我们会回到被引用的来源核对，然后更正页面，或说明为何维持原表述。">If a fact, standard scope or typical value does not match its source, send us the page URL and the exact sentence via the contact form. We check it against the cited source, then correct the page or explain why the wording stands.</p>
  <p class="lead" data-zh="本页与全站内容一起，由验证闸门在每次发布前检查：审核署名与结构化复核日期成对一致、案例来源 URL 明文、标准引用与免责声明、无零售实体误归类。">This page and the rest of the site are checked before every publish by verification gates: visible review lines paired with structured review dates, case source URLs in plain text, standard citations with disclaimers, and no retail-entity misclassification.</p>
</div></section>

<section class="l2"><div class="container">
  <h2 data-zh="常见问题">FAQ</h2>
  <p class="cn" lang="zh-CN">常见问题</p>
  <div class="qa">
    <h3 data-zh="这些内容由谁撰写与复核？">Who writes and reviews this content?</h3>
    <p data-zh="由 Anchormere 采购工程组（内部采购工程团队）撰写，并对照公开标准、供应商流程与买家常见询价复核；每个采购主题页都带可见的复核日期。">The Anchormere sourcing desk — an in-house sourcing engineering team — writes the category notes and reviews them against public standards, supplier processes and typical buyer RFQs. Each sourcing page carries a visible review date.</p>
    <h3 data-zh="你们持有页面提到的认证吗？">Do you hold the certifications you mention?</h3>
    <p data-zh="不持有。IEC、ISO、IPC、FCC、CE、Incoterms 等只作为公开参考，供买方要求供应商提供相应证据；Anchormere 不主张持有任何认证，也不代表发证机构。">No. Standards such as IEC, ISO, IPC, FCC, CE and Incoterms are cited as public references for buyers to verify with their chosen supplier. Anchormere claims no certification and represents no issuing body.</p>
    <h3 data-zh="案例研究是你们自己的客户吗？">Are the case studies your own clients?</h3>
    <p data-zh="不是。所有公开案例均来自公开报道、官方裁定或上市公司披露，并逐条保留完整来源网址；它们是行业参考，不是 Anchormere 的客户、合作伙伴或背书。">No. All public case references come from reporting, official rulings or public filings, each with its full source URL. They are industry references, not Anchormere clients, partners or endorsements.</p>
    <h3 data-zh="页面上的规格与数字有约束力吗？">Are the specifications and figures binding?</h3>
    <p data-zh="没有。MOQ、交期、公差、功率与成本均为行业典型区间，仅用于定向；有约束力的是按贵方图纸、目标市场与书面询价确认的数值。">No. MOQ, lead times, tolerances, wattage and cost figures are typical industry ranges for orientation. The binding values are those confirmed in writing against your drawing, target market and RFQ.</p>
    <h3 data-zh="如何报告错误或申请更正？">How do I report an error or request a correction?</h3>
    <p data-zh="通过询盘表单附上页面网址与具体句子。我们会对照被引用的来源复核，然后更正页面或说明维持原表述的理由。">Use the contact form, quoting the page URL and the sentence in question. We review the claim against the cited source and either correct the page or explain why it stands.</p>
  </div>
</div></section>

<section class="dark"><div class="container" style="text-align:center">
  <div class="eyebrow" style="color:var(--brass)" data-zh="下一步">Next step</div>
  <h2 style="color:#fff" data-zh="把可核验的信息，用在你自己的询价上">Put checkable information to work on your own RFQ</h2>
  <p class="cn" lang="zh-CN">把可核验的信息，用在你自己的询价上</p>
  <p style="color:var(--on-dark2);max-width:640px;margin:14px auto 0" data-zh="发一张照片或一个料号，工程师 48 小时内回复，并书面确认归类、所需单证、成本与交期。">Send a photo or a part number — an engineer replies within 48 hours and confirms classification, required documents, cost and lead time in writing.</p>
  <p style="margin-top:16px"><a class="btn-primary" href="contact.html" data-zh="获取报价">Get a Quote</a> <a class="btn-ghost" href="sourcing-case-studies.html" data-zh="查看公开案例参考">Public case references →</a></p>
</div></section>
</main>
{longtail.FOOTER}
<a class="wa-float" href="https://wa.me/8619068984158" data-zh="💬 WhatsApp 咨询">💬 WhatsApp</a>
<script defer src="assets/lang.js"></script>
</body></html>'''
    return doc


def main():
    if not io_util.selected(SLUG + ".html"):
        print("  (skipped by workarea selection)")
        return
    p = os.path.join(ROOT, SLUG + ".html")
    io_util.write_final(p, build())
    print("  ✓", SLUG)


if __name__ == "__main__":
    main()
