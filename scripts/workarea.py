#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模块化增量工作区驱动器（workarea）
==================================
把「分板块更新、无变更不动、无需求不扫描、换模型照常运行」从口头约定
变成可执行的仓库内制度。所有判断只依赖三个仓库文件：
  scripts/modules.json        模块分区与依赖（唯一事实来源）
  scripts/module_state.json   内容哈希基线（纳入 git，跨机器/跨模型继承）
  WORKFLOW.md                 人类/模型交接协议

命令：
  status    [--deep] [--include-frozen]          查看模块状态（默认零内容读取）
  plan      [--module ID]... [--change FILE]... [--all] [--include-scheduled]
                                                 输出影响范围，不执行
  apply     [同上] [--dry-run]                   只重建受影响模块 + 只校验脏模块
  verify    [--module ID]... [--all] [--gate]    增量校验（--gate 时即使无变更也跑全局不变量）
  init                                          写入/刷新内容哈希基线（须先 verify --all PASS）
  audit                                         校验注册表自洽与文件归属覆盖率
  freeze ID / unfreeze ID                       临时冻结/解冻模块
  handoff                                       打印新模型/新会话接手检查单
"""
import os
import sys
import json
import subprocess
import argparse
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import io_util as io

ROOT = io.ROOT
REG_PATH = os.path.join(ROOT, "scripts", "modules.json")
STATE_PATH = os.path.join(ROOT, "scripts", "module_state.json")
STATE_REL = "scripts/module_state.json"

# 状态文件自身不参与哈希，否则每次写状态都会把自己的模块判为 DIRTY，形成死循环。
HASH_EXEMPT = {STATE_REL}
EXCLUDE_DIRS = {".git", "__pycache__", ".codebuddy", "node_modules", ".venv"}
EXCLUDE_FILES = {".gitignore", ".DS_Store"}


def now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()


def load_reg():
    with open(REG_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if not os.path.exists(STATE_PATH):
        return {"version": 1, "generated_at": None, "head": None,
                "modules": {}, "overrides": {"frozen": []}}
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_state(st):
    """幂等：只有模块哈希/验证结论实质变化时才写盘。

    若每次都刷新 generated_at / head，CI 在没有新内容时也会产生 diff，
    进而触发一次空提交与无意义部署 —— 与「无变更不落盘」相悖。
    """
    st["version"] = 1
    st["head"] = git_head()

    def core(d):
        return {k: v for k, v in d.items() if k not in ("generated_at", "head")}

    existing = None
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, encoding="utf-8") as f:
                existing = json.load(f)
        except (ValueError, OSError):
            pass
    if existing is not None and core(existing) == core(st):
        return False
    st["generated_at"] = now()
    text = json.dumps(st, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    io.write_if_changed(STATE_PATH, text)
    return True


# ------------------------------------------------------------------ git
def git(*args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=ROOT,
                           capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def git_head():
    return git("rev-parse", "--short", "HEAD") or "unknown"


def git_changed():
    """返回工作区相对仓库根有变动的文件集合；非 git 环境返回 None（触发深扫）。"""
    # core.quotePath=false：否则中文/非 ASCII 文件名会被 git 转成八进制转义并加引号，
    # git_changed() 拿到的路径与 walk_files() 的 Unicode 路径对不上，中文文档改动
    # 会永远显示为 CLEAN（换模型接手时会漏判）。此开关对该子命令局部生效。
    out = git("-c", "core.quotePath=false", "status", "--porcelain", "--untracked-files=all")
    if out is None:
        return None
    if out == "":
        return set()
    paths = set()
    for line in out.splitlines():
        p = line[3:] if len(line) > 3 else ""
        if " -> " in p:
            p = p.split(" -> ", 1)[1]
        p = p.strip().strip('"')
        if p:
            paths.add(p.replace(os.sep, "/"))
    return paths


# ------------------------------------------------------------------ 归属
def walk_files():
    out = []
    for base, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fn in files:
            if fn in EXCLUDE_FILES or fn.endswith(".pyc"):
                continue
            rel = os.path.relpath(os.path.join(base, fn), ROOT).replace(os.sep, "/")
            out.append(rel)
    return sorted(out)


def assign(reg):
    """自上而下先到先得分配文件归属。返回 (map, unassigned)。"""
    allf = walk_files()
    remaining = set(allf)
    amap = {}
    for m in reg["modules"]:
        cand = set()
        for p in m.get("paths", []):
            # 显式声明的路径始终归属本模块，即使文件尚未落盘。
            # 新增页场景下注册表先写入 slug、生成器随后创建文件；若这里要求
            # 文件已存在，新页会被挡在 WORKAREA_FILES 之外，导致「只重建旧页」。
            cand.add(p)
        for p in io.expand(m.get("globs", [])):
            if p in remaining:
                cand.add(p)
        amap[m["id"]] = sorted(cand)
        remaining -= cand
    return amap, sorted(remaining - HASH_EXEMPT)


def mod_by_id(reg):
    return {m["id"]: m for m in reg["modules"]}


def effective_policy(m, st):
    if m["id"] in st.get("overrides", {}).get("frozen", []):
        return "frozen"
    return m["policy"]


def hashable(files):
    return [f for f in files if f not in HASH_EXEMPT]


def module_hash(files):
    return io.digest_paths(hashable(files))


# ------------------------------------------------------------------ status
def compute_status(reg, st, deep=False, include_frozen=False):
    amap, _ = assign(reg)
    changed = None if deep else git_changed()
    # state 随代码一起提交，所以提交后基线必然落后正好 1 个 commit，属正常。
    # 只有落后多个（期间有别人/别的模型连续提交）或无法判定时才提示深扫。
    base = st.get("head")
    out = git("rev-list", "--count", f"{base}..HEAD") if base and base != "unknown" else None
    try:
        dist = int(out) if out is not None else None
    except (TypeError, ValueError):
        dist = None
    drift = dist is None or dist > 1
    rows = []
    for m in reg["modules"]:
        files = amap[m["id"]]
        pol = effective_policy(m, st)
        if pol == "frozen" and not include_frozen:
            rows.append(dict(id=m["id"], policy=pol, files=len(files),
                             state="SKIP", dirty=False, hash=None,
                             verified=st["modules"].get(m["id"], {}).get("verified_at"),
                             note="frozen：不计哈希、不扫描"))
            continue
        rec = st["modules"].get(m["id"])
        touched = changed is None or bool(set(hashable(files)) & changed)
        h = module_hash(files) if (deep or touched or not rec) else None
        if not rec:
            state, dirty = "NEW", True
        elif h is None:
            state, dirty = "CLEAN", False
        elif h != rec.get("hash"):
            state, dirty = "DIRTY", True
        else:
            state, dirty = "CLEAN", False
        rows.append(dict(id=m["id"], policy=pol, files=len(files),
                         state=state, dirty=dirty, hash=h,
                         verified=rec.get("verified_at") if rec else None,
                         note=m["title"]))
    return rows, drift, unassigned_of(reg)


def unassigned_of(reg):
    return assign(reg)[1]


def cmd_status(a):
    reg, st = load_reg(), load_state()
    rows, drift, unassigned = compute_status(reg, st, a.deep, a.include_frozen)
    print("\n=========== 模块工作区状态 ===========")
    print(f"  HEAD={git_head()}  基线={st.get('head') or '未建立'}"
          f"  模式={'深扫(内容哈希)' if a.deep else '快判(git diff, 零内容读取)'}")
    if drift and not a.deep:
        print("  [提示] 基线落后多个提交或无法判定（换机器/换模型/他人连续提交），建议先跑 status --deep 复核。")
    print(f"  {'模块':<17}{'策略':<12}{'文件':>5}  {'状态':<7} 上次验证")
    print("  " + "-" * 74)
    for r in rows:
        print(f"  {r['id']:<17}{r['policy']:<12}{r['files']:>5}  {r['state']:<7} {r['verified'] or '-'}")
    dirty = [r["id"] for r in rows if r["dirty"]]
    print("  " + "-" * 74)
    print(f"  脏模块：{', '.join(dirty) if dirty else '无（全站干净，无需扫描/重建）'}")
    if unassigned:
        print(f"  [WARN] 未归属文件 {len(unassigned)} 个：{', '.join(unassigned[:6])}")
        print("         请在 scripts/modules.json 补入对应模块，否则增量制度存在盲区。")
    print("  提示：status 默认不读取任何页面内容；--deep 强制内容哈希复核。\n")
    return 1 if unassigned and reg.get("unassigned_is_error") else 0


# ------------------------------------------------------------------ plan
def closure(reg, seeds, include_scheduled=False):
    """沿 invalidates 做依赖闭包；返回 (受影响模块集合, 人工复核集合, 是否需全局校验)。"""
    byid = mod_by_id(reg)
    seen, review = set(), set()
    force_global = False
    queue = list(seeds)
    while queue:
        mid = queue.pop(0)
        if mid in seen or mid not in byid:
            continue
        seen.add(mid)
        m = byid[mid]
        force_global = force_global or bool(m.get("force_global"))
        review.update(m.get("review", []))
        for nxt in m.get("invalidates", []):
            if nxt not in seen:
                queue.append(nxt)
    return seen, sorted(review), force_global


def topo_order(affected, byid):
    """按 invalidates 做拓扑排序：上游先于下游。

    典型场景：longtail -> config。必须先生成全部长尾页面，再重建 sitemap，
    否则 sitemap 的 lastmod 取到的是上一版页面。字母序会把 config 排到前面，
    因此这里必须按依赖入度排序。
    """
    indeg = {m: 0 for m in affected}
    for m in affected:
        for nxt in byid.get(m, {}).get("invalidates", []):
            if nxt in affected:
                indeg[nxt] += 1
    ready = sorted(m for m in affected if indeg[m] == 0)
    out = []
    while ready:
        m = ready.pop(0)
        out.append(m)
        for nxt in byid.get(m, {}).get("invalidates", []):
            if nxt in affected:
                indeg[nxt] -= 1
                if indeg[nxt] == 0:
                    ready.append(nxt)
        ready.sort()
    out += sorted(m for m in affected if m not in out)  # 环兜底
    return out


def resolve_targets(a, reg, st):
    byid = mod_by_id(reg)
    amap, _ = assign(reg)
    seeds = set()
    if a.all:
        seeds = {m["id"] for m in reg["modules"]
                 if effective_policy(m, st) != "frozen"}
    if a.module:
        for mid in a.module:
            if mid not in byid:
                print(f"[ERROR] 未知模块 id: {mid}（见 scripts/modules.json）")
                sys.exit(2)
            seeds.add(mid)
    if a.change:
        path2mod = {}
        for mid, files in amap.items():
            for f in files:
                path2mod[f] = mid
                path2mod[os.path.basename(f)] = mid
        for c in a.change:
            mid = path2mod.get(c) or path2mod.get(os.path.basename(c))
            if not mid:
                print(f"[WARN] 变更文件 {c} 未归属任何模块，已忽略（请补注册表）")
            else:
                seeds.add(mid)
    if not seeds:
        rows, _, _ = compute_status(reg, st)
        seeds = {r["id"] for r in rows if r["dirty"]}
    return seeds


def build_plan(a, reg, st):
    seeds = resolve_targets(a, reg, st)
    affected, review, force_global = closure(reg, seeds)
    byid = mod_by_id(reg)
    amap, _ = assign(reg)
    rebuild, verify_mods, skipped = [], [], []
    protected = set(reg["protected"]["paths"])
    for mid in topo_order(affected, byid):
        m = byid[mid]
        pol = effective_policy(m, st)
        if pol == "frozen":
            skipped.append((mid, "frozen：不计哈希、不扫描"))
            continue
        explicit = a.all or a.include_scheduled or mid in (a.module or [])
        if pol == "scheduled" and not explicit:
            # 无新需求：不自动重建（避免意外联网抓取历史新闻）。
            # 但若这个模块自身变脏了，仍要纳入本次校验，不能漏检。
            skipped.append((mid, "scheduled：无新需求，不自动重建"))
            if mid in seeds:
                verify_mods.append(mid)
            continue
        if m.get("build") and (mid in seeds or pol in ("auto", "config")):
            rebuild.append(mid)
        if m.get("verify_default") or mid in seeds:
            verify_mods.append(mid)
    verify_files = sorted({f for mid in verify_mods for f in amap[mid]
                           if f.endswith(".html")})
    return dict(seeds=sorted(seeds), affected=sorted(affected), review=review,
                force_global=force_global, rebuild=rebuild,
                verify_mods=verify_mods, verify_files=verify_files,
                skipped=skipped, protected=sorted(protected), amap=amap)


def print_plan(p, reg):
    byid = mod_by_id(reg)
    print("\n=========== 增量执行计划 ===========")
    print(f"  声明模块   : {', '.join(p['seeds']) or '（自动发现：无脏模块）'}")
    print(f"  依赖闭包   : {', '.join(p['affected']) or '无'}")
    print(f"  将重建     : {', '.join(p['rebuild']) or '无'}")
    for mid in p["rebuild"]:
        print(f"      └─ {byid[mid]['build']}")
    print(f"  将校验({len(p['verify_files'])} 页): {', '.join(p['verify_mods']) or '无'}")
    print(f"  人工复核   : {', '.join(p['review']) or '无'}（只读提示，不自动改写）")
    print(f"  校验级别   : {'全量复验（engine / 实体 / 资源强依赖变更）' if p['force_global'] else '增量局部 + 全局不变量'}")
    for mid, why in p["skipped"]:
        print(f"  跳过       : {mid} — {why}")
    print(f"  受保护     : {', '.join(p['protected'])}（自动流程禁止写入）")
    print("====================================\n")


def cmd_plan(a):
    reg, st = load_reg(), load_state()
    print_plan(build_plan(a, reg, st), reg)
    return 0


# ------------------------------------------------------------------ 执行
def run_build(m, files, protected_snapshot):
    env = dict(os.environ)
    env["WORKAREA_FILES"] = ",".join(os.path.basename(f) for f in files if f.endswith(".html"))
    r = subprocess.run(m["build"], shell=True, cwd=ROOT, env=env,
                       capture_output=True, text=True)
    out = (r.stdout or "").strip()
    if out:
        for line in out.splitlines()[-8:]:
            print("      ", line)
    if r.returncode != 0:
        print(f"      [ERROR] 构建失败 rc={r.returncode}: {(r.stderr or '')[-400:]}")
        return False
    # 核心目标保护：生成器若误写 protected 文件，立即还原并中止
    for rel, old in protected_snapshot.items():
        cur = io.read_text(rel)
        if cur != old:
            io.write_if_changed(rel, old)
            print(f"      [ABORT] 生成器试图改写受保护文件 {rel}，已还原")
            return False
    return True


def cmd_apply(a):
    reg, st = load_reg(), load_state()
    p = build_plan(a, reg, st)
    print_plan(p, reg)
    if a.dry_run:
        print("  [dry-run] 未执行任何写操作。\n")
        return 0
    if not p["rebuild"] and not p["verify_files"]:
        print("  结论：没有变更、没有需求 —— 不重建、不扫描、不写盘。\n")
        return 0
    byid = mod_by_id(reg)
    protected_snapshot = {rel: io.read_text(rel) for rel in p["protected"]
                          if os.path.exists(os.path.join(ROOT, rel))}
    before = {f: io.file_hash(os.path.join(ROOT, f)) for f in p["verify_files"]}
    ok = True
    for mid in p["rebuild"]:
        m = byid[mid]
        files = p["amap"][mid]
        n_html = len([f for f in files if f.endswith(".html")])
        scope = f"范围 {n_html} 页" if n_html else "站点级配置（非页面产物）"
        print(f"  [BUILD] {mid} — {scope}")
        if not run_build(m, files, protected_snapshot):
            ok = False
            break
    after = {f: io.file_hash(os.path.join(ROOT, f)) for f in p["verify_files"]}
    changed_files = [f for f in before if before[f] != after[f]]
    print(f"  [IO] 实际写盘 {len(changed_files)} 个文件；"
          f"{len(before) - len(changed_files)} 个字节不变已跳过")
    if changed_files and len(changed_files) <= 12:
        for f in changed_files:
            print("      ~", f)
    if not ok:
        return 1
    vr = run_verify(p["verify_files"], full=False, force_global=p["force_global"])
    if vr != 0:
        print("  [FAIL] 校验未通过，不更新状态基线、不提交。")
        return 1
    refresh_state(reg, st, p)
    print("  [OK] 增量应用完成，状态基线已更新。\n")
    return 0


def run_verify(files, full=False, force_global=False, gate=False):
    env = dict(os.environ)
    args = ["python3", "scripts/verify_seo.py"]
    if full or force_global:
        env.pop("WORKAREA_FILES", None)     # 全量闸门
        scope = "全量"
    elif not files:
        if not gate:
            print("  [VERIFY] 无脏模块 —— 跳过扫描（无需求不重新扫描）")
            return 0
        args.append("--global-only")
        env.pop("WORKAREA_FILES", None)
        scope = "仅全局不变量"
    else:
        env["WORKAREA_FILES"] = ",".join(files)
        scope = f"增量 {len(files)} 页"
    r = subprocess.run(args, cwd=ROOT, env=env, capture_output=True, text=True)
    print(f"  [VERIFY] {scope}")
    for line in (r.stdout or "").splitlines():
        if "[FAIL]" in line or "[WARN]" in line or "PASS=" in line or "结论" in line:
            print("      ", line.strip())
    if r.returncode != 0 and not (r.stdout or "").strip():
        print("      ", (r.stderr or "")[-500:])
    return r.returncode


def refresh_state(reg, st, p):
    amap, _ = assign(reg)
    byid = mod_by_id(reg)
    verified = set(p["verify_mods"])
    for m in reg["modules"]:
        mid = m["id"]
        files = amap[mid]
        if effective_policy(m, st) == "frozen":
            continue
        rec = st["modules"].setdefault(mid, {})
        rec["hash"] = module_hash(files)
        rec["files"] = len(files)
        if mid in verified or p["force_global"]:
            rec["verified_at"] = now()
            rec["verified_hash"] = rec["hash"]
            rec["result"] = "PASS"
            rec["scope"] = "full" if p["force_global"] else "incremental"
    save_state(st)


def cmd_verify(a):
    reg, st = load_reg(), load_state()
    if a.all:
        rc = run_verify([], full=True)
        if rc == 0:
            amap, _ = assign(reg)
            p = dict(verify_mods=[m["id"] for m in reg["modules"]
                                  if effective_policy(m, st) != "frozen"],
                     force_global=True)
            refresh_state(reg, st, p)
        return rc
    p = build_plan(a, reg, st)
    return run_verify(p["verify_files"], force_global=p["force_global"], gate=a.gate)


def cmd_init(a):
    reg, st = load_reg(), load_state()
    amap, unassigned = assign(reg)
    for m in reg["modules"]:
        mid = m["id"]
        files = amap[mid]
        h = module_hash(files)
        rec = st["modules"].setdefault(mid, {})
        if rec.get("hash") != h or not rec.get("verified_at"):
            rec["verified_at"] = now()
        rec["hash"] = h
        rec["files"] = len(files)
        rec["verified_hash"] = h
        rec.setdefault("result", "BASELINE")
        rec["scope"] = "full"
    wrote = save_state(st)
    print(f"[init] {'已刷新' if wrote else '无实质变化，未写盘'}："
          f"{len(st['modules'])} 个模块内容哈希基线 @ {st['head']}")
    if unassigned:
        print(f"[init] [WARN] 未归属文件 {len(unassigned)} 个：{', '.join(unassigned[:8])}")
    print("[init] 基线已纳入 git，任何新模型/新机器 clone 后 status 即可继承全局认知。")
    return 0


def cmd_audit(a):
    reg, st = load_reg(), load_state()
    amap, unassigned = assign(reg)
    byid = mod_by_id(reg)
    errs = []
    for m in reg["modules"]:
        for nxt in m.get("invalidates", []) + m.get("review", []):
            if nxt not in byid:
                errs.append(f"{m['id']}.invalidates 引用了不存在的模块 {nxt}")
        if not amap[m["id"]] and m["policy"] != "frozen":
            errs.append(f"{m['id']} 未匹配到任何文件（paths/globs 可能有误）")
    for rel in reg["protected"]["paths"]:
        if not os.path.exists(os.path.join(ROOT, rel)):
            errs.append(f"受保护文件不存在：{rel}")
    if unassigned and reg.get("unassigned_is_error"):
        errs.append(f"有 {len(unassigned)} 个文件未归属：{', '.join(unassigned[:8])}")
    state_ids = set(st["modules"])
    reg_ids = set(byid)
    if state_ids - reg_ids:
        errs.append(f"状态文件含已移除模块：{', '.join(sorted(state_ids - reg_ids))}")
    print("\n=========== 注册表自洽审计 ===========")
    print(f"  模块 {len(reg_ids)} 个，受管文件 {sum(len(v) for v in amap.values())} 个")
    print(f"  policy 分布：", end="")
    from collections import Counter
    print(dict(Counter(m["policy"] for m in reg["modules"])))
    if errs:
        for e in errs:
            print("  [FAIL]", e)
        print("  结论：注册表不自洽，增量制度存在盲区。\n")
        return 1
    print("  [PASS] 归属完整、依赖引用有效、受保护文件齐全、状态与注册表一致。\n")
    return 0


def cmd_freeze(a):
    st = load_state()
    ov = st.setdefault("overrides", {}).setdefault("frozen", [])
    if a.action == "freeze":
        if a.mid not in ov:
            ov.append(a.mid)
    else:
        st["overrides"]["frozen"] = [x for x in ov if x != a.mid]
    save_state(st)
    print(f"[{a.action}] {a.mid} -> 当前冻结列表：{st['overrides']['frozen']}")
    return 0


def cmd_handoff(a):
    reg, st = load_reg(), load_state()
    rows, drift, unassigned = compute_status(reg, st)
    dirty = [r["id"] for r in rows if r["dirty"]]
    print("""
