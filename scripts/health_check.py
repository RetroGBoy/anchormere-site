#!/usr/bin/env python3
"""
Live site health monitor for anchormere.com.

Pulls *real* responses from the production site (Cloudflare Pages) and asserts the
critical SEO / infrastructure invariants that were historically fragile:

  - Core pages return HTTP 200
  - Every HTML page uses a proper <link rel="canonical"> (NOT the invalid
    <meta name="canonical"> form)
  - Index / news / archive pages carry hreflang alternates (en / zh-CN / x-default)
  - sitemap.xml is well-formed and every listed URL resolves 200
  - robots.txt + llms.txt are reachable; robots allows the AI crawlers
  - consent.js ships the correct GA4 id; contact.html carries the live
    Web3Forms access_key + the current WhatsApp / WeChat contacts
  - No internal dead links (sampled)

Exit code: 0 = healthy, 1 = at least one CRITICAL regression (fails CI so the
repo owner gets a GitHub notification).
"""

import sys
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

SITE = "https://anchormere.com"

# Pages whose <head> MUST carry hreflang alternates.
HREFLANG_REQUIRED = {
    "/", "/news", "/news-archive.html",
}
# Other key pages to status-check (subset of the full sitemap).
CORE_PAGES = [
    "/", "/about.html", "/contact.html", "/capabilities.html",
    "/supply-base.html", "/news.html", "/privacy.html", "/terms.html",
    "/rack-accessories.html", "/consumer-smart-electronics.html",
    "/smart-toys-devices.html", "/cable-management.html",
]

# Contact / tracking invariants that must not silently regress.
EXPECT = {
    "GA4_ID": "G-EZE1LV2MRH",
    "WEB3FORMS_KEY": "045c5b38-d0a4-4f3b-80b1-c94cf66b437a",
    "WHATSAPP": "8619068984158",
    "WECHAT": "SenyaSz",
    "EMAIL": "Anchormere@gmail.com",
}

CRITICAL = []   # (area, detail)
WARNINGS = []   # (area, detail)


def fetch(url, timeout=15, max_bytes=2_000_000):
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; AnchormereHealthBot/1.0)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read(max_bytes).decode("utf-8", "ignore")
            return r.status, data, dict(r.getheaders())
    except urllib.error.HTTPError as e:
        return e.code, "", dict(e.headers)
    except Exception as e:  # network / timeout
        return None, "", {"_err": str(e)}


def check(name, ok, detail=""):
    if ok:
        print(f"  [ok]   {name}")
    else:
        print(f"  [FAIL] {name}  {detail}")
        CRITICAL.append((name, detail))


def warn(name, detail=""):
    print(f"  [warn] {name}  {detail}")
    WARNINGS.append((name, detail))


