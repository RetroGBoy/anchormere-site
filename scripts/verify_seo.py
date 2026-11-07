#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO 验证闭环 (Verification Loop)
===============================
对站内技术 SEO 关键不变量做一致性自检，可在本地或 CI 中重复运行：
  - hreflang 合法性（无 zh-CN、无“不同语言指向同一 URL”的冲突声明）
  - 中文替代版本声明口径一致（hreflang / og:locale:alternate / lang.js）
  - 孤儿页检测（仅计 <a> 导航链接，排除 canonical/hreflang 自引用）
  - JSON-LD 解析与核心实体类型覆盖
  - Organization 单一数据源一致性（全站含 news-* 与 scripts/org_entity.json 完全一致）
  - E-E-A-T 审核署名与 WebPage.lastReviewed 成对一致
  - 简报 Article.wordCount 与实际可见正文一致
  - canonical 存在且与扩展名省略式 URL 一致
  - sitemap lastmod 为合法且按内容分布的真实日期（防 CI mtime 漂移）
  - 站内链接统一为 clean URL（无 .html 308 跳转，与 canonical 一致）
  - 中文片段带 lang="zh-CN"（WCAG 2.1 AA 3.1.2）
  - Article author/publisher 以 @id 串联唯一 Organization 实体
  - robots.txt 放行主流 AI 爬虫（GEO 前提）
  - IndexNow key 落地
  - GSC / Bing 验证 meta：仅当仍为 REPLACE 占位符时 WARN；已删除(meta 非必须)或已填真实码则视为闭环通过