==================== 新模型 / 新会话 接手检查单 ====================
本段由 scripts/workarea.py 生成，自包含：不需要读取聊天记录。

【唯一事实来源】先看这三个文件，不要凭印象工作：
  WORKFLOW.md                制度总纲与红线
  scripts/modules.json       模块分区、策略、依赖闭包、受保护文件
  scripts/module_state.json  各模块内容哈希基线与上次验证结论
  （可执行入口统一为：python3 scripts/workarea.py <命令>）

【五条硬纪律】
  1. 先声明模块再动手：plan --module <id> 或 --change <文件>
  2. 无变更不落盘：生成器只经 io_util.write_final / write_if_changed 写盘
  3. 无需求不扫描：只对脏模块 + 依赖闭包读取/重建/校验
  4. 没问题的不做变动：manual / frozen 模块自动流程只读不写
  5. 核心目标不变：引流、询盘、关键词覆盖、转化路径；protected 列表禁自动改

【禁止事项】
  - 不要全量重跑 longtail.py / build_briefings.py 等生成器来"顺手刷新"
  - 不要改动 manual 模块页面，除非任务显式声明该模块
  - 不要用 mtime 判断变化（CI checkout 会重置），一律用内容哈希
  - 不要改 protected 文件来"顺带优化"转化路径