def main():
    print("=" * 64)
    print("ANCHORMERE LIVE HEALTH CHECK  " + SITE)
    print("=" * 64)

    # ---- 1. Core page status + canonical form + hreflang --------------------
    print("\n[1] Core pages: status / canonical / hreflang")
    for path in CORE_PAGES:
        url = SITE + path
        status, body, _ = fetch(url)
        ok_status = status == 200
        ok_canon = '<link rel="canonical"' in body
        has_meta_canon = 'name="canonical"' in body
        ok_href = ('rel="alternate" hreflang="en"' in body and
                   'rel="alternate" hreflang="x-default"' in body)
        need_href = path in HREFLANG_REQUIRED

        check(f"{path} HTTP 200", ok_status, f"got {status}")
        check(f"{path} <link rel=canonical>", ok_canon,
              "uses invalid <meta name=canonical>" if has_meta_canon else "missing")
        if need_href:
            check(f"{path} hreflang alternates", ok_href, "missing hreflang")

    # ---- 2. robots.txt + llms.txt ------------------------------------------
    print("\n[2] robots.txt / llms.txt")
    _, robots, _ = fetch(SITE + "/robots.txt")
    if robots:
        # Parse user-agent groups. A bot is "blocked" only if its own group (or
        # the catch-all "*") carries a BLANKET disallow. Naming a bot with an
        # Allow (or a path-specific disallow) is fine and is GEO-positive.
        groups, cur = [], None
        for line in robots.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("user-agent:"):
                cur = {"agent": line.split(":", 1)[1].strip().lower(), "rules": []}
                groups.append(cur)
            elif cur is not None:
                cur["rules"].append(line)
        for bot in ["GPTBot", "PerplexityBot", "ClaudeBot", "Google-Extended", "Applebot"]:
            blocked = False
            for g in groups:
                if g["agent"] == bot or g["agent"] == "*":
                    for r in g["rules"]:
                        rl = r.lower()
                        if rl.startswith("disallow:"):
                            path = rl[len("disallow:"):].strip()
                            # A blanket block under the bot's own or "*" group.
                            if path in ("", "/", "*"):
                                blocked = True
            if blocked:
                warn(f"robots blocks {bot}", "blanket Disallow present")
    check("robots.txt reachable & not blocking AI crawlers",
          bool(robots) and "Disallow: /" not in robots and "Disallow: *" not in robots,
          "missing or over-restrictive")

    _, llms, _ = fetch(SITE + "/llms.txt")
    check("llms.txt reachable", bool(llms) and "anchormere.com" in llms,
          "missing or empty")

    # ---- 3. sitemap integrity ----------------------------------------------
    print("\n[3] sitemap.xml")
    _, sm, _ = fetch(SITE + "/sitemap.xml")
    urls = []
    if sm:
        try:
            root = ET.fromstring(sm)
            ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            urls = [u.findtext("s:loc", "", ns) for u in root.findall("s:url", ns)]
        except Exception as e:
            warn("sitemap parse", str(e))
    check("sitemap well-formed & non-empty", len(urls) > 0, f"urls={len(urls)}")
    print(f"      sitemap lists {len(urls)} URLs; sampling status...")
    bad = 0
    for u in urls[:30]:  # sample first 30 to bound runtime
        st, _, _ = fetch(u)
        if st != 200:
            bad += 1
            warn(f"sitemap URL {st}", u)
    check("sitemap sample (first 30) all 200", bad == 0, f"{bad} non-200")

    # ---- 4. tracking + contact invariants ----------------------------------
    print("\n[4] tracking & contact invariants")
    _, consent, _ = fetch(SITE + "/assets/consent.js")
    check("GA4 id present in consent.js", EXPECT["GA4_ID"] in consent,
          "GA4 id missing")
    _, contact, _ = fetch(SITE + "/contact.html")
    check("Web3Forms access_key present", EXPECT["WEB3FORMS_KEY"] in contact,
          "access_key missing")
    check("WhatsApp number present", EXPECT["WHATSAPP"] in contact,
          "WhatsApp missing")
    check("WeChat id present (SenyaSz)", EXPECT["WECHAT"] in contact,
          "WeChat missing")
    check("Contact email present", EXPECT["EMAIL"] in contact, "email missing")
    # JSON-LD on home
    _, home, _ = fetch(SITE + "/")
    check("Home JSON-LD present", 'application/ld+json' in home, "no structured data")

    # ---- 5. internal dead-link sweep (sampled) -----------------------------
    print("\n[5] internal link sweep (sampled)")
    seen = set()
    to_check = ["/", "/news.html", "/contact.html", "/supply-base.html",
                "/index.html"]
    dead = 0
    checked = 0
    for p in to_check:
        _, b, _ = fetch(SITE + p)
        if not b:
            continue
        for m in re.finditer(r'href="([^"#?]+)"', b):
            href = m.group(1)
            if href.startswith("http") and not href.startswith(SITE):
                continue
            if href.startswith("mailto:") or href.startswith("tel:") or href.startswith("https://wa.me"):
                continue
            rel = href if href.startswith("http") else (SITE + ("" if href.startswith("/") else "/") + href)
            rel = rel.split("#")[0]
            if rel in seen or rel.rstrip("/") == SITE:
                continue
            seen.add(rel)
            if len(seen) > 80:
                break
    for u in list(seen)[:80]:
        st, _, _ = fetch(u)
        checked += 1
        if st != 200:
            dead += 1
            warn(f"dead internal link {st}", u)
    check("internal links resolve (sampled %d)" % checked, dead == 0,
          f"{dead} dead")

    # ---- summary -----------------------------------------------------------
    print("\n" + "=" * 64)
    print(f"CRITICAL issues : {len(CRITICAL)}")
    print(f"WARNINGS       : {len(WARNINGS)}")
    print("=" * 64)
    if CRITICAL:
        for a, d in CRITICAL:
            print(f"  CRIT {a}: {d}")
    if WARNINGS:
        for a, d in WARNINGS:
            print(f"  WARN {a}: {d}")
    print("\nRESULT:", "UNHEALTHY" if CRITICAL else "HEALTHY")
    sys.exit(1 if CRITICAL else 0)


if __name__ == "__main__":
    main()
