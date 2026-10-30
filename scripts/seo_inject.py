#!/usr/bin/env python3
"""SEO injection across the site (idempotent): static hreflang (en/zh-CN/x-default),
BreadcrumbList JSON-LD, Product JSON-LD on product pages, and new-category nav anchors."""
import os, re, json, html

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PRODUCT_PAGES = {"rack-accessories", "cable-management",
                 "consumer-smart-electronics", "smart-toys-devices", "supply-base"}
SITE = "https://anchormere.com"

CABLE_NAV = '<a class="nav" href="cable-management.html" data-zh="线缆管理">Cable Mgmt</a>'
NEW_NAV = ('<a class="nav" href="consumer-smart-electronics.html" data-zh="消费与智能电子">Consumer</a>'
           '<a class="nav" href="smart-toys-devices.html" data-zh="智能玩具与设备">Toys &amp; Devices</a>')

FAQ_PAGES = {"index.html"} | {p + ".html" for p in PRODUCT_PAGES}
FAQS = [
    ("What is the minimum order quantity (MOQ)?",
     "500 pcs per item. Mixed-SKU consolidation across one shipment is allowed, so smaller buyers can combine several products."),
    ("How fast is the quote?",
     "Standard items are quoted within 48 hours by an engineer, with lead time and Incoterms stated up front."),
    ("How can I verify the factory remotely?",
     "By-process photo gallery, recorded shop-floor video, a certificate & document wall, and live inspection by appointment — no blind trust required."),
    ("What are the payment terms?",
     "T/T to Shenzhen Senya Industrial Co., Ltd.: 30% deposit to start production, 70% before shipment (ship after full payment)."),
    ("Do you handle finished or powered devices?",
     "Yes. We integrate assembled electronics and PCBA, and consolidate finished devices into one shipment with a full export document package."),
]


def inject_head(c, fn):
    # Strip prior injections for idempotency + self-correction (do not cross </script>)
    NB = r'(?:(?!</script>).)*?'  # non-greedy, stays inside one script block
    c = re.sub(r'<link rel="alternate" hreflang="[^"]*" href="[^"]*">\n?', '', c)
    c = re.sub(r'<script type="application/ld\+json">' + NB + r'BreadcrumbList' + NB + r'</script>\n?', '', c, flags=re.S)
    c = re.sub(r'<script type="application/ld\+json">' + NB + r'"@type": "Product"' + NB + r'</script>\n?', '', c, flags=re.S)
    c = re.sub(r'<script type="application/ld\+json">' + NB + r'"@type": "FAQPage"' + NB + r'</script>\n?', '', c, flags=re.S)
    # Resolve canonical URL
    m = re.search(r'(?:<meta name="canonical"|<link rel="canonical") href="([^"]+)"', c)
    if m:
        url = m.group(1)
    elif fn == "index.html":
        url = SITE + "/"
    else:
        url = SITE + "/" + fn[:-5]
    # Title -> clean name (strip trailing " | Anchormere …")
    tm = re.search(r'<title>(.*?)</title>', c, re.S)
    raw = html.unescape(tm.group(1).strip()) if tm else fn[:-5]
    title_full = raw
    name = re.sub(r'\s*\|\s*Anchormere.*$', '', raw).strip() or raw
    # 0) Organization JSON-LD (site-wide; restore if stripped by earlier runs)
    if "parentOrganization" not in c:
        org = json.dumps({
            "@context": "https://schema.org", "@type": "Organization",
            "name": "Anchormere", "alternateName": "锚泊",
            "url": "https://anchormere.com", "email": "info@anchormere.com",
            "address": {"@type": "PostalAddress",
                        "addressRegion": "Guangdong", "addressCountry": "CN"},
            "description": "China sourcing partner for the Greater Bay Area manufacturing base — OEM, sourcing and joint manufacturing for global buyers.",
            "parentOrganization": {"@type": "Organization", "name": "深圳森亚实业有限公司"}},
            ensure_ascii=False)
        c = c.replace("</head>", f'<script type="application/ld+json">{org}</script>\n</head>', 1)
    # 1) hreflang (self-referential; site serves one URL, both locales)
    hl = (f'<link rel="alternate" hreflang="en" href="{url}">\n'
          f'<link rel="alternate" hreflang="zh-CN" href="{url}">\n'
          f'<link rel="alternate" hreflang="x-default" href="{url}">')
    cm = re.search(r'(<(?:meta name="canonical"|link rel="canonical") href="[^"]*"[^>]*>)', c)
    if cm:
        c = c.replace(cm.group(1), cm.group(1) + "\n" + hl, 1)
    else:
        c = c.replace("</head>", hl + "\n</head>", 1)
    # 2) BreadcrumbList
    if fn[:-5] in PRODUCT_PAGES:
        trail = [("Home", SITE + "/"), ("Products", SITE + "/supply-base"), (name, url)]
    else:
        trail = [("Home", SITE + "/"), (name, url)]
    items = [{"@type": "ListItem", "position": i + 1, "name": n, "item": u}
             for i, (n, u) in enumerate(trail)]
    bc = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList",
                     "itemListElement": items}, ensure_ascii=False)
    c = c.replace("</head>", f'<script type="application/ld+json">{bc}</script>\n</head>', 1)
    # 3) Product JSON-LD on product pages
    if fn[:-5] in PRODUCT_PAGES:
        dm = re.search(r'<meta name="description" content="([^"]+)"', c)
        desc = html.unescape(dm.group(1)) if dm else title_full
        prod = json.dumps({
            "@context": "https://schema.org", "@type": "Product",
            "name": title_full,
            "brand": {"@type": "Brand", "name": "Anchormere"},
            "description": desc,
            "category": "Greater Bay Area OEM sourcing",
            "offers": {"@type": "Offer", "priceCurrency": "USD",
                       "availability": "https://schema.org/InStock",
                       "url": url,
                       "seller": {"@type": "Organization", "name": "Anchormere"}},
        }, ensure_ascii=False)
        c = c.replace("</head>", f'<script type="application/ld+json">{prod}</script>\n</head>', 1)
    # 3b) FAQPage JSON-LD on homepage + product pages (GEO: machine-readable answers)
    if fn in FAQ_PAGES:
        qa = [{"@type": "Question", "name": q,
               "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQS]
        faq = json.dumps({"@context": "https://schema.org", "@type": "FAQPage",
                          "mainEntity": qa}, ensure_ascii=False)
        c = c.replace("</head>", f'<script type="application/ld+json">{faq}</script>\n</head>', 1)
    # 4) nav anchors for new categories
    if 'class="nav" href="consumer-smart-electronics.html"' not in c and CABLE_NAV in c:
        c = c.replace(CABLE_NAV, CABLE_NAV + NEW_NAV, 1)
    return c


def main():
        changed = 0
        for fn in sorted(os.listdir(ROOT)):
            if not fn.endswith(".html") or fn == "404.html":
                continue
            p = os.path.join(ROOT, fn)
            with open(p, encoding="utf-8") as f:
                c = f.read()
            nc = inject_head(c, fn)
            if nc != c:
                with open(p, "w", encoding="utf-8") as f:
                    f.write(nc)
                changed += 1
                print("  ✓", fn)
        print(f"injected SEO into {changed} files")


if __name__ == "__main__":
    main()
