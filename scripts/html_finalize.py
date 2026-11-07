#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML 最终态归一化（纯函数，无写盘、无 cwd 依赖）
================================================
把三条「每页都必须成立」的不变量集中到一处，供两类调用方共用：

  * 生成器：io_util.write_final() 在写盘前调用 normalize()，使产出即为最终态；
  * 兜底扫描：site_normalize.py 对全站做幂等检查。

由此消除历史架构里的「生成器输出中间态 → 再跑 normalize 改回」双重写盘：
以前单独重跑 longtail.py / build_briefings.py 会先写 38 个文件、再被改回，
现在单独重跑即零写盘。这是「没有问题的不做变动」的源头保证。

三条不变量：
  1. 站内 <a href> 用 clean URL（/about），与 canonical / sitemap 一致（避免 308）。
  2. 中文片段标 lang="zh-CN"（WCAG 2.1 AA 3.1.2）。
  3. Article / NewsArticle 的 author、publisher 用 @id 串联唯一 Organization。
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
    """幂等：normalize(normalize(x)) == normalize(x)。"""
    text = HREF_ATTR.sub(_href_repl, text)
    text = CN_TAG.sub(_cn_repl, text)
    text = LD_BLOCK.sub(_ld_repl, text)
    return text