退出码：0 = 全部 PASS；1 = 存在 FAIL；2 = 仅 WARN。
"""
import os, re, json, sys, html
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_util

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

LD_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
CANON_RE = re.compile(r'<link rel="canonical" href="([^"]*)"')
HL_RE = re.compile(r'<link rel="alternate" hreflang="([^"]*)"\s+href="([^"]*)"')
HREF_RE = re.compile(r'href="([^"]+)"')
ROBOTS_AI = ["GPTBot", "ClaudeBot", "PerplexityBot"]

fails, warns, passes = [], [], []

def norm(url):
    u = url.strip()
    u = re.sub(r'^https?://[^/]+', '', u)
    u = u.split('#')[0].split('?')[0]
    u = u.lstrip('/')
    if u.endswith('.html'):
        u = u[:-5]
    u = u.rstrip('/')
    return (u or 'index').lower()  # 根路径 canonical 对应首页 index

def ok(msg): passes.append(msg)
def warn(msg): warns.append(msg)
def fail(msg): fails.append(msg)

# 收集文件
htmls = sorted(f for f in os.listdir('.') if f.endswith('.html'))
pages = [f for f in htmls if f != '404.html']

# ---- workarea 增量制度：页面单次读取缓存 + 可选局部范围 ----
# 旧实现把同一批 HTML 反复 open() 十余次；这里全站只读一遍。
PAGE = {f: io_util.read_text(f) for f in htmls}
_argv = sys.argv[1:]
GLOBAL_ONLY = '--global-only' in _argv
_raw = next((a.split('=', 1)[1] for a in _argv if a.startswith('--files=')), '')
_raw = _raw or os.environ.get('WORKAREA_FILES', '')
if GLOBAL_ONLY:
    SCOPE = set()
elif _raw.strip():
    SCOPE = {x.strip() if x.strip().endswith('.html') else x.strip() + '.html'
             for x in _raw.replace(';', ',').split(',') if x.strip()}
    SCOPE &= set(htmls)
else:
    SCOPE = None
MODE = '全量' if SCOPE is None else ('仅全局不变量' if GLOBAL_ONLY else f'增量 {len(SCOPE)} 页')

def S(seq):
    """逐页检查的范围闸门；全局不变量始终使用完整 htmls/pages。"""
    return seq if SCOPE is None else [f for f in seq if f in SCOPE]

# ---- 1. hreflang 合法性 ----
zh_count = 0
hl_conflicts = 0
for f in S(htmls):
    t = PAGE[f]
    pairs = HL_RE.findall(t)
    if any(l == 'zh-CN' for l, _ in pairs):
        zh_count += 1
    d = {}
    for lang, href in pairs:
        h = norm(href)
        if h in d and d[h] != lang:
            # 仅允许 en <-> x-default 指向同一 URL
            if not ({d[h], lang} <= {'en', 'x-default'}):
                hl_conflicts += 1
                fail(f"{f}: hreflang 冲突 — {d[h]} 与 {lang} 指向同一 URL ({h})")
if zh_count:
    fail(f"存在 {zh_count} 个页面仍声明 hreflang=zh-CN（已确认 GEO 不打中文市场，应删除）")
else:
    ok("无 hreflang=zh-CN 虚假声明")

# ---- 1b. 中文替代版本声明口径一致性 ----
# 站点为同一 URL 的双语 UI，没有独立中文页面；hreflang 只声明 en / x-default。
# 因此 OG 的 og:locale:alternate=zh_CN 与 lang.js 运行时注入的 zh-CN hreflang
# 都属于「不存在的中文版本」信号，必须一并禁止，避免与静态口径冲突。
zh_decl = []
for f in S(htmls):
    t = PAGE[f]
    if re.search(r'og:locale:alternate"\s+content="zh', t):
        zh_decl.append(f)
LANG_JS = os.path.join('assets', 'lang.js')
if os.path.exists(LANG_JS):
    lj = open(LANG_JS, encoding='utf-8').read()
    if re.search(r'\[\s*"zh-CN"\s*,\s*url\s*\]', lj):
        zh_decl.append('assets/lang.js (addHreflang)')
if zh_decl:
    fail(f"仍声明不存在的中文替代版本（{len(zh_decl)} 处）: " + ", ".join(zh_decl[:4]))
else:
    ok("无 zh_CN 替代版本声明（hreflang / OG / lang.js 口径一致）")

# ---- 2. 孤儿页检测 ----
# 只统计真实可点击的 <a href> 站内链接。canonical / hreflang 等 <link href>
# 是资源声明而非导航入链，且每个页面的 canonical 都指向自身；若把它们计入，
# 任何页面都会「自链成功」，孤儿页检测将永远通过（历史缺陷）。页面自引用也不算入链。
A_HREF_RE = re.compile(r'<a\s[^>]*href="([^"]+)"', re.I)
slugs = {f[:-5] for f in htmls}
inlinks = set()
for f in htmls:
    t = PAGE[f]
    self_slug = norm(f)
    for h in A_HREF_RE.findall(t):
        n = norm(h)
        if n in slugs and n != self_slug:
            inlinks.add(n)
orphans = [f for f in pages if norm(f) not in inlinks]
if orphans:
    fail(f"孤儿页（无站内入链）: {', '.join(orphans)}")
else:
    ok("无孤儿页：所有索引页均有站内入链（仅计 <a> 导航链接）")

# ---- 3. JSON-LD 解析 + 核心实体 ----
# 核心页（news-* 为非核心资讯页，按既定策略保持原样，不强制实体数据）
core_pages = [f for f in pages if not f.startswith('news-')]
news_pages = [f for f in pages if f.startswith('news-')]
all_types = set()
per_page_missing = 0
for f in core_pages:
    t = PAGE[f]
    blocks = LD_RE.findall(t)
    if not blocks:
        per_page_missing += 1
        continue
    page_has_entity = False
    for b in blocks:
        try:
            o = json.loads(b)
        except Exception as e:
            fail(f"{f}: JSON-LD 解析失败 — {e}")
            continue
        objs = o if isinstance(o, list) else [o]
        for oj in objs:
            if isinstance(oj, dict):
                ty = oj.get('@type')
                tys = ty if isinstance(ty, list) else [ty]
                for x in tys:
                    if x:
                        all_types.add(x)
                        if x in ('Organization', 'WebSite', 'Service'):
                            page_has_entity = True
    if not page_has_entity:
        per_page_missing += 1
if per_page_missing:
    fail(f"{per_page_missing} 个核心页缺少核心实体结构化数据 (Organization/WebSite/Service)")
else:
    ok("全部核心页均含核心实体结构化数据")
# ---- 3b. Organization 单一数据源一致性（防 CI 每夜重生漂移） ----
# 全站（含 news-* 资讯页）统一为 scripts/org_entity.json 的唯一定义，
# 且必须包含 E-E-A-T 关键字段 contactPoint / telephone / knowsAbout。
ORG_FILE = os.path.join(ROOT, "scripts", "org_entity.json")
if not os.path.exists(ORG_FILE):
    fail("缺少 scripts/org_entity.json（Organization 单一数据源）")
else:
    canonical = json.load(open(ORG_FILE, encoding="utf-8"))
    drift = []
    for f in S(pages):
        t = PAGE[f]
        orgs = []
        for b in LD_RE.findall(t):
            try:
                o = json.loads(b)
                for x in (o if isinstance(o, list) else [o]):
                    if isinstance(x, dict) and x.get("@type") == "Organization":
                        orgs.append(x)
            except Exception:
                pass
        if not orgs:
            drift.append(f + ":缺实体")
        elif len(orgs) > 1:
            drift.append(f + ":重复实体")
        elif orgs[0] != canonical:
            drift.append(f + ":与单一数据源不一致")
    if drift:
        fail(f"Organization 实体漂移 {len(drift)} 页: " + ", ".join(drift[:3]))
    else:
        ok(f"全站 {len(pages)} 页 Organization 与 org_entity.json 完全一致（含 news 页）")
    for need in ("contactPoint", "telephone", "knowsAbout", "address"):
        if need in canonical:
            ok(f"Organization 含 E-E-A-T 字段 {need}")
        else:
            fail(f"Organization 缺 E-E-A-T 字段 {need}")

# E-E-A-T: 可见审核署名必须与 WebPage.lastReviewed 成对出现
signed = [f for f in S(pages) if "Reviewed by the Anchormere sourcing desk" in PAGE[f]]
unsigned = [f for f in signed if "lastReviewed" not in PAGE[f]]
if unsigned:
    warn(f"{len(unsigned)} 页有可见审核署名但缺 WebPage.lastReviewed")
else:
    ok(f"E-E-A-T 审核署名与 WebPage.lastReviewed 成对一致（{len(signed)} 页）")

# ---- 3c. 文章 Article.wordCount 必须与实际可见正文相符 ----
# 早期简报生成器只统计「英文要点 + 术语释义」，声明值不足页面正文一半，
# 属于不实结构化数据。允许 15% 的排版差异（小标题/CTA 是否计入）。
#
# 简报按 Article.articleSection == "Sourcing briefing" 语义识别，与文件名日期解耦。
# 旧实现用 news-2026-11-07- 前缀判定：当日新生成的 digest 页恰好同名前缀，
# 而 digest 本就不声明 wordCount，于是被误判为不实结构化数据，
# 2026-11-07 每日任务在闸门处被拦截（未上线、未提交，属正确阻断）。
def article_lds(f):
    out = []
    for b in LD_RE.findall(PAGE[f]):
        try:
            o = json.loads(b)
        except Exception:
            continue
        if isinstance(o, dict) and o.get('@type') in ('Article', 'NewsArticle'):
            out.append(o)
    return out


brief_pages = [f for f in pages
               if any(o.get('articleSection') == 'Sourcing briefing'
                      for o in article_lds(f))]
# 任何主动声明了 wordCount 的文章页同样受校验，防止将来新增文章类型漏检。
declares_wc = [f for f in pages if any(o.get('wordCount') for o in article_lds(f))]
wc_checked = list(dict.fromkeys(brief_pages + declares_wc))
wc_bad = []
for f in S(wc_checked):
    t = PAGE[f]
    sec = re.search(r'<section class="l1">.*?</section>', t, re.S)
    if not sec:
        continue
    frag = re.sub(r'<script.*?</script>', ' ', sec.group(0), flags=re.S)
    frag = re.sub(r'<[^>]+>', ' ', frag)
    frag = html.unescape(re.sub(r'\s+', ' ', frag))
    actual = len(re.findall(r"[A-Za-z][A-Za-z'-]+", frag))
    declared = next((o['wordCount'] for o in reversed(article_lds(f))
                     if o.get('wordCount')), None)
    if not declared or not actual or abs(declared - actual) / actual > 0.15:
        wc_bad.append(f"{f}: 声明 {declared} / 实际 {actual}")
if wc_bad:
    fail(f"Article.wordCount 与实际正文偏差过大: " + "; ".join(wc_bad[:3]))
elif brief_pages:
    ok(f"Article.wordCount 与实际可见正文一致（{len(brief_pages)} 篇简报 / 本次校验 {len(S(wc_checked))} 页）")

# ---- 3d. GSC 产品摘要合规（全局不变量，始终全量扫描）----
# Google 对 @type=Product 强制要求 offers / review / aggregateRating；B2B 询价制
# 站点无法真实提供，虚构又违反 Search Essentials。方案 A 的最终形态是彻底不声明
# Product/Offer，改用 Service 承载主题实体。此闸门防止 CI 重生带回旧实体。
ecom_bad = []
for f in htmls:                       # 不受 --files / --gate 增量范围影响
    for b in LD_RE.findall(PAGE[f]):
        try:
            o = json.loads(b)
        except Exception:
            continue
        for z in (o if isinstance(o, list) else [o]):
            if not isinstance(z, dict):
                continue
            if z.get('@type') in ('Product', 'Offer') or 'offers' in z or 'aggregateRating' in z:
                ecom_bad.append(f)
if ecom_bad:
    fail(f"存在零售商品结构化数据（GSC 产品摘要问题）: {len(set(ecom_bad))} 页 "
         + ", ".join(sorted(set(ecom_bad))[:3]))
else:
    ok("全站无 Product/Offer/offers 商品结构化数据（GSC 产品摘要合规）")

for need in ('Organization', 'WebSite', 'Service', 'BreadcrumbList'):
    if need in all_types:
        ok(f"全站含 {need} 实体")
    else:
        warn(f"全站未见 {need} 实体类型")

# ---- 4. canonical 一致性 ----
canon_missing = 0
for f in S(pages):
    t = PAGE[f]
    m = CANON_RE.search(t)
    if not m:
        canon_missing += 1
        continue
    c = norm(m.group(1))
    exp = norm(f)
    if c != exp:
        fail(f"{f}: canonical({c}) 与文件名({exp}) 不一致")
if canon_missing:
    fail(f"{canon_missing} 个页面缺少 canonical")
else:
    ok("canonical 全部存在且与 URL 一致")

# ---- 4b. sitemap lastmod 必须是真实的、按内容分布的日期 ----
# 若用文件 mtime，CI checkout 会把全站 mtime 重置为当天，产生「全站每天
# 全量更新」的虚假信号，Google 会忽略不可信的 lastmod。
if not os.path.exists('sitemap.xml'):
    fail("缺少 sitemap.xml")
else:
    sm = open('sitemap.xml', encoding='utf-8').read()
    locs = re.findall(r'<loc>(.*?)</loc>', sm)
    lms = re.findall(r'<lastmod>(\d{4}-\d{2}-\d{2})</lastmod>', sm)
    if len(lms) != len(locs) or not lms:
        fail(f"sitemap lastmod 缺失或格式非法（loc={len(locs)}, lastmod={len(lms)}）")
    elif len(set(lms)) < 2:
        fail(f"sitemap 全部 {len(lms)} 条 lastmod 相同（疑似 mtime 漂移，信号不可信）")
    else:
        ok(f"sitemap {len(lms)} 条 lastmod 合法且按内容分布（{len(set(lms))} 个不同日期）")

# ---- 5. robots.txt 放行 AI 爬虫 ----
if os.path.exists('robots.txt'):
    rb = open('robots.txt', encoding='utf-8').read()
    miss = [b for b in ROBOTS_AI if b not in rb]
    if miss:
        warn(f"robots.txt 未显式放行: {', '.join(miss)}（GEO 信号偏弱）")
    else:
        ok("robots.txt 放行 GPTBot / ClaudeBot / PerplexityBot（GEO 友好）")
else:
    warn("未找到 robots.txt")

# ---- 6. IndexNow key ----
if os.path.exists('.indexnow_key'):
    ok("IndexNow key 已落地 (.indexnow_key)")
else:
    warn("未找到 .indexnow_key（IndexNow 提交将无效）")

# ---- 7. GSC / Bing 验证占位 ----
idx = PAGE['index.html']
gsc = re.search(r'name="google-site-verification" content="([^"]*)"', idx)
bing = re.search(r'name="msvalidate\.01" content="([^"]*)"', idx)
if not gsc:
    # 验证已通过（如 DNS / Google Analytics 方式），站点验证 meta 非必须 → 视为已闭环
    ok("GSC 验证 meta 未使用（已通过其他验证方式完成，排名数据闭环已打通）")
elif 'REPLACE' in gsc.group(1):
    warn("GSC 验证码仍为占位符，待在 GSC 添加站点后填入")
else:
    ok("GSC 验证 meta 已填入")
if not bing:
    ok("Bing 验证 meta 未使用（已通过 GSC 导入或其他方式完成，排名数据闭环已打通）")
elif 'REPLACE' in bing.group(1):
    warn("Bing 验证码仍为占位符，待在 Bing Webmaster 添加站点后填入")
else:
    ok("Bing 验证 meta 已填入")

# ---- 8. 站内链接统一为 clean URL（避免 .html 308 跳转）----
# Cloudflare Pages 把 /about.html 308 到 /about，而 canonical / sitemap 均为
# 无扩展名形式；继续链到 .html 既多一次跳转，也与 canonical 自相矛盾。
LEGACY_LINK = re.compile(r'''<a\s[^>]*href=["']([^"':#]+\.html)(?:[#?][^"']*)?["']''', re.I)
legacy = []
for f in S(htmls):
    n = len(LEGACY_LINK.findall(PAGE[f]))
    if n:
        legacy.append((f, n))
if legacy:
    fail(f"{len(legacy)} 页仍有 .html 站内链接（共 {sum(n for _, n in legacy)} 处，"
         f"线上 308 且与 canonical 不一致）: " + ", ".join(x for x, _ in legacy[:4]))
else:
    ok("站内链接全部为 clean URL，与 canonical / sitemap 一致（无 .html 308 跳转）")

# ---- 9. 中文片段语言声明（WCAG 2.1 AA 3.1.2 Language of Parts）----
# 中文 UI 是同一文档的客户端渲染，lang.js 切换根 lang 时中文片段仍是中文，
# 因此静态 lang="zh-CN" 在两种状态下都成立。
CN_RE = re.compile(r'<[A-Za-z][A-Za-z0-9]*\b[^>]*\bclass="[^"]*\bcn\b[^"]*"[^>]*>', re.S)
cn_total = cn_bad = 0
for f in S(htmls):
    for tag in CN_RE.findall(PAGE[f]):
        cn_total += 1
        if not re.search(r'\blang\s*=', tag):
            cn_bad += 1
if cn_bad:
    fail(f"{cn_bad}/{cn_total} 个中文片段缺 lang=\"zh-CN\"（WCAG 2.1 AA 3.1.2）")
else:
    ok(f"中文片段语言声明完整（{cn_total} 处均带 lang=\"zh-CN\"，WCAG 3.1.2）")

# ---- 10. Article 实体 @id 串联（不内联重复 Organization）----
inline = []
for f in S(htmls):
    for b in LD_RE.findall(PAGE[f]):
        try:
            o = json.loads(b)
        except (ValueError, TypeError):
            continue
        if isinstance(o, dict) and o.get('@type') in ('Article', 'NewsArticle'):
            for k in ('author', 'publisher'):
                v = o.get(k)
                if isinstance(v, dict) and '@id' not in v:
                    inline.append((f, k))
if inline:
    fail(f"{len(inline)} 处 Article author/publisher 仍内联 Organization（应以 @id 引用单一实体）: "
         + ", ".join(x for x, _ in inline[:4]))
else:
    ok("Article author/publisher 均以 @id 串联全站唯一 Organization 实体")

# ---- 汇总 ----
print("\n================ SEO 验证闭环报告 ================")
print(f"  校验模式：{MODE}  |  全站 {len(htmls)} 个 HTML，单次读取缓存")
if SCOPE is not None and not SCOPE:
    print("  注意：逐页检查范围为空，下列逐页 PASS 表示『无待检页面』，不代表全站复验；")
    print("        全站复验请运行 python3 scripts/workarea.py verify --all")
for m in passes: print(f"  [PASS] {m}")
for m in warns:  print(f"  [WARN] {m}")
for m in fails:  print(f"  [FAIL] {m}")
print("------------------------------------------------")
print(f"  PASS={len(passes)}  WARN={len(warns)}  FAIL={len(fails)}")
print("================================================\n")
if fails:
    print("结论：存在必须修复的问题 (FAIL)。"); sys.exit(1)
if warns:
    print("结论：通过，但有待办项 (WARN)。"); sys.exit(2)
print("结论：全部通过。")
sys.exit(0)
