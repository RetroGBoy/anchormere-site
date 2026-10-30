#!/usr/bin/env python3
"""Regenerate sitemap.xml from all *.html in the site root (excludes 404.html).
Pure standard library; wired into the nightly news workflow so new posts appear."""
import os, html

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

def priority_for(fn):
    if fn in PRIORITY:
        return PRIORITY[fn]
    if fn.startswith("news-20"):
        return NEWS_POST
    return CORE

def main():
    urls = []
    for fn in sorted(os.listdir(ROOT)):
        if not fn.endswith(".html") or fn == "404.html":
            continue
        url = SITE + "/" + fn[:-5]  # strip .html -> clean URL
        urls.append((url, priority_for(fn)))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, pri in urls:
        out.append(f'  <url><loc>{html.escape(url)}</loc>'
                   f'<changefreq>weekly</changefreq><priority>{pri}</priority></url>')
    out.append('</urlset>')
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")
    print(f"sitemap.xml written with {len(urls)} urls")

if __name__ == "__main__":
    main()
