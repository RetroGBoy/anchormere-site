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
import os as _wa_os, sys as _wa_sys
_wa_sys.path.insert(0, _wa_os.path.dirname(_wa_os.path.abspath(__file__)))
import io_util  # workarea: write_if_changed / selected
import re
import json
import sys
import glob

import html_finalize  # 纯函数归一化：与生成器共用同一套最终态规则
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

normalize = html_finalize.normalize


def main():
    check_only = "--check" in sys.argv
    files = sorted(glob.glob("*.html"))
    changed, total = [], 0
    for fn in files:
        if not io_util.selected(fn):
            continue
        old = open(fn, encoding="utf-8").read()
        new = normalize(old)
        total += 1
        if new != old:
            changed.append(fn)
            if not check_only:
                io_util.write_if_changed(fn, new)
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
