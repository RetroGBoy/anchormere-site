#!/usr/bin/env python3
"""Submit all sitemap URLs to IndexNow (Bing / Yandex / Seznam / Naver).

This automates the "收录提报" (indexing submission) step that cannot be done
via the Google Search Console API without the owner's Google account. IndexNow
is a single ping that covers Bing and its partners; combined with the manual
GSC sitemap submission (documented in SEO_GEO系统收纳提报流程.md) it closes the
loop for the major engines.

Usage:
    python3 scripts/submit_indexnow.py            # submit sitemap.xml
    python3 scripts/submit_indexnow.py --dry-run  # validate without network
    python3 scripts/submit_indexnow.py --limit 50 # cap url count (debug)

Key resolution: env INDEXNOW_KEY -> ./<key>.txt (published) -> ./.indexnow_key
Pure standard library; safe to run from CI.
"""
import os, sys, json, argparse, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SITE = "https://anchormere.com"
ENDPOINT = "https://api.indexnow.org/indexnow"
HOST = "anchormere.com"


def load_key():
    if os.environ.get("INDEXNOW_KEY"):
        return os.environ["INDEXNOW_KEY"].strip()
    # Published verification file: <key>.txt at site root.
    for name in os.listdir(ROOT):
        if name.endswith(".txt") and len(name) == 32 + 4:  # 32 hex + .txt
            p = os.path.join(ROOT, name)
            with open(p, encoding="utf-8") as f:
                k = f.read().strip()
            if k and len(k) == 32:
                return k
    dot = os.path.join(ROOT, ".indexnow_key")
    if os.path.exists(dot):
        with open(dot, encoding="utf-8") as f:
            return f.read().strip()
    raise SystemExit("IndexNow key not found (set INDEXNOW_KEY or add <key>.txt)")


def read_urls(limit=None):
    sp = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sp):
        raise SystemExit("sitemap.xml not found — run build_sitemap.py first")
    txt = open(sp, encoding="utf-8").read()
    urls = []
    import re
    for m in re.findall(r"<loc>(.*?)</loc>", txt, re.S):
        urls.append(m.strip())
    if limit:
        urls = urls[:limit]
    return urls


def submit(urls, key, dry_run=False):
    key_file = f"{key}.txt"
    payload = {
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key_file}",
        "urlList": urls,
    }
    body = json.dumps(payload).encode("utf-8")
    if dry_run:
        print(f"[dry-run] would POST {len(urls)} urls to {ENDPOINT}")
        print(f"[dry-run] keyLocation: https://{HOST}/{key_file}")
        return 0
    req = urllib.request.Request(
        ENDPOINT, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.getcode()
            data = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code = e.code
        data = e.read().decode("utf-8", "replace")
    except Exception as e:  # noqa
        print(f"INDEXNOW ERROR: {e}")
        return 2
    # 200 = OK (submitted), 202 = accepted (will be processed)
    if code in (200, 202):
        print(f"INDEXNOW OK: {code} — submitted {len(urls)} urls")
        return 0
    print(f"INDEXNOW FAILED: {code} — {data[:300]}")
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()
    key = load_key()
    urls = read_urls(args.limit)
    if not urls:
        print("No URLs to submit.")
        return 0
    print(f"Loaded {len(urls)} urls from sitemap.xml")
    rc = submit(urls, key, dry_run=args.dry_run)
    sys.exit(rc)


if __name__ == "__main__":
    main()