【标准动作】
  python3 scripts/workarea.py status              看状态（零内容读取）
  python3 scripts/workarea.py status --deep       新环境接手先做一次全量哈希复核
  python3 scripts/workarea.py plan --module <id>  看影响范围
  python3 scripts/workarea.py apply --module <id> 只做该板块
  python3 scripts/workarea.py verify --gate       推送前最小闸门
  python3 scripts/workarea.py verify --all        全量复审（仅在显式需求时）
  python3 scripts/workarea.py audit               注册表自洽检查
""")
    print(f"【当前状态】HEAD={git_head()}  基线={st.get('head') or '未建立'}"
          f"  脏模块={', '.join(dirty) if dirty else '无'}")
    print(f"            受管模块 {len(rows)} 个，未归属文件 {len(unassigned)} 个")
    if dirty:
        print("            下一步：先 plan 再 apply，其余板块保持不动。")
    else:
        print("            下一步：无需扫描或重建；有需求时按模块声明即可。")
    print("==============================================================\n")
    return 0


# ------------------------------------------------------------------ CLI
def main():
    ap = argparse.ArgumentParser(description="模块化增量工作区驱动器")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("status"); p.add_argument("--deep", action="store_true")
    p.add_argument("--include-frozen", action="store_true"); p.set_defaults(fn=cmd_status)

    def common(sp):
        sp.add_argument("--module", action="append", default=[])
        sp.add_argument("--change", action="append", default=[])
        sp.add_argument("--all", action="store_true")
        sp.add_argument("--include-scheduled", action="store_true")

    p = sub.add_parser("plan"); common(p); p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("apply"); common(p)
    p.add_argument("--dry-run", action="store_true"); p.set_defaults(fn=cmd_apply)

    p = sub.add_parser("verify")
    p.add_argument("--module", action="append", default=[])
    p.add_argument("--change", action="append", default=[])
    p.add_argument("--all", action="store_true")
    p.add_argument("--gate", action="store_true")
    p.add_argument("--include-scheduled", action="store_true")
    p.set_defaults(fn=cmd_verify)

    p = sub.add_parser("init"); p.set_defaults(fn=cmd_init)
    p = sub.add_parser("audit"); p.set_defaults(fn=cmd_audit)
    p = sub.add_parser("handoff"); p.set_defaults(fn=cmd_handoff)
    for name in ("freeze", "unfreeze"):
        p = sub.add_parser(name); p.add_argument("mid")
        p.set_defaults(fn=cmd_freeze, action=name)

    a = ap.parse_args()
    sys.exit(a.fn(a))


if __name__ == "__main__":
    main()
