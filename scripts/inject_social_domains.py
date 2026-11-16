#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌域名文字注入器 · 无图标 / 动态展示 / 数据驱动 / 可逆
===========================================================
对应 modules.json 的 social-domains 模块，制度说明见 WORKFLOW.md §10。

按用户要求：不使用任何平台图标、徽标、SVG 资源，不发起 fetch 或第三方请求。
footer 只放一个指向**本站自有域名首页**的文字链接，动态展示文字为品牌化写法
Anchormere.com；域名文字在初始 HTML 的占位内**静态可见**（爬虫 / 禁用 JS /
脚本加载失败都能看到），assets/social-domains.js 在页面加载过程中再从 <a href>
用 URL() 派生域名、做同源一致性校正并动态写入一次，<a href> 与 aria-label 恒为静态。

设计要点：
  1. 单一数据源 scripts/social_links.json；profiles 或 pages 为空时
     **连页面都不读取**，直接退出 —— 全站 HTML 零写盘、零 diff、零部署。
  2. 域名只从 href 派生（生成器用 urlparse，运行时 JS 用 URL()）；
     display 只承载品牌大小写，validate() 强制其与 href 同源，杜绝文案与链接失配。
  3. 占位锁定固定尺寸 + overflow:hidden + white-space:nowrap →
     动态写入等长文字不改变任何几何尺寸 → 0 CLS，不抢 LCP，零网络请求。
  4. 只处理 pages 白名单；protected 核心转化页默认跳过（需 allow_protected）。
  5. 幂等：BEGIN/END 标记块整段替换；内容相同经 io_util.write_final 跳过写盘。
  6. 可逆：清空配置后 --rollback 一键移除所有标记块与 script；同时清理
     历史 SOCIAL-ICONS 图标方案的残留痕迹（内置迁移，换模型不依赖聊天记录）。
