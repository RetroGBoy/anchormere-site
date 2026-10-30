#!/usr/bin/env python3
"""Ensure every HTML page loads the consent-gated GA4 loader (assets/consent.js).
Idempotent: skips pages that already include it. Pure standard library."""
import os, glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAG = '<script defer src="assets/consent.js"></script>'
n = 0
for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
    c = open(p, encoding="utf-8").read()
    if "assets/consent.js" in c:
        continue
    if "</head>" not in c:
        print("  ! skip (no </head>):", os.path.basename(p))
        continue
    c = c.replace("</head>", TAG + "\n</head>", 1)
    open(p, "w", encoding="utf-8").write(c)
    n += 1
    print("  ✓ added consent.js:", os.path.basename(p))
print(f"updated {n} pages")
