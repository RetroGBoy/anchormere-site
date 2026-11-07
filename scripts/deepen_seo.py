#!/usr/bin/env python3
"""Deepen SEO recommendations 2 & 3 for Anchormere.

建议2 (subject<->keyword co-occurrence): inject cluster-grouped keyword-index
sections into the hub pages (index / capabilities / supply-base) so the pillar
pages lexically + via anchor links co-occur with ALL 23 long-tail keywords.

建议3 (entity structured-data chaining): add knowsAbout / areaServed / slogan to
the Organization entity on every static page so the site-wide subject entity is
consistently bound to its topical keywords (GEO + entity-disambiguation signal).
(The 23 long-tail pages get the same via scripts/longtail.py.)
"""
import os, re, json, html
import os as _wa_os, sys as _wa_sys
_wa_sys.path.insert(0, _wa_os.path.dirname(_wa_os.path.abspath(__file__)))
import io_util  # workarea: write_if_changed / selected

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEEDS = json.load(open(os.path.join(ROOT, "scripts", "longtail_seeds.json"), encoding="utf-8"))

KNOWS_ABOUT = ["OEM manufacturing", "ODM manufacturing", "private label manufacturing",
               "contract manufacturing", "PCBA", "SMT assembly", "EMS",
               "injection molding", "sheet metal fabrication", "low MOQ manufacturing",
               "China sourcing", "Greater Bay Area manufacturing", "product development",
               "small batch manufacturing", "electronic manufacturing services",
               "IoT modules", "wearable manufacturing", "toy manufacturing",
               "drone parts", "EV charger components", "USB-C charger OEM"]

AREA_SERVED = [{"@type": "Place", "name": "Worldwide"},
               {"@type": "Place", "name": "Greater Bay Area, China"},
               {"@type": "Country", "name": "China"}]
SLOGAN = "Your accountable China sourcing partner in the Greater Bay Area"

GROUP_TITLES = {
    "electronics": ("Electronics & connected devices", "电子与联网设备"),
    "toys": ("Toys, robots & STEM", "玩具、机器人与 STEM"),
    "industrial": ("Industrial & hardware", "工业与硬件"),
    "capability": ("OEM / ODM & sourcing services", "代工与采购服务"),
    "knowledge": ("Buyer's guides", "买家指南"),
}


def zh(s):
    return html.escape(s, quote=True)


def card(s):
    return (f'<div class="card"><h3 data-zh="{zh(s["zh_title"])}">{html.escape(s["en_title"])}</h3>'
            f'<p><a href="{s["slug"]}.html" data-zh="查看专题 →">Explore this topic →</a></p></div>')


def group_block(cluster):
    en, zht = GROUP_TITLES[cluster]
    subs = [s for s in SEEDS if s.get("cluster") == cluster]
    body = "\n".join(card(s) for s in subs)
    return (f'<h3 style="margin-top:26px" data-zh="{zh(zht)}">{html.escape(en)}</h3>\n'
            f'<div class="grid grid-3">\n{body}\n</div>')


def build_index_section():
    grouped = "\n".join(group_block(c) for c in GROUP_TITLES)
    return (f'<section class="l2" id="topic-index">\n  <div class="container">\n'
            '    <div class="eyebrow" data-zh="按采购主题浏览">Browse by sourcing topic</div>\n'
            '    <h2 data-zh="大湾区 OEM / ODM 与代采专题入口">Greater Bay Area OEM / ODM &amp; sourcing topics</h2>\n'
            '    <p class="cn">按采购主题浏览 · 同主体下全部长尾专题</p>\n'
            '    <p class="lead" data-zh="以下专题页围绕海外买家实际的 OEM/ODM 与代采检索意图撰写，集中于同一主体（Anchormere · 中国采购合作伙伴），强化主体与关键词的相关度。">These topic pages target the OEM/ODM and sourcing intents buyers actually search — all under one subject (Anchormere · your China sourcing partner), concentrating subject-to-keyword relevance.</p>\n'
            f'{grouped}\n  </div>\n</section>')


