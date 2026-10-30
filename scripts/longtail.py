#!/usr/bin/env python3
"""Generate long-tail product landing pages from scripts/longtail_seeds.json.
Each page is a substantive, bilingual (EN/中文) landing page targeting a high-intent
procurement keyword, with internal links, a one-click quote CTA and full SEO/JSON-LD.
Pure standard library; run manually or wire into the nightly workflow."""
import os, json, html

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
          '<li><a href="supply-base.html" data-zh="供应基地">Supply Base</a></li></ul></div>'
          '<div><h4 data-zh="公司">Company</h4><ul>'
          '<li><a href="about.html" data-zh="关于我们">About</a></li><li><a href="capabilities.html" data-zh="供应能力">Capabilities</a></li>'
          '<li><a href="certifications.html" data-zh="认证说明">Certifications</a></li><li><a href="faq.html" data-zh="常见问题">FAQ</a></li>'
          '<li><a href="process.html" data-zh="合作流程">Process</a></li><li><a href="quality.html" data-zh="品质管控">Quality</a></li>'
          '<li><a href="shipping.html" data-zh="包装物流">Shipping</a></li></ul></div>'
          '<div><h4 data-zh="法律">Legal</h4><ul>'
          '<li data-zh="运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）">Operator: 深圳森亚实业有限公司 (Shenzhen Senya Industrial Co., Ltd.)</li>'
          '<li data-zh="商标：Anchormere / Buyeex">Trade mark: Anchormere / Buyeex</li></ul></div>'
          '</div><p style="margin-top:20px;text-align:center;color:var(--on-dark2)" data-zh="© 2026 Anchormere · 由深圳森亚实业有限公司运营">© 2026 Anchormere · Operated by 深圳森亚实业有限公司</p>'
          '<p style="margin-top:6px;text-align:center;color:var(--on-dark2);font-size:12px;opacity:.75" data-zh="最后更新：2026-10-30">Last updated: 2026-10-30</p></div>'
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


def build_page(seed):
    slug = seed["slug"]
    url = SITE + "/" + slug
    en_t = seed["en_title"]
    zh_t = seed["zh_title"]
    en_lede = seed["en_lede"]
    zh_lede = seed["zh_lede"]
    kw = seed["kw"]
    mother_href, mother_label = seed["mother"]
    caps = "".join(
        f'<li><span data-zh="{html.escape(zh)}">{html.escape(en)}</span></li>' for en, zh in seed["caps"])
    specs = "".join(
        f'<tr><td>{html.escape(en_p)}</td>'
        f'<td data-zh="{html.escape(zh_v)}">{html.escape(en_v)}</td></tr>'
        for en_p, en_v, zh_v in seed["specs"])
    qa = "".join(
        f'<div class="qa"><h3 data-zh="">{html.escape(q)}</h3>'
        f'<p data-zh="">{html.escape(a)}</p></div>' for q, a in FAQS)
    faq = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                      "mainEntity": [{"@type": "Question", "name": q,
                                      "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]},
                     ensure_ascii=False)
    prod = json.dumps({
        "@context": "https://schema.org", "@type": "Product", "name": en_t,
        "brand": {"@type": "Brand", "name": "Anchormere"},
        "description": seed["en_intro"], "category": "Greater Bay Area OEM sourcing",
        "offers": {"@type": "Offer", "priceCurrency": "USD",
                   "availability": "https://schema.org/InStock", "url": url,
                   "seller": {"@type": "Organization", "name": "Anchormere"}}}, ensure_ascii=False)
    org = json.dumps({"@context": "https://schema.org", "@type": "Organization", "name": "Anchormere",
                      "alternateName": "锚泊", "url": SITE, "email": "info@anchormere.com",
                      "address": {"@type": "PostalAddress", "addressRegion": "Guangdong", "addressCountry": "CN"},
                      "description": "China sourcing partner for the Greater Bay Area manufacturing base.",
                      "parentOrganization": {"@type": "Organization", "name": "深圳森亚实业有限公司"}}, ensure_ascii=False)
    bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
        {"@type": "ListItem", "position": 2, "name": "Products", "item": SITE + "/supply-base"},
        {"@type": "ListItem", "position": 3, "name": html.escape(en_t), "item": url}]}, ensure_ascii=False)

    doc = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(en_t)}</title>
<meta name="title-zh" content="{html.escape(zh_t)}">
<meta name="description" content="{html.escape(en_lede)}">
<meta name="desc-zh" content="{html.escape(zh_lede)}">
<meta name="keywords" content="{html.escape(kw)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<link rel="alternate" hreflang="en" href="{url}">
<link rel="alternate" hreflang="zh-CN" href="{url}">
<link rel="alternate" hreflang="x-default" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Anchormere">
<meta property="og:locale" content="en_US">
<meta property="og:title" content="{html.escape(en_t)}">
<meta property="og:description" content="{html.escape(en_lede)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/img/warehouse.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{html.escape(en_t)}">
<meta name="twitter:description" content="{html.escape(en_lede)}">
<meta name="twitter:image" content="{SITE}/assets/img/warehouse.jpg">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/consent.css">
<script defer src="assets/consent.js"></script>
<script type="application/ld+json">{org}</script>
<script type="application/ld+json">{bc}</script>
<script type="application/ld+json">{faq}</script>
<script type="application/ld+json">{prod}</script>
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
<section class="l2"><div class="container">
  <h2 data-zh="典型规格与时效">Typical specs &amp; lead times</h2>
  <p class="cn">典型规格与时效</p>
  <table class="spec-table"><thead><tr><th data-zh="项目">Parameter</th><th data-zh="说明">Detail</th></tr></thead><tbody>{specs}</tbody></table>
</div></section>
<section class="l1"><div class="container">
  <h2 data-zh="常见问题">FAQ</h2>
  <p class="cn">常见问题</p>
  <div class="faq">{qa}</div>
</div></section>
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
        p = os.path.join(ROOT, s["slug"] + ".html")
        with open(p, "w", encoding="utf-8") as f:
            f.write(build_page(s))
        n += 1
        print("  ✓", s["slug"])
    print(f"generated {n} long-tail pages")


if __name__ == "__main__":
    main()
