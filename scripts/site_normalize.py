#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全站 HTML 规范化（幂等，单一数据源）
====================================
把三条「每页都必须成立」的不变量集中到一处处理，包括 CI 每夜重新生成的页面：

  1. 站内 <a href> 使用 clean URL（/about），与 canonical、sitemap 一致。
     Cloudflare Pages 会把 /about.html 308 到 /about；继续链到 .html 形式
     会多一次跳转，且与无扩展名 canonical 自相矛盾。
  2. 中文片段标注 lang="zh-CN"（WCAG 2.1 AA 3.1.2 Language of Parts）。
     中文 UI 是同一文档的客户端渲染，lang.js 把根 lang 切到 zh-CN 时
     这些片段仍是中文，不冲突。
  3. Article / NewsArticle 的 author、publisher 用 @id 引用唯一的
     Organization 节点（读取 scripts/org_entity.json），不再内联重复对象，
     让结构化数据实体图真正串联。

用法：
  python3 scripts/site_normalize.py            # 规范化根目录所有 *.html
  python3 scripts/site_normalize.py --check   # 只报告，需要改动时退出码 1

脚本只在内容实际变化时写文件，重复运行不产生 diff（可安全接入 CI）。
"""
import os
import re
import json
import sys
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# Organization 的 @id 由全站唯一数据源提供，不硬编码。
ORG_FILE = os.path.join("scripts", "org_entity.json")
with open(ORG_FILE, encoding="utf-8") as fh:
    ORG_ID = json.load(fh)["@id"]

# href="xxx.html" / href='xxx.html#' —— 只处理站内相对文件名，外链、锚点、
# mailto/tel/协议相对 URL 一律跳过。
HREF_ATTR = re.compile(r'(href\s*=\s*)(["\'])([^"\']*)(\2)')
REL_HTML = re.compile(r'^([A-Za-z0-9_][A-Za-z0-9_.-]*)\.html((?:[#?].*)?)$')

# 带 class="cn" 的开标签（p / span / div / li / …）。
CN_TAG = re.compile(r'(<[A-Za-z][A-Za-z0-9]*\b[^>]*\bclass="[^"]*\bcn\b[^"]*"[^>]*?)(>)', re.S)

LD_BLOCK = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def _href_repl(m):
    val = m.group(3)
    hit = REL_HTML.match(val)
    if not hit:
        return m.group(0)
    slug, suffix = hit.group(1), hit.group(2)
    # 首页用根 URL，其余用 /<slug>；保留 #锚点 与 ?query。
    clean = "/" if slug == "index" else "/" + slug
    return m.group(1) + m.group(2) + clean + suffix + m.group(4)


def _cn_repl(m):
    tag = m.group(1)
    if re.search(r'\blang\s*=', tag):
        return m.group(0)
    return tag.rstrip() + ' lang="zh-CN"' + m.group(2)


def _ld_repl(m):
    try:
        obj = json.loads(m.group(2))
    except (ValueError, TypeError):
        return m.group(0)
    if not isinstance(obj, dict) or obj.get("@type") not in ("Article", "NewsArticle"):
        return m.group(0)
    changed = False
    for key in ("author", "publisher"):
        v = obj.get(key)
        if isinstance(v, dict) and v.get("@type") == "Organization":
            obj[key] = {"@id": ORG_ID}
            changed = True
    if not changed:
        return m.group(0)
    return m.group(1) + json.dumps(obj, ensure_ascii=False) + m.group(3)


def normalize(text):
    text = HREF_ATTR.sub(_href_repl, text)
    text = CN_TAG.sub(_cn_repl, text)
    text = LD_BLOCK.sub(_ld_repl, text)
    return text


def main():
    check_only = "--check" in sys.argv
    files = sorted(glob.glob("*.html"))
    changed, total = [], 0
    for fn in files:
        old = open(fn, encoding="utf-8").read()
        new = normalize(old)
        total += 1
        if new != old:
            changed.append(fn)
            if not check_only:
                open(fn, "w", encoding="utf-8").write(new)
    print(f"[site_normalize] 扫描 {total} 个页面，"
          f"{'需要规范化' if check_only else '已规范化'} {len(changed)} 个")
    if changed and len(changed) <= 15:
        for f in changed:
            print("   -", f)
    if check_only and changed:
        print("[site_normalize] 存在未规范化页面，请先运行 python3 scripts/site_normalize.py")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
