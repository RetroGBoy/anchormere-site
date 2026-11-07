#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块化增量工作区 · 共享 IO 约束（制度层，不依赖任何模型或会话记忆）
================================================================
本模块是「没有问题的不做变动 / 没有需求的不用重新扫描」两条纪律的物理保证：

1. write_if_changed() —— 所有生成器写盘的唯一入口。内容字节相同则不写盘，
   因此不产生 mtime 漂移、不产生 git diff、不触发 Cloudflare Pages 重新部署，
   也不会污染 sitemap 的 lastmod 信号。任何新接手的模型只要沿用此函数，
   就自动遵守「无变更不落盘」，无需读懂历史对话。

2. selected() —— 生成器循环的范围闸门。workarea.py 通过环境变量
   WORKAREA_FILES 下发本次允许处理的文件名，生成器在循环开头调用本函数，
   范围外的文件连读取都不发生，实现「没有需求的不用重新扫描」。
   未设置环境变量时返回 True（兼容单独手动运行脚本 = 全量）。

3. 内容哈希工具 —— 状态快照与脏判定基于文件内容，而非 mtime。
   mtime 在 CI checkout 后会全站重置，不能作为跨机器/跨模型的判据。
"""
import os
import hashlib
import glob as _glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILES = "WORKAREA_FILES"


# ---------------------------------------------------------------- 哈希
def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    """文件内容 sha256；不存在返回 None。二进制安全。"""
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None


def digest_paths(paths, root=ROOT):
    """一组路径的聚合哈希：与顺序无关，缺失文件以 '-' 占位参与计算。"""
    items = []
    for p in paths:
        ap = p if os.path.isabs(p) else os.path.join(root, p)
        items.append((os.path.relpath(ap, root).replace(os.sep, "/"),
                      file_hash(ap) or "-"))
    items.sort()
    body = "".join(f"{n}:{h}\n" for n, h in items)
    return sha256_text(body)


# ---------------------------------------------------------------- 范围闸门
def _allowed():
    raw = os.environ.get(ENV_FILES, "").strip()
    if not raw:
        return None
    out = set()
    for tok in raw.replace(";", ",").split(","):
        tok = tok.strip()
        if not tok:
            continue
        out.add(tok)
        if tok.endswith(".html"):
            out.add(tok[:-5])
        else:
            out.add(tok + ".html")
    return out


def selected(name):
    """生成器在遍历文件前调用；返回 True 才处理该文件。

    name 可为 'about.html'、'about' 或任意路径（取 basename 比较）。
    """
    allow = _allowed()
    if allow is None:
        return True
    base = os.path.basename(name)
    return base in allow


def selection_size():
    allow = _allowed()
    return None if allow is None else len(allow)


# ---------------------------------------------------------------- 幂等写盘
def write_if_changed(path, text, encoding="utf-8"):
    """仅当内容变化时写盘。返回 True 表示实际写入，False 表示跳过。"""
    try:
        with open(path, "r", encoding=encoding) as f:
            if f.read() == text:
                return False
    except (FileNotFoundError, UnicodeDecodeError):
        pass
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(text)
    return True


def write_final(path, text, encoding="utf-8"):
    """生成器写 HTML 的统一入口：先归一化为最终态，再幂等写盘。

    历史问题：生成器输出的是「中间态」（含 .html 内链、缺 lang、内联实体），
    必须靠后续 site_normalize.py 改回，导致单独重跑生成器会先写 N 个文件、
    再被改回，产生双重写盘与 mtime 漂移。这里把归一化前置到写盘之前，
    使生成器产出即为线上最终态 —— 内容不变时连一次写盘都不发生。
    """
    import html_finalize
    return write_if_changed(path, html_finalize.normalize(text), encoding)


def write_bytes_if_changed(path, data):
    try:
        with open(path, "rb") as f:
            if f.read() == data:
                return False
    except FileNotFoundError:
        pass
    with open(path, "wb") as f:
        f.write(data)
    return True


# ---------------------------------------------------------------- 文件展开
def expand(patterns, root=ROOT):
    """把 glob 列表展开成相对 root 的、去重排序后的真实文件路径。"""
    out = set()
    for pat in patterns:
        for p in _glob.glob(os.path.join(root, pat), recursive=True):
            if os.path.isfile(p):
                out.add(os.path.relpath(p, root).replace(os.sep, "/"))
    return sorted(out)


def read_text(rel_path, root=ROOT):
    with open(os.path.join(root, rel_path), "r", encoding="utf-8") as f:
        return f.read()