def build_capability_section():
    grouped = "\n".join(group_block(c) for c in ("capability", "knowledge"))
    return (f'<section class="l2" id="service-topics">\n  <div class="container">\n'
            '    <div class="eyebrow" data-zh="代工与采购服务专题">Sourcing &amp; manufacturing service topics</div>\n'
            '    <h2 data-zh="按 OEM/ODM 与采购意图进入对应专题">Jump to the OEM/ODM or sourcing topic you need</h2>\n'
            '    <p class="cn">代工与采购服务专题</p>\n'
            '    <p class="lead" data-zh="这些专项页针对海外买家最常搜索的代工、贴牌与找厂意图，便于从服务能力页直接进入对应长尾专题。">These focused pages target the contract-manufacturing, private-label and find-a-factory intents overseas buyers search most.</p>\n'
            f'{grouped}\n  </div>\n</section>')


def build_supplybase_index():
    blocks = []
    for cl, (en, zht) in GROUP_TITLES.items():
        subs = [s for s in SEEDS if s.get("cluster") == cl]
        links = "".join(
            f'<a class="tag" href="{s["slug"]}.html" data-zh="{zh(s["zh_title"])}">{html.escape(s["en_title"])}</a>'
            for s in subs)
        blocks.append(f'<h3 style="margin-top:22px" data-zh="{zh(zht)}">{html.escape(en)}</h3>\n<div class="tags">{links}</div>')
    body = "\n".join(blocks)
    return (f'<section class="l2" id="topic-index-sb">\n  <div class="container">\n'
            '    <div class="eyebrow" data-zh="采购主题索引">Sourcing topic index</div>\n'
            '    <h2 data-zh="同一主体下的全部长尾专题">Every long-tail topic, one subject</h2>\n'
            '    <p class="cn">采购主题索引 · 同主体（Anchormere）下全部长尾专题</p>\n'
            '    <p class="lead" data-zh="下面是本站在同一主体下覆盖的全部采购与 OEM 专题。每个链接都是一个针对具体检索意图的长尾落地页，集中强化主体与关键词之间的关联权重。">Below is the full set of sourcing and OEM topics covered under one subject. Each link is a long-tail landing page for a concrete search intent, concentrating the association weight between the subject and the keyword.</p>\n'
            f'{body}\n  </div>\n</section>')


def insert_before_footer(path, section, section_id):
    txt = open(path, encoding="utf-8").read()
    if section_id in txt:
        print(f"  skip (already present): {os.path.basename(path)}")
        return False
    idx = txt.rfind("<footer")
    if idx == -1:
        idx = txt.rfind("</body>")
    txt = txt[:idx] + section + "\n" + txt[idx:]
    io_util.write_final(path, txt)
    print(f"  inserted {section_id}: {os.path.basename(path)}")
    return True


LD_PAT = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def inject_entity(path):
    txt = open(path, encoding="utf-8").read()
    if "knowsAbout" in txt:
        return False

    def repl(m):
        inner = m.group(1)
        try:
            obj = json.loads(inner)
        except Exception:
            return m.group(0)
        if isinstance(obj, dict) and obj.get("@type") == "Organization" and "knowsAbout" not in obj:
            obj["slogan"] = SLOGAN
            obj["areaServed"] = AREA_SERVED
            obj["knowsAbout"] = KNOWS_ABOUT
            return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + '</script>'
        return m.group(0)

    new = LD_PAT.sub(repl, txt)
    if new != txt:
        io_util.write_final(path, new)
        return True
    return False


def main():
    print("建议2 — hub<->keyword co-occurrence sections:")
    insert_before_footer(os.path.join(ROOT, "index.html"), build_index_section(), "topic-index")
    insert_before_footer(os.path.join(ROOT, "capabilities.html"), build_capability_section(), "service-topics")
    insert_before_footer(os.path.join(ROOT, "supply-base.html"), build_supplybase_index(), "topic-index-sb")

    print("建议3 — site-wide Organization entity binding (knowsAbout/areaServed/slogan):")
    n = 0
    for fn in sorted(os.listdir(ROOT)):
        if fn.endswith(".html") and fn != "404.html":
            if inject_entity(os.path.join(ROOT, fn)):
                n += 1
    print(f"  injected into {n} static pages")


if __name__ == "__main__":
    main()
