#!/usr/bin/env python3
"""Regenerate sitemap.xml from all *.html in the site root (excludes 404.html).
Pure standard library; wired into the nightly news workflow so new posts appear.

<lastmod> comes from each page's OWN declared date (Last updated / datePublished /
lastReviewed), never from file mtime: a CI checkout resets every mtime to the run
date, which would otherwise advertise a fake site-wide daily update and make the
signal untrustworthy. The home page is emitted as the canonical root URL instead
of /index, which Cloudflare answers with a 308 redirect.
"""
import os, re, html, datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://anchormere.com"

# priority by page type
PRIORITY = {
    "index.html": 1.0, "consumer-smart-electronics.html": 0.9,
    "smart-toys-devices.html": 0.9, "supply-base.html": 0.9,
    "rack-accessories.html": 0.9, "cable-management.html": 0.9,
    "about.html": 0.8, "capabilities.html": 0.8, "process.html": 0.8,
    "quality.html": 0.8, "shipping.html": 0.8, "contact.html": 0.8,
    "news.html": 0.5, "privacy.html": 0.3, "terms.html": 0.3,
}
CORE = 0.7          # other static pages
NEWS_POST = 0.4     # dated news posts

DATE_PATTERNS = (
    re.compile(r'Last updated:\s*(\d{4}-\d{2}-\d{2})'),
    re.compile(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})'),
    re.compile(r'"lastReviewed"\s*:\s*"(\d{4}-\d{2}-\d{2})'),
)

def priority_for(fn):
    if fn in PRIORITY:
        return PRIORITY[fn]
    if fn.startswith("news-20"):
        return NEWS_POST
    return CORE


def page_date(fn):
    """Real content date declared inside the page; mtime is only a last resort."""
    path = os.path.join(ROOT, fn)
    t = open(path, encoding="utf-8").read()
    for pat in DATE_PATTERNS:
        m = pat.search(t)
        if m:
            return m.group(1)
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def main():
    urls = []
    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith(".html") or fn == "404.html":
            continue
        # Home is the canonical root (200); /index is a 308 redirect.
        slug = "" if fn == "index.html" else fn[:-5]
        url = SITE + "/" + slug
        urls.append((url, priority_for(fn), fn))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, pri, fn in urls:
        lm = page_date(fn)
        out.append(f'  <url><loc>{html.escape(url)}</loc>'
                   f'<lastmod>{lm}</lastmod>'
                   f'<changefreq>weekly</changefreq><priority>{pri}</priority></url>')
    out.append('</urlset>')
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"sitemap.xml written with {len(urls)} urls")

if __name__ == "__main__":
    main()
