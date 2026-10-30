#!/usr/bin/env python3
"""
Anchormere daily news digest generator.

- Pulls curated RSS feeds (consumer electronics / smart devices / GBA manufacturing).
- Keeps only items relevant to the buyer's scope (keyword filter).
- Generates an original, bilingual (EN/中文) short post per item:
  headline (quoted from source) + buyer-focused commentary + an internal
  product-link (SEO keyword association) + outbound link to the original source.
- Prepends a card to news.html and de-duplicates via news_state.json.

Pure standard library (no pip installs) so it runs on GitHub Actions' ubuntu runner.
"""

import os
import re
import json
import html
import datetime
from email.utils import parsedate_to_datetime
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
STATE_FILE = os.path.join(ROOT, "news_state.json")
NEWS_INDEX = os.path.join(ROOT, "news.html")
SITE = "https://anchormere.com"
MAX_POSTS_PER_RUN = 4
MAX_AGE_DAYS = 4  # only surface items newer than this

UA = "Mozilla/5.0 (compatible; AnchormereNewsBot/1.0; +https://anchormere.com)"

# ---- Curated feeds (consumer electronics / smart devices / GBA manufacturing) ----
FEEDS = [
    {"url": "https://techcrunch.com/feed/", "lang": "en", "name": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/index.xml", "lang": "en", "name": "The Verge"},
    {"url": "https://www.engadget.com/rss.xml", "lang": "en", "name": "Engadget"},
    {"url": "http://feeds.arstechnica.com/arstechnica/index", "lang": "en", "name": "Ars Technica"},
    {"url": "https://spectrum.ieee.org/feeds/topic/consumer-electronics.rss", "lang": "en", "name": "IEEE Spectrum"},
    {"url": "https://spectrum.ieee.org/feeds/topic/robotics.rss", "lang": "en", "name": "IEEE Spectrum (Robotics)"},
    {"url": "https://www.wired.com/feed/rss", "lang": "en", "name": "Wired"},
    {"url": "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10001115", "lang": "en", "name": "CNBC Technology"},
    {"url": "https://news.ycombinator.com/rss", "lang": "en", "name": "Hacker News"},
    {"url": "https://36kr.com/feed", "lang": "zh", "name": "36氪"},
]

# ---- Relevance keywords, grouped by product category ----
# 聚焦：采购 / 大湾区 / 产品（OEM·PCBA·外壳·模组·整机）。
KEYWORDS = {
    "consumer": ["smartphone", "phone", "tablet", "laptop", "wearable", "smartwatch",
                 "earbuds", "headphones", "display", "oled", "lcd", "battery", "charger",
                 "usb", "pcb", "pcba", "semiconductor", "chip", "electronics",
                 "speaker", "iot", "smart home", "appliance", "consumer tech",
                 "手机", "平板", "可穿戴", "消费电子", "半导体", "芯片", "显示", "智能硬件", "模组"],
    "toys": ["toy", "robot", "drone", "educational", "kids", "children", "gaming",
             "console", "ar/vr", "vr", "玩具", "机器人", "无人机", "教育硬件", "编程"],
    "datacenter": ["data center", "data-centre", "server", "rack", "cabling", "edge",
                   "数据中心", "服务器", "机柜", "算力"],
    "ev": ["electric vehicle", "ev battery", "ev ", "新能源汽车", "电动车", "电池", "充电桩"],
    "gba": ["shenzhen", "greater bay", "guangdong", "china manufactur", "factory",
            "supply chain", "export", "tariff", "made in china", "china's",
            "大湾区", "深圳", "广东", "制造", "供应链", "出口", "工厂", "东莞", "长三角"],
    # 采购/代工信号：命中即视为与买家采购高度相关
    "procurement": ["sourcing", "oem", "odm", "contract manufacturer", "contract manufacturing",
                    "manufactur", "assembly", "supplier", "suppliers", "production",
                    "import", "trade war", "tariffs", "moq", "prototype",
                    "采购", "代工", "制造", "工厂", "供应链", "出口", "关税", "贸易", "打样", "量产"],
}

# ---- Off-theme blocklist: 命中任一词即丢弃（与采购/制造无关的消费/娱乐/金融/政安新闻）----
BLOCK = [
    "fashion app", "stylish", "vrchat", "dating", "social media app", "influencer",
    "streaming", "netflix", "spotify", "tiktok", "instagram", "snapchat", "tiktok shop",
    "crypto", "bitcoin", "ethereum", "nft", "web3", "meme coin", "blockchain game",
    "celebrity", "box office", "movie", "tv show", "album", "concert",
    "restaurant", "recipe", "travel", "vacation", "sports", "football", "fashion week",
    "makeup", "beauty", "skincare",
    # 政安 / 法务 / 八卦噪声（与采购无关）
    "spy", "investigation", "investigated", "lawsuit", "arrest", "indict",
    "breach", "hacked", "fraud", "scam", "rumor", "leak", "layoff", "fired",
    "bankrupt", "bribe", "corruption", "protest", "sanction",
]

# 命中后用于排序的权重：产品/采购类优先，泛科技靠后
CAT_WEIGHT = {"consumer": 3, "toys": 3, "ev": 3, "datacenter": 2,
              "procurement": 3, "gba": 2}

CATEGORY_TARGET = {
    "consumer": ("consumer-smart-electronics.html", "consumer &amp; smart electronics", "消费与智能电子"),
    "toys": ("smart-toys-devices.html", "smart toys &amp; devices", "智能玩具与设备"),
    "datacenter": ("rack-accessories.html", "rack accessories", "机架配件"),
    "ev": ("supply-base.html", "Greater Bay Area supply base", "大湾区供应基地"),
    "gba": ("supply-base.html", "Greater Bay Area supply base", "大湾区供应基地"),
    "procurement": ("supply-base.html", "Greater Bay Area supply base", "大湾区供应基地"),
}
PRIMARY_ORDER = ["consumer", "toys", "datacenter", "ev", "procurement", "gba"]

FRAMING = {
    "consumer": {
        "en": "For buyers, this is a reminder of why sourcing <a href='{t}'>{a}</a> through the Greater Bay Area is efficient: PCBA, enclosures and display modules sit within a single day's logistics.",
        "zh": "对买家而言，这再次说明经由大湾区采购<a href='{t}'>{a}</a>的高效：PCBA、外壳与显示模组在一天物流半径内高度密集。",
    },
    "toys": {
        "en": "For buyers, this highlights the depth of <a href='{t}'>{a}</a> manufacturing in the GBA — screen, connected and educational products are prototyped and built here at speed.",
        "zh": "对买家而言，这凸显了大湾区的<a href='{t}'>{a}</a>制造纵深——带屏、联网与教育类产品在此被快速打样与量产。",
    },
    "datacenter": {
        "en": "For buyers, this reinforces demand for <a href='{t}'>{a}</a> and structured cabling as AI and hyperscale builds expand across the region.",
        "zh": "对买家而言，随着 AI 与超大规模建设在区域内扩张，对<a href='{t}'>{a}</a>与结构化布线的需求持续走强。",
    },
    "ev": {
        "en": "For buyers, this points to the <a href='{t}'>{a}</a> behind one of the world's largest EV ecosystems — batteries, components and electronics sourcing opportunities.",
        "zh": "对买家而言，这指向全球最大电动汽车生态背后的<a href='{t}'>{a}</a>——电池、零部件与电子采购机会。",
    },
    "gba": {
        "en": "For buyers, this is a signal to map the <a href='{t}'>{a}</a>: Shenzhen, Dongguan and the surrounding cluster concentrate the factories that matter.",
        "zh": "对买家而言，这是一个梳理<a href='{t}'>{a}</a>的信号：深圳、东莞及周边集群集中了最关键的工厂。",
    },
}


def local(tag):
    """Return an element's local name ignoring any XML namespace."""
    return tag.rsplit("}", 1)[-1]


# ---- Translation: DeepL (if TRANSLATE_KEY set) else keyless best-effort ----
def _translate_deepl(text, src, tgt, key):
    """DeepL Free API. src/tgt are 'en'/'zh-CN'."""
    src_d = "EN" if src == "en" else "ZH"
    tgt_d = "ZH" if tgt == "zh-CN" else "EN"
    try:
        url = "https://api-free.deepl.com/v2/translate"
        body = urllib.parse.urlencode({
            "text": text[:500],
            "source_lang": src_d,
            "target_lang": tgt_d,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={
            "Authorization": f"DeepL-Auth-Key {key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": UA,
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read().decode("utf-8"))
        out = resp.get("translations", [{}])[0].get("text", "")
        if out:
            return out.strip()
    except Exception as e:
        print(f"    (translate deepl failed: {e})")
    return ""


def translate(text, src, tgt):
    """Translate text; return original on any failure (graceful degradation)."""
    text = (text or "").strip()
    if not text:
        return text
    key = os.environ.get("TRANSLATE_KEY")
    if key:
        out = _translate_deepl(text, src, tgt, key)
        if out:
            return out
        print("    (no DeepL result; falling back to keyless)")
    # Keyless best-effort (flaky on CI shared IPs; kept only as last resort)
    q = urllib.parse.quote(text[:500])
    try:
        url = (f"https://translate.googleapis.com/translate_a/single"
               f"?client=gtx&sl={src}&tl={tgt}&dt=t&q={q}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        parts = [seg[0] for seg in data[0] if seg and seg[0]]
        out = "".join(parts).strip()
        if out:
            return out
    except Exception:
        pass
    try:
        url = f"https://api.mymemory.translated.net/get?q={q}&langpair={src}|{tgt}"
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode("utf-8"))
        out = data.get("responseData", {}).get("translatedText", "")
        if out and "MYMEMORY WARNING" not in out:
            return out.strip()
    except Exception:
        pass
    return text


def make_titles(item):
    """Return (en_title, zh_title), translating the missing language."""
    if item.get("lang") == "zh":
        zh = item["title"].strip()
        en = translate(zh, "zh-CN", "en")
        return en, zh
    en = item["title"].strip()
    zh = translate(en, "en", "zh-CN")
    return en, zh


CATEGORY_LABELS = {
    "consumer": ("consumer electronics", "消费电子"),
    "toys": ("smart toys & devices", "智能玩具与设备"),
    "datacenter": ("data-center hardware", "数据中心硬件"),
    "ev": ("EV & battery", "电动车与电池"),
    "gba": ("Greater Bay Area supply", "大湾区供应链"),
    "procurement": ("sourcing & procurement", "采购与供应链"),
}

STATIC_KEYWORDS = ["Anchormere", "China sourcing", "Greater Bay Area",
                   "Shenzhen manufacturing", "中国采购", "大湾区",
                   "深圳制造", "OEM", "export docs", "PCBA"]


def matched_terms(item, cats):
    blob = (item["title"] + " " + item["summary"]).lower()
    seen, out = set(), []
    for c in cats:
        for k in KEYWORDS[c]:
            k = k.strip()
            if k and k in blob and k not in seen:
                seen.add(k)
                out.append(k)
    return out


def build_keywords(item, cats):
    kws = []
    for c in cats:
        en, zh = CATEGORY_LABELS.get(c, (c, c))
        kws.append(en)
        kws.append(zh)
    kws.extend(matched_terms(item, cats))
    kws.extend(STATIC_KEYWORDS)
    seen, out = set(), []
    for k in kws:
        k = k.strip()
        if k and k.lower() not in seen:
            seen.add(k.lower())
            out.append(k)
    return ", ".join(out[:24])


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"posted": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        dt = parsedate_to_datetime(s)
        if dt:
            return dt.replace(tzinfo=None)
    except Exception:
        pass
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        pass
    return None


def get_link(el):
    # RSS: <link>url</link>  |  Atom: <link href="url" rel="alternate"/>
    for c in el:
        if local(c.tag) != "link":
            continue
        if c.text and c.text.strip():
            return c.text.strip()
        rel = c.get("rel")
        if rel in (None, "alternate"):
            href = c.get("href")
            if href:
                return href.strip()
    return None


def get_text(el, *tags):
    wanted = set(tags)
    for c in el.iter():
        if local(c.tag) in wanted and c.text and c.text.strip():
            return c.text.strip()
    return ""


def fetch_feed(feed):
    out = []
    try:
        req = urllib.request.Request(feed["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = r.read()
        root = ET.fromstring(data)
        is_rss = local(root.tag) == "rss"
        for it in root.iter():
            if local(it.tag) not in ("item", "entry"):
                continue
            title = get_text(it, "title")
            link = get_link(it)
            summary = get_text(it, "description", "summary", "content")
            pub = get_text(it, "pubDate", "published", "updated")
            if not (title and link):
                continue
            out.append({
                "title": title,
                "link": link,
                "summary": re.sub(r"<[^>]+>", " ", summary or "")[:280],
                "pub": parse_date(pub),
                "lang": feed["lang"],
                "source": feed["name"],
            })
    except Exception as e:
        print(f"  ! feed failed: {feed['name']} ({feed['url']}) -> {e}")
    return out


def categorize(item):
    blob = (item["title"] + " " + item["summary"]).lower()
    cats = [c for c, kws in KEYWORDS.items() if any(k in blob for k in kws)]
    return cats


def slugify(text):
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text[:50] or "update"


def build_post(item, cats, today, title_en, title_zh):
    primary = next((c for c in PRIMARY_ORDER if c in cats), "gba")
    t, a_en, a_zh = CATEGORY_TARGET[primary]
    en_why = FRAMING[primary]["en"].format(t=t, a=a_en)
    zh_why = FRAMING[primary]["zh"].format(t=t, a=a_zh)

    gba_extra_en = ""
    gba_extra_zh = ""
    if "gba" in cats and primary != "gba":
        gba_extra_en = " See how it connects to the wider <a href='supply-base.html'>Greater Bay Area supply base</a>."
        gba_extra_zh = "了解它与更广阔的<a href='supply-base.html'>大湾区供应基地</a>如何关联。"

    en_title = html.escape(html.unescape(title_en))
    zh_title = html.escape(html.unescape(title_zh))
    src_title = html.escape(html.unescape(item["title"]))
    src_name = html.escape(item["source"])
    src_url = html.escape(item["link"])
    keywords = build_keywords(item, cats)
    kw_esc = html.escape(keywords)

    en_lead = (f"Anchormere's digest bot is tracking “{en_title}” and what it signals "
               f"for overseas buyers who source through the Greater Bay Area.{gba_extra_en}")
    zh_lead = (f"Anchormere 摘要机器人正在追踪「{zh_title}」，以及它对经由大湾区采购的"
               f"海外买家的信号意义。{gba_extra_zh}")

    slug = slugify(item["title"])
    filename = f"news-{today.strftime('%Y-%m-%d')}-{slug}.html"
    # avoid collisions
    base = filename
    i = 1
    while os.path.exists(os.path.join(ROOT, filename)):
        filename = base.replace(".html", f"-{i}.html")
        i += 1

    json_ld = json.dumps({
        "@context": "https://schema.org", "@type": "Article",
        "headline": title_en,
        "keywords": keywords,
        "datePublished": today.strftime("%Y-%m-%d"),
        "author": {"@type": "Organization", "name": "Anchormere"},
        "publisher": {"@type": "Organization", "name": "Anchormere"},
        "description": html.unescape(item["summary"][:160] or item["title"]),
        "mainEntityOfPage": f"{SITE}/{filename}",
    }, ensure_ascii=False)

    html_doc = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{en_title} | Anchormere</title>
<meta name="title-zh" content="{zh_title}">
<meta name="keywords" content="{kw_esc}">
<meta name="description" content="{html.escape(html.unescape(item['summary'][:155] or item['title']))}">
<meta name="desc-zh" content="{html.escape(html.unescape(item['summary'][:155] or item['title']))}">
<link rel="canonical" href="{SITE}/{filename}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Anchormere">
<meta property="og:locale" content="en_US">
<meta property="og:locale:alternate" content="zh_CN">
<meta property="og:title" content="{en_title}">
<meta property="og:description" content="{html.escape(html.unescape(item['summary'][:155] or item['title']))}">
<meta property="og:url" content="{SITE}/{filename}">
<meta property="og:image" content="{SITE}/assets/img/warehouse.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{en_title}">
<meta name="twitter:description" content="{html.escape(html.unescape(item['summary'][:155] or item['title']))}">
<meta name="twitter:image" content="{SITE}/assets/img/warehouse.jpg">
<link rel="stylesheet" href="assets/style.css">
<link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="assets/consent.css">
<script type="application/ld+json">
{json_ld}
</script>
<script defer src="assets/consent.js"></script>
</head><body>
<div class="topbar"><span data-zh="⚓ <b>48 小时报价</b>">⚓ <b>48h quote</b></span><span data-zh="🏭 <b>20+ 家认证工厂</b>">🏭 <b>20+ vetted factories</b></span><span data-zh="📦 <b>500 件起订</b>">📦 <b>500 pcs MOQ</b></span><span data-zh="📑 <b>完整出口单证</b>">📑 <b>Full export docs</b></span></div>
<nav class="mainnav"><div class="container">
  <div class="brand" data-zh="Anchormere <small>锚泊 · 中国采购合作伙伴</small>">Anchormere <small>锚泊 · 中国采购合作伙伴</small></div>
  <a class="nav" href="index.html" data-zh="首页">Home</a><a class="nav" href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a>
  <a class="nav" href="cable-management.html" data-zh="线缆管理">Cable Mgmt</a><a class="nav" href="capabilities.html" data-zh="供应能力">Capabilities</a>
  <a class="nav" href="certifications.html" data-zh="认证说明">Certifications</a>
  <a class="nav" href="about.html" data-zh="关于我们">About</a>  <a class="nav" href="faq.html" data-zh="常见问题">FAQ</a>
  <a class="nav" href="supply-base.html" data-zh="供应基地">Supply Base</a>
  <a class="nav" href="news.html" data-zh="资讯动态">News</a>
  <a class="btn-quote" href="contact.html" data-zh="获取报价">Get a Quote</a>
</div></nav>
<section class="l1"><div class="container">
  <div class="crumb"><a href="index.html" data-zh="首页">Home</a> / <a href="news.html" data-zh="资讯动态">News</a> / <span data-zh="{zh_title}">{en_title}</span></div>
  <div class="eyebrow" data-zh="自动摘要 · {today.strftime('%Y-%m-%d')}">Auto digest · {today.strftime('%Y-%m-%d')}</div>
  <h1 data-zh="{zh_title}">{en_title}</h1>
  <p class="lead">{en_lead}</p>
  <p class="cn">{zh_lead}</p>
  <h2 data-zh="为何关乎买家">Why it matters for buyers</h2>
  <p>{en_why}</p>
  <p class="cn">{zh_why}</p>
  <h2 data-zh="来源">Source</h2>
  <ul>
    <li>Original: <a href="{src_url}" target="_blank" rel="nofollow noopener">{src_title}</a> — {src_name}</li>
  </ul>
  <p class="cn">原文：<a href="{src_url}" target="_blank" rel="nofollow noopener">{src_title}</a> —— {src_name}</p>
  <p style="color:var(--slate);font-size:13px">This is an automated news digest. The headline and link credit the original publisher; Anchormere adds buyer-focused commentary only and is not affiliated with the source. 本内容为自动资讯摘要，标题与链接归属原发布方，Anchormere 仅补充买家视角解读，与来源无隶属关系。</p>
  <div style="background:var(--paper2);border-left:4px solid var(--brass);padding:14px 18px;margin:18px 0;border-radius:0 8px 8px 0">
    <b data-zh="想要一份属于你产品的集群地图？">Want a cluster map for your product?</b> <span data-zh="告诉我们品类，我们将为你匹配最合适的大湾区城市与认证工厂。">Tell us the category and we'll map the right GBA cities and vetted factories.</span> <a href="contact.html" data-zh="获取报价 →">Get a quote →</a>
  </div>
</div></section>
<footer><div class="container">
  <div class="cols">
    <div><h4 data-zh="Anchormere 锚泊 · 中国采购合作伙伴">Anchormere 锚泊 · 中国采购合作伙伴</h4><ul><li data-zh="中国采购合作伙伴 · OEM · 采购 · 联合制造 · 大湾区">China sourcing partner · OEM · sourcing · joint manufacturing · Greater Bay Area</li><li data-zh="中国 · 大湾区">Greater Bay Area, China</li><li>中国广东深圳市光明区特发工业园B座</li></ul></div>
    <div><h4 data-zh="产品">Products</h4><ul><li><a href="rack-accessories.html" data-zh="机架配件">Rack Accessories</a></li><li><a href="cable-management.html" data-zh="线缆管理">Cable Management</a></li><li><a href="consumer-smart-electronics.html" data-zh="消费与智能电子">Consumer &amp; Smart Electronics</a></li><li><a href="smart-toys-devices.html" data-zh="智能玩具与设备">Smart Toys &amp; Devices</a></li><li><a href="supply-base.html" data-zh="供应基地">Supply Base</a></li></ul></div>
    <div><h4 data-zh="公司">Company</h4><ul><li><a href="about.html" data-zh="关于我们">About</a></li><li><a href="capabilities.html" data-zh="供应能力">Capabilities</a></li><li><a href="certifications.html" data-zh="认证说明">Certifications</a></li><li><a href="faq.html" data-zh="常见问题">FAQ</a></li>
    <li><a href="process.html" data-zh="合作流程">Process</a></li><li><a href="quality.html" data-zh="品质管控">Quality</a></li><li><a href="shipping.html" data-zh="包装物流">Shipping</a></li></ul></div>
    <div><h4 data-zh="法律">Legal</h4><ul><li data-zh="运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）">Operator: 深圳森亚实业有限公司 (Shenzhen Senya Industrial Co., Ltd.)</li><li data-zh="商标：Anchormere / Buyeex">Trade mark: Anchormere / Buyeex</li></ul></div>
  </div>
  <p style="margin-top:20px;text-align:center;color:var(--on-dark2)" data-zh="© 2026 Anchormere · 由深圳森亚实业有限公司运营">© 2026 Anchormere · Operated by 深圳森亚实业有限公司</p>
  <p style="margin-top:6px;text-align:center;color:var(--on-dark2);font-size:12px;opacity:.75" data-zh="最后更新：{today.strftime('%Y-%m-%d')}">Last updated: {today.strftime('%Y-%m-%d')}</p>
</div><p style="text-align:center;margin-top:10px;font-size:12px"><a href="privacy.html" data-zh="隐私政策">Privacy Policy</a> · <a href="terms.html" data-zh="服务条款">Terms &amp; Conditions</a></p>
</footer>
<a class="wa-float" href="https://wa.me/8619068984158" data-zh="💬 WhatsApp 咨询">💬 WhatsApp</a>
<script defer src="assets/lang.js"></script>
</body></html>
"""
    return filename, html_doc


def update_index(filename, item, cats, today, title_en, title_zh):
    with open(NEWS_INDEX, encoding="utf-8") as f:
        idx = f.read()
    headline = html.escape(html.unescape(title_en))
    headline_zh = html.escape(html.unescape(title_zh))
    en_blurb = "Daily auto-digest: what this development means for sourcing through the Greater Bay Area."
    zh_blurb = "每日自动摘要：这一动向对经由大湾区采购意味着什么。"
    card = f"""    <div class="card">
      <div style="font-size:12px;color:var(--brass);letter-spacing:.5px;text-transform:uppercase;margin-bottom:6px" data-zh="自动摘要 · {today.strftime('%Y-%m-%d')}">Auto digest · {today.strftime('%Y-%m-%d')}</div>
      <h3 data-zh="{headline_zh}">{headline}</h3>
      <p data-zh="{zh_blurb}">{en_blurb}</p>
      <a href="{filename}" data-zh="阅读全文 →">Read more →</a>
    </div>
"""
    marker = '<div class="grid grid-3">'
    if marker in idx:
        idx = idx.replace(marker, marker + "\n" + card, 1)
    else:
        print("  ! news.html grid marker not found; skipping index update")
    # refresh Last updated dates
    idx = idx.replace("Last updated: 2026-10-29", f"Last updated: {today.strftime('%Y-%m-%d')}")
    idx = idx.replace("最后更新：2026-10-29", f"最后更新：{today.strftime('%Y-%m-%d')}")
    with open(NEWS_INDEX, "w", encoding="utf-8") as f:
        f.write(idx)


def main():
    today = datetime.datetime.utcnow()
    state = load_state()
    posted = set(state.get("posted", []))

    print("Fetching feeds...")
    items = []
    for feed in FEEDS:
        items.extend(fetch_feed(feed))
    print(f"  collected {len(items)} raw items")

    # filter relevance + recency + dedup + off-theme blocklist
    candidates = []
    for it in items:
        cats = categorize(it)
        if not cats:
            continue
        blob = (it["title"] + " " + it["summary"]).lower()
        if any(b in blob for b in BLOCK):
            continue
        if it["link"] in posted:
            continue
        if it["pub"]:
            age = (today - it["pub"]).days
            if age > MAX_AGE_DAYS:
                continue
        it["cats"] = cats
        it["score"] = sum(CAT_WEIGHT.get(c, 0) for c in cats)
        candidates.append(it)

    # rank: procurement/product relevance first, then recency
    candidates.sort(key=lambda x: (x["score"], x["pub"] or datetime.datetime.min), reverse=True)
    chosen = candidates[:MAX_POSTS_PER_RUN]

    print(f"  {len(chosen)} items selected for publishing")
    generated = []
    for it in chosen:
        title_en, title_zh = make_titles(it)
        filename, doc = build_post(it, it["cats"], today, title_en, title_zh)
        with open(os.path.join(ROOT, filename), "w", encoding="utf-8") as f:
            f.write(doc)
        update_index(filename, it, it["cats"], today, title_en, title_zh)
        posted.add(it["link"])
        generated.append((filename, it["title"], it["cats"]))
        print(f"  + {filename}  [{','.join(it['cats'])}]  {it['title'][:60]}")

    state["posted"] = list(posted)
    save_state(state)
    print(f"Done. {len(generated)} post(s) generated.")


if __name__ == "__main__":
    main()
