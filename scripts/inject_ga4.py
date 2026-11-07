#!/usr/bin/env python3
"""Ensure every HTML page loads the consent-gated GA4 loader (assets/consent.js).
Idempotent: skips pages that already include it. Pure standard library."""
import os, glob
import os as _wa_os, sys as _wa_sys
_wa_sys.path.insert(0, _wa_os.path.dirname(_wa_os.path.abspath(__file__)))
import io_util  # workarea: write_if_changed / selected

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
    io_util.write_final(p, c)
    n += 1
    print("  ✓ added consent.js:", os.path.basename(p))
print(f"updated {n} pages")
