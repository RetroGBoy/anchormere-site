#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade existing daily-digest news posts with:
  * editorial outbound links to verified public standards / government sources,
  * a visible "Sources & references" block printing each FULL link URL verbatim,
  * one rotated domain term (key term) per post,
  * Article JSON-LD `citation`,
  * card-title / content-kind meta for the news index.

Idempotent: posts already carrying the <!-- cited-enhance-v1 --> marker are
skipped. Reuses news_digest.py's single citation pool (briefings.json), so the
daily generator and the historical archive never drift apart.

Run: python3 scripts/enhance_news_citations.py
"""
import os
import re
import sys
import json
import html

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import news_digest as nd   # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, ".."))
MARKER = "<!-- cited-enhance-v1 -->"

TARGET_TO_CAT = {
    "rack-accessories": "datacenter",
    "consumer-smart-electronics": "consumer",
    "smart-toys-devices": "toys",
    "supply-base": "procurement",
}

DISCLAIMER = (
    '  <p style="color:var(--slate);font-size:13px">This is an automated news digest. '
    'The headline and link credit the original publisher; outbound references are editorial '
    'citations to public standards bodies and government sources. Anchormere adds buyer-focused '
    'commentary only and is not affiliated with, nor endorsed by, any cited source. '
    '本内容为自动资讯摘要，标题与链接归属原发布方；外部引用为对公开标准机构与政府来源的编辑性引用，'
    'Anchormere 仅补充买家视角解读，与来源无隶属关系，亦不主张其背书。</p>'
)

TERM_BOX = (
    '  <div style="background:var(--paper2);border-left:3px solid var(--brass);'
    'padding:12px 16px;margin:14px 0;border-radius:0 6px 6px 0">\n'
    '    <b data-zh="专有名词释义">Key term: {term_en}</b>\n'
    '    <p style="margin:4px 0 0">{term_def_en}</p>\n'
    '    <p class="cn" style="margin:3px 0 0">{term_def_zh}</p>\n'
    '  </div>\n'
)


def detect_category(text, en_title):
    """Read the framing link inside 'Why it matters for buyers', not the nav."""
    seg_start = text.find("Why it matters for buyers")
    seg_end = text.find('data-zh="来源"')
    seg = text[seg_start:seg_end] if seg_start >= 0 and seg_end > seg_start else text
    m = re.search(r"href='([a-z-]+)\.html'", seg)
    cat = TARGET_TO_CAT.get(m.group(1), "procurement") if m else "procurement"
    low = en_title.lower()
    if cat == "procurement" and any(x in low for x in (
            "electric vehicle", "ev battery", "bmw", "chevrolet", "rivian", "charger")):
        cat = "ev"
    return cat


def build_block(src_url, src_title, src_name, cat, en_title):
    ref_keys = nd.CAT_SOURCES.get(cat, nd.CAT_SOURCES["gba"])
    ref_items = [nd.CITED[k] for k in ref_keys]
    term_keys = nd.CAT_TERMS.get(cat, nd.CAT_TERMS["gba"])
    term_key = term_keys[sum(ord(c) for c in en_title) % len(term_keys)]
    term = nd.TERMS[term_key]

    context_en = " and ".join(
        f'<a href="{html.escape(s["url"], quote=True)}" target="_blank" '
        f'rel="noopener noreferrer">{html.escape(s["name"])}</a>' for s in ref_items
    )
    context_zh = "、".join(html.escape(s["zh"], quote=True) for s in ref_items)
    src_lines = [nd.source_attribution(src_url, src_title, src_name)]
    src_lines += [nd.source_attribution(s["url"], s["title"], s["name"], s["zh"])
                  for s in ref_items]
    sources_html = "\n".join(f"    <li>{x}</li>" for x in src_lines)

    block = (
        '  <h2 data-zh="延伸阅读与专有名词">Further reading &amp; key term</h2>\n'
        f'  <p data-zh="背景参考：{context_zh}的公开标准与官方资料。">'
        f'Background reference: public standards and official material from {context_en}.</p>\n'
        f'  <p class="cn">背景参考：{context_zh}的公开标准与官方资料。</p>\n'
        + TERM_BOX.format(
            term_en=html.escape(term["term"]),
            term_def_en=html.escape(term["en"]),
            term_def_zh=html.escape(term["zh"]),
        )
        + '  <h2 data-zh="来源与外链网址标注">Sources &amp; references</h2>\n'
          '  <ul>\n'
        + sources_html + '\n'
          '  </ul>\n'
          '  <p class="cn">每条来源均标注完整链接网址（Source URL），便于独立核验。</p>\n'
        + DISCLAIMER
    )
    cite = nd.citation_objects(ref_keys, extra=(src_title, src_url, src_name))
    return block, cite


def add_citation_ld(text, cite):
    """Attach schema.org citation to the Article JSON-LD block."""
    pat = re.compile(r'(<script type="application/ld\+json">\s*)(.*?)(\s*</script>)', re.S)
    for m in reversed(list(pat.finditer(text))):
        try:
            obj = json.loads(m.group(2))
        except Exception:
            continue
        if isinstance(obj, dict) and obj.get("@type") in ("Article", "NewsArticle"):
            obj["citation"] = cite
            return text[:m.start(2)] + json.dumps(obj, ensure_ascii=False) + text[m.end(2):]
    raise RuntimeError("找不到 Article JSON-LD 块")


def add_meta(text, en_title, zh_title):
    """Add card-title / card-title-zh / content-kind after the title-zh meta."""
    extra = (
        f'\n<meta name="card-title" content="{html.escape(en_title, quote=True)}">'
        f'\n<meta name="card-title-zh" content="{html.escape(zh_title, quote=True)}">'
        f'\n<meta name="content-kind" content="digest">'
    )
    pat = re.compile(r'(<meta name="title-zh" content="[^"]*">)')
    m = pat.search(text)
    if not m:
        raise RuntimeError("找不到 title-zh meta")
    return text[:m.end()] + extra + text[m.end():]


ZH_ALT_RE = re.compile(r'<meta property="og:locale:alternate"[^>]*>\s*\n?')


def strip_zh_alt(fn):
    """Keep the no-separate-Chinese-URL invariant idempotent.

    The Chinese UI is a client-side rendering of the same document, so any
    og:locale:alternate=zh_CN on a historical digest is a false alternate-page
    signal. Generators no longer emit it; this cleans already-generated pages.
    """
    path = os.path.join(ROOT, fn)
    t = open(path, encoding="utf-8").read()
    n = len(ZH_ALT_RE.findall(t))
    if n:
        open(path, "w", encoding="utf-8").write(ZH_ALT_RE.sub("", t))
    return n


def process(fn):
    path = os.path.join(ROOT, fn)
    text = open(path, encoding="utf-8").read()
    if MARKER in text:
        return "skip"

    om = re.search(
        r'<li>Original: <a href="([^"]+)"[^>]*>(.*?)</a>\s*—\s*(.*?)</li>', text, re.S)
    if not om:
        raise RuntimeError("找不到原文来源行")
    src_url = html.unescape(om.group(1))
    src_title = html.unescape(om.group(2))
    src_name = html.unescape(om.group(3))

    h1 = re.search(r'<h1 data-zh="[^"]*">(.*?)</h1>', text, re.S)
    zm = re.search(r'<meta name="title-zh" content="(.*?)"', text, re.S)
    en_title = html.unescape(h1.group(1).strip()) if h1 else src_title
    zh_title = html.unescape(zm.group(1).strip()) if zm else en_title

    cat = detect_category(text, en_title)
    block, cite = build_block(src_url, src_title, src_name, cat, en_title)

    start = text.find('  <h2 data-zh="来源">Source</h2>')
    if start < 0:
        raise RuntimeError("找不到旧 Source 区块")
    end_marker = "与来源无隶属关系。</p>"
    end = text.find(end_marker, start)
    if end < 0:
        raise RuntimeError("找不到旧免责声明结尾")
    end += len(end_marker)
    text = text[:start] + block + text[end:]

    text = add_citation_ld(text, cite)
    text = add_meta(text, en_title, zh_title)
    text = text.replace('<section class="l1">', MARKER + '\n<section class="l1">', 1)

    open(path, "w", encoding="utf-8").write(text)
    return cat


def main():
    files = sorted(f for f in os.listdir(ROOT)
                   if f.startswith("news-20") and f.endswith(".html"))
    stats = {}
    removed = 0
    for fn in files:
        removed += strip_zh_alt(fn)
        if 'name="content-kind" content="briefing"' in open(
                os.path.join(ROOT, fn), encoding="utf-8").read(4000):
            continue  # 10 篇简报已有完整引用，跳过
        try:
            r = process(fn)
        except Exception as e:
            print(f"  [FAIL] {fn}: {e}")
            return 1
        stats[r] = stats.get(r, 0) + 1
    print("增强完成：", ", ".join(f"{k}={v}" for k, v in sorted(stats.items())),
          f"| 清理 zh_CN 替代版本声明 {removed} 处")
    return 0


if __name__ == "__main__":
    sys.exit(main())
