#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新闻稿 / 引用页「原文权威性」注入器 · 幂等 / 可逆 / 数据驱动
============================================================
对应 modules.json 的 engine 模块（scripts/*.py 已被 glob 覆盖）。

需求：语言置换时，新闻稿与引用页要保持原来的权威性。
实现（与 lang.js 配套）：
  1) 权威页 <body> 带 data-lang-default="en" → 首访默认英文原文，
     不因中文地区自动切中文；用户仍可主动点切换器看中文正文。
  2) 来源标题 / 来源列表 / 全部外链锚文本带 data-keep-en →
     lang.js 在 applyLang() 中跳过，机构名、专有名词、引用原句、
     Source URL 在任何语言下都保持英文原文，可独立核验。
  3) 正文叙述仍可切中文（data-zh 不变），即「正文可译、来源不译」。

权威页判定（内容特征驱动，无需维护白名单，换模型仍然有效）：
  - 文件名以 news-20 开头（新闻稿 / 简报），或
  - 正文含 "Source URL:" / "Sources & references"（公开来源编辑性引用页）。

幂等：属性已存在则不写；内容不变时 io_util.write_final 跳过写盘。
可逆：--rollback 移除 data-lang-default 与所有 data-keep-en。
CI：news-auto.yml 在 Normalize 之后调用，每日新生成的新闻页自动补齐。
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_util

ROOT = io_util.ROOT
DEFAULT_ATTR = 'data-lang-default="en"'
KEEP_ATTR = "data-keep-en"

BODY_RE = re.compile(r"<body\b[^>]*>", re.I)
HEAD_BLOCK_RE = re.compile(r"<(h2|h3)\b([^>]*)>(.*?)</\1>", re.I | re.S)
# 来源区标题有多种写法：新闻稿 "Sources & references"；PCB 枢纽
# "Public sources, figures & boundaries" / "Public sources & references ..."。
# 只认「sources + references/figures/boundaries/urls」，避免误锁
# "Why source the chain, not just a board" 这类正文标题。
SRC_HEAD_RE = re.compile(r"sources.{0,60}?(?:references|figures|boundaries|urls)", re.I | re.S)
SRC_RE = re.compile(r"Sources\s*(?:&amp;|&)\s*references", re.I)
LIST_RE = re.compile(r"<(ol|ul)\b([^>]*)>", re.I)
EXT_A_RE = re.compile(r'<a\b([^>]*\bhref="https?://[^"]*"[^>]*)>', re.I)

# 站点自有域名块 / WhatsApp 按钮不是「来源引用」，且域名块由
# inject_social_domains.py 幂等重渲染（会覆盖任何附加属性）。若给它们打标，
# 两个注入器会互相覆盖、每次复跑都写盘，破坏幂等性 —— 必须排除。
NON_SOURCE_MARKERS = (
    "social-domain", "wa-float", "https://anchormere.com/", "https://wa.me/",
)


def is_authority(name, text):
    if name.startswith("news-20"):
        return True
    if "Source URL:" in text:
        return True
    return bool(SRC_RE.search(text))


def _add_attr(tag, attr):
    """给一个开始标签追加属性（tag 以 '>' 结尾），已有则原样返回。"""
    if attr in tag:
        return tag
    return tag[:-1].rstrip() + " " + attr + ">"


def set_body_default(text):
    m = BODY_RE.search(text)
    if not m or DEFAULT_ATTR in m.group(0):
        return text
    return text[:m.start()] + _add_attr(m.group(0), DEFAULT_ATTR) + text[m.end():]


def mark_sources_heading(text):
    """来源区标题（h2 / h3 多种写法）与其后首个 ol/ul 列表加 data-keep-en。"""
    def repl(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if not SRC_HEAD_RE.search(inner):
            return m.group(0)
        if KEEP_ATTR in attrs:
            return m.group(0)
        return "<%s%s %s>%s</%s>" % (tag, attrs.rstrip(), KEEP_ATTR, inner, tag)
    out = HEAD_BLOCK_RE.sub(repl, text)
    m = SRC_HEAD_RE.search(out)
    if m:
        lst = LIST_RE.search(out, m.end())
        if lst and KEEP_ATTR not in lst.group(0):
            out = out[:lst.start()] + _add_attr(lst.group(0), KEEP_ATTR) + out[lst.end():]
    return out


def mark_external_links(text):
    def repl(m):
        tag, attrs = m.group(0), m.group(1)
        if any(x in tag for x in NON_SOURCE_MARKERS):
            # 顺带清除历史残留，保证从旧状态也能一次收敛到幂等终态
            return tag.replace(" " + KEEP_ATTR, "")
        if KEEP_ATTR in attrs:
            return tag
        return "<a%s %s>" % (attrs.rstrip(), KEEP_ATTR)
    return EXT_A_RE.sub(repl, text)


def apply(text):
    text = set_body_default(text)
    text = mark_sources_heading(text)
    text = mark_external_links(text)
    return text


def rollback(text):
    text = re.sub(r"\s+" + re.escape(DEFAULT_ATTR), "", text)
    text = re.sub(r"\s+" + KEEP_ATTR, "", text)
    return text


def main():
    do_rollback = "--rollback" in sys.argv[1:]
    names = io_util.expand(["*.html"])
    changed = authority = 0
    for name in names:
        if not io_util.selected(name):
            continue
        text = io_util.read_text(name)
        auth = is_authority(os.path.basename(name), text)
        if auth:
            authority += 1
            out = rollback(text) if do_rollback else apply(text)
        else:
            # 曾被打标、但已不再是权威页 → 清理，避免残留
            out = rollback(text) if (KEEP_ATTR in text or DEFAULT_ATTR in text) else text
        if io_util.write_final(os.path.join(ROOT, name), out):
            changed += 1
    act = "还原" if do_rollback else "权威性标记"
    print("lang-authority: %s → %d 页写入 / %d 个权威页 / %d 页扫描"
          % (act, changed, authority, len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