"""
import os
import re
import sys
import json
import html as html_lib
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_util

ROOT = io_util.ROOT
CONFIG = os.path.join(ROOT, "scripts", "social_links.json")
SCRIPT_TAG = '<script defer src="assets/social-domains.js"></script>'
BEGIN = "<!-- SOCIAL-DOMAINS:BEGIN -->"
END = "<!-- SOCIAL-DOMAINS:END -->"
BLOCK_RE = re.compile(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", re.S)

# ---- 历史图标方案痕迹（内置迁移，保证旧页面一次替换干净、回滚字节一致）----
LEGACY_TAG = '<script defer src="assets/social-icons.js"></script>'
LEGACY_BLOCK_RE = re.compile(
    r"<!-- SOCIAL-ICONS:BEGIN -->.*?<!-- SOCIAL-ICONS:END -->\n?", re.S)

PROTECTED = {"index.html", "contact.html"}
PLACEHOLDER = ("YOUR_", "example.com", "example.org", "@handle", "REPLACE", "TODO")


def load_config():
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def host_of(href):
    try:
        return (urlparse(href).hostname or "").lower()
    except ValueError:
        return ""


def norm_host(s):
    """同源比对用：小写 + 去掉开头的 www.（不能用 lstrip，它是字符集删除）。"""
    v = (s or "").lower()
    return v[4:] if v.startswith("www.") else v


def display_of(p, host):
    """品牌化显示文字（如 Anchormere.com）；缺省回退到 hostname。"""
    return (p.get("display") or host).strip()


def rel_of(p):
    """自有域名首页链接不声称身份，默认不带 rel=me。"""
    r = (p.get("rel") or "noopener noreferrer").strip()
    if not re.fullmatch(r"[a-z ]+", r):
        return None
    if "noopener" not in r or "noreferrer" not in r:
        return None
    return r


def validate(profiles):
    errs = []
    for p in profiles:
        pid, href = p.get("id", ""), p.get("href", "")
        host = host_of(href)
        if not re.fullmatch(r"[a-z0-9-]+", pid or ""):
            errs.append("id 非法: %r" % pid)
        if not href.startswith("https://") or any(x in href for x in PLACEHOLDER):
            errs.append("href 缺失或为占位符: %r" % href)
        if not re.fullmatch(r"[a-z0-9.-]+", host or ""):
            errs.append("href 无法派生合法域名: %r" % href)
        disp = display_of(p, host)
        if not re.fullmatch(r"[A-Za-z0-9.-]+", disp or ""):
            errs.append("%s 的 display 含非法字符: %r" % (pid, disp))
        elif norm_host(disp) != norm_host(host):
            errs.append("%s 的 display 与 href 不同源: %r vs %r"
                        % (pid, disp, host))
        if not p.get("label"):
            errs.append("%s 缺 label" % pid)
        if rel_of(p) is None:
            errs.append("%s 的 rel 非法（须含 noopener / noreferrer）" % pid)
    return errs


def esc(v):
    return html_lib.escape(str(v), quote=True)


def render_block(profiles):
    links = []
    for p in profiles:
        href = p["href"]
        host = host_of(href)
        disp = display_of(p, host)
        zh = p.get("label_zh") or p["label"]
        zh_attrs = esc(json.dumps({"aria-label": zh}, ensure_ascii=False))
        width = len(disp) + 1                    # 锁定宽度，动态写入不产生 CLS
        links.append(
            '<a class="social-domain" href="%s" target="_blank" rel="%s" '
            'aria-label="%s" data-zh-attrs="%s" title="%s" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'margin:0 6px;vertical-align:middle;text-decoration:underline">'
            '<span data-domain-slot data-domain="%s" '
            'style="display:inline-flex;align-items:center;justify-content:center;'
            'width:%dch;height:24px;min-height:24px;max-height:24px;'
            'line-height:24px;overflow:hidden;white-space:nowrap">'
            '%s</span></a>'
            % (esc(href), esc(rel_of(p)), esc(p["label"]), zh_attrs,
               esc(disp), esc(disp), width, esc(disp))
        )
    return (BEGIN + "\n"
            + '<div class="social-domains" style="text-align:center;margin-top:12px;'
              'height:24px;min-height:24px;max-height:24px;line-height:24px;'
              'overflow:hidden">'
            + "".join(links) + "</div>\n" + END + "\n")


def strip_block(text):
    """清掉新旧两套标记块与 script 标签，回到未注入的原始状态。"""
    out = LEGACY_BLOCK_RE.sub("", BLOCK_RE.sub("", text))
    for tag in (SCRIPT_TAG, LEGACY_TAG):
        out = out.replace(tag + "\n", "").replace(tag, "")
    return out


def inject(text, block):
    if "</head>" not in text or "</footer>" not in text:
        return None
    text = strip_block(text)                   # 先迁移旧图标痕迹，再插入新块
    text = text.replace("</head>", SCRIPT_TAG + "\n</head>", 1)
    text = text.replace("</footer>", block + "</footer>", 1)
    return text


def target_pages(pages):
    if "*" in pages:
        return io_util.expand(["*.html"])
    out = []
    for p in pages:
        name = p if p.endswith(".html") else p + ".html"
        if os.path.isfile(os.path.join(ROOT, name)):
            out.append(name)
        else:
            print("  ! 白名单页面不存在，跳过:", name)
    return sorted(set(out))


def rollback():
    n = 0
    for name in io_util.expand(["*.html"]):
        if not io_util.selected(name):
            continue
        text = io_util.read_text(name)
        if BEGIN not in text and SCRIPT_TAG not in text \
                and "SOCIAL-ICONS:BEGIN" not in text and LEGACY_TAG not in text:
            continue
        if io_util.write_final(os.path.join(ROOT, name), strip_block(text)):
            n += 1
    print("social-domains rollback: %d 页还原（含历史图标痕迹清理）" % n)
    return 0


def main():
    c = load_config()
    profiles = c.get("profiles") or []
    pages = c.get("pages") or []

    if "--rollback" in sys.argv[1:]:
        return rollback()

    if not profiles or not pages:
        print("social-domains: 未启用（profiles/pages 为空）→ 零读取、零写盘")
        return 0

    errs = validate(profiles)
    if errs:
        print("social-domains: 配置校验失败，拒绝写盘：")
        for e in errs:
            print("  -", e)
        return 1

    allow_protected = bool(c.get("allow_protected"))
    block = render_block(profiles)
    names = target_pages(pages)
    changed = 0
    for name in names:
        if not io_util.selected(name):
            continue
        if name in PROTECTED and not allow_protected:
            print("  ! protected 核心页已跳过:", name)
            continue
        text = io_util.read_text(name)
        out = inject(text, block)
        if out is None:
            print("  ! 缺 </head> 或 </footer>，跳过:", name)
            continue
        if io_util.write_final(os.path.join(ROOT, name), out):
            changed += 1
    print("social-domains: %d 页写入 / %d 页白名单（品牌域名文字动态展示，零图标资源）"
          % (changed, len(names)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
