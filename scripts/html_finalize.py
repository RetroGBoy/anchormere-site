#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 最终态归一化（纯函数，无写盘、无 cwd 依赖）
================================================
把「每页都必须成立」的不变量集中到一处，供两类调用方共用：

  * 生成器：io_util.write_final() 在写盘前调用 normalize()，使产出即为最终态；
  * 兜底扫描：site_normalize.py 对全站做幂等检查。

由此消除历史架构里的「生成器输出中间态 → 再跑 normalize 改回」双重写盘：
以前单独重跑 longtail.py / build_briefings.py 会先写 38 个文件、再被改回，
现在单独重跑即零写盘。这是「没有问题的不做变动」的源头保证。

五条不变量：
  1. 站内 <a href> 用 clean URL（/about），与 canonical / sitemap 一致（避免 308）。
  2. 中文片段标 lang="zh-CN"（WCAG 2.1 AA 3.1.2）。
  3. Article / NewsArticle 的 author、publisher 用 @id 串联唯一 Organization。
  4. meta keywords ≤200 字符：Google 忽略该标签，超长只增加关键词堆砌观感；
     按逗号词边界收敛，零关键词损失（LSI 词仍在正文 / FAQ / 结构化数据里）。
  5. FAQPage 带 speakable：把语音助手与答案引擎指向页面里真实存在的问答 DOM。
     长尾页有 .qa 问答块，早期框架页的 FAQ 问题落在 h3，选择器按页面自适应。

放在收口层而非各生成器里的原因：任何新生成器、手写页、CI 重生都必然经过
write_final / site_normalize，因此不变量不可能被「重生带回旧模板」绕过。
"""
import os
import re
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_HERE, "org_entity.json"), encoding="utf-8") as _fh:
    ORG_ID = json.load(_fh)["@id"]

HREF_ATTR = re.compile(r'(href\s*=\s*)(["\'])([^"\']*)(\2)')
REL_HTML = re.compile(r'^([A-Za-z0-9_][A-Za-z0-9_.-]*)\.html((?:[#?].*)?)$')
CN_TAG = re.compile(r'(<[A-Za-z][A-Za-z0-9]*\b[^>]*\bclass="[^"]*\bcn\b[^"]*"[^>]*?)(>)', re.S)
LD_BLOCK = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)
# 全站生成器统一输出 <meta name="keywords" content="...">；属性用双引号。
META_KW = re.compile(r'(<meta\s+name="keywords"\s+content=")([^"]*)(")', re.I)
KW_MAX = 200


def _href_repl(m):
    val = m.group(3)
    hit = REL_HTML.match(val)
    if not hit:
        return m.group(0)
    slug, suffix = hit.group(1), hit.group(2)
    clean = "/" if slug == "index" else "/" + slug
    return m.group(1) + m.group(2) + clean + suffix + m.group(4)


def _cn_repl(m):
    tag = m.group(1)
    if re.search(r'\blang\s*=', tag):
        return m.group(0)
    return tag.rstrip() + ' lang="zh-CN"' + m.group(2)


def _clip_keywords(val):
    """按逗号词边界收敛到 KW_MAX；不产生半截词、不留尾部逗号。幂等。"""
    if len(val) <= KW_MAX:
        return val
    parts = [p.strip() for p in val.split(",") if p.strip()]
    out = []
    for p in parts:
        if len(", ".join(out + [p])) > KW_MAX:
            break
        out.append(p)
    if out:
        return ", ".join(out)
    head = val[:KW_MAX]
    return (head.rsplit(" ", 1)[0] if " " in head else head).rstrip(",; ")


def _kw_repl(m):
    val = _clip_keywords(m.group(2))
    return m.group(0) if val == m.group(2) else m.group(1) + val + m.group(3)


def _ld_repl(m, has_qa):
    try:
        obj = json.loads(m.group(2))
    except (ValueError, TypeError):
        return m.group(0)
    if not isinstance(obj, dict):
        return m.group(0)
    t = obj.get("@type")
    if t == "FAQPage" and "speakable" not in obj:
        obj["speakable"] = {
            "@type": "SpeakableSpecification",
            "cssSelector": [".qa h3", ".qa p"] if has_qa else ["h3"],
        }
        return m.group(1) + json.dumps(obj, ensure_ascii=False) + m.group(3)
    if t not in ("Article", "NewsArticle"):
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
    """幂等：normalize(normalize(x)) == normalize(x)。"""
    text = HREF_ATTR.sub(_href_repl, text)
    text = CN_TAG.sub(_cn_repl, text)
    text = META_KW.sub(_kw_repl, text)
    has_qa = 'class="qa"' in text
    text = LD_BLOCK.sub(lambda m: _ld_repl(m, has_qa), text)
    return text
