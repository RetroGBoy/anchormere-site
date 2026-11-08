# 回滚预案（Rollback Runbook）

适用站点：anchormere.com · Cloudflare Pages + GitHub `main` 自动部署。
**核心目标不可回滚**：引流 → 询盘 → 关键词覆盖 → 转化路径。任何回滚都不得破坏
`contact.html` 的 RFQ 表单、WhatsApp / 邮箱入口与 `generate_lead` 埋点。

> 总原则：**优先 `git revert`（保留历史、可审计、不产生分叉）**。
> `reset --hard` + `push --force` 只在本地尚未推送或确认无他人提交时使用，
> 且必须先与仓库所有者确认；它是最后手段，不是常规操作。

---

## 0. 先判断回滚层级（30 秒）

| 症状 | 层级 | 章节 |
|---|---|---|
| 只是线上渲染不对，代码没问题 | Cloudflare 部署级 | §1 |
| 本批改动引入回归，需撤销一整批 | Git 提交级 | §2 |
| 只有几个页面被生成器污染 | 单文件 / 单模块级 | §3 |
| 每日资讯 / 某板块持续出错，需先止血 | 模块冻结级 | §4 |
| 结构化数据被 GSC 判错，需重验 | 验证闭环级 | §5 |

---

## 1. Cloudflare Pages 部署级回滚（最快，秒级）

不依赖 git，适合"代码没问题、但这版部署有问题"：

1. Cloudflare Dashboard → Workers & Pages → `anchormere-site` → **Deployments**。
2. 找到上一个状态为 *Success* 的部署，右侧 `⋯` → **Rollback to this deployment**。
3. 确认后该 deployment 立即成为线上版本。

注意：这只是把线上指针移回去，**git `main` 没变**。下一次推送会覆盖它。
所以必须紧接着做 §2 或提交修复，否则问题会随下一次部署复现。

---

## 2. Git 提交级回滚（推荐）

```bash
# 1) 确认要撤销的提交
git log --oneline -10

# 2) 生成反向提交（保留历史，不改写已推送记录）
git revert <sha>            # 单批
git revert --no-commit <sha1> <sha2>   # 多批合并成一次反向提交

# 3) 回滚后必须重建的派生资产
python3 scripts/site_normalize.py
python3 scripts/build_sitemap.py
python3 scripts/workarea.py init       # 刷新模块内容哈希基线
python3 scripts/workarea.py audit
python3 scripts/workarea.py verify --all

# 4) 提交并推送
git add -A
git commit -m "revert: <原因，关联 sha>"
git push origin main
```

**为什么必须跑 `workarea.py init`**：`module_state.json` 记录的是各模块内容哈希，
回滚页面后若基线不刷新，`status` 会把回滚误判为"脏模块"，并触发不必要的全量重建，
违背"没有问题的不做变动"。

**若本地刚提交、还没推送**：可用 `git reset --hard HEAD~1` 直接撤销，
不需要 force push。已推送则改用 `git revert`。

---

## 3. 单文件 / 单模块级回滚

生成器产物是**可重建的派生资产**，禁止手改 HTML 来"修回来"：

```bash
# 从指定提交取回数据源 / 生成器（而不是取回 HTML 产物）
git checkout <sha> -- scripts/longtail_seeds.json scripts/longtail.py

# 由制度按依赖闭包重建受影响模块，其余模块零变动
python3 scripts/workarea.py plan  --change scripts/longtail_seeds.json
python3 scripts/workarea.py apply --gate
python3 scripts/workarea.py verify --all
python3 scripts/build_sitemap.py
python3 scripts/workarea.py init
```

**关键**：改数据源 / 生成器 → `plan` 自动展开 `invalidates` 依赖闭包 → `apply` 只重建
受影响板块。不要直接 `python3 scripts/longtail.py` 全量跑，也不要手动复制页面。
`html_finalize.normalize()` 是收口层，保证生成器产出即最终态，单独复跑零写盘。

确需只还原单个页面时：
```bash
git checkout <sha> -- <page>.html
python3 scripts/site_normalize.py --check   # 收口层不变量是否仍成立
python3 scripts/workarea.py init
```

---

## 4. 模块冻结级止血（不回滚代码）

某板块（如每日资讯）持续出错但不想动其他板块时，让制度临时跳过它：

```bash
python3 scripts/workarea.py freeze news-digest   # 冻结
# ... 修好数据源 / 生成器 ...
python3 scripts/workarea.py unfreeze news-digest
python3 scripts/workarea.py status
```

冻结期间 `status` 显示 `SKIP`，增量闸门与 `apply` 都不处理该板块；
`archive` 模块默认就是 frozen（历史归档，永不重建）。这是成本最低的止损方式。

---

## 5. 结构化数据 / 索引验证闭环

涉及 JSON-LD、canonical、hreflang 的回滚，代码恢复不等于搜索引擎已恢复：

1. `python3 scripts/workarea.py verify --all` → PASS / WARN=0 / FAIL=0。
2. `python3 scripts/site_normalize.py --check` → 退出码 0。
3. 线上抽样：`python3 scripts/health_check.py` → HEALTHY / CRITICAL 0。
4. `sitemap.xml` 重建后，在 **Google Search Console → 站点地图** 重新提交；
   若之前是「产品摘要 / 购物」类错误，在 GSC 对应问题条目点 **验证修复**。
5. `python3 scripts/submit_indexnow.py` 通知 Bing 系引擎重新抓取。
6. 2–6 周后按 GSC「效果」的真实查询词复核排名与曝光。

---

## 6. 回滚后必做清单

- [ ] `git status --short` 干净，远端 `main` 与本地一致（`git log -1` 双端核对）。
- [ ] `workarea.py status` 全 CLEAN（或仅预期的 SKIP），`audit` PASS。
- [ ] `verify --all` 无 FAIL；`site_normalize --check` 退出码 0。
- [ ] 幂等复跑：`apply --all` 后零写盘（证明没有"中间态"残留）。
- [ ] 核心转化路径手工验一次：`/contact` 表单可提交、WhatsApp 链接正确、
      GA4 `generate_lead` 事件可触发。
- [ ] 在 `CHANGELOG.md` 登记本次回滚原因与关联 sha。

---

## 7. 已知坑（历史踩过）

- **CI 重生带回旧模板**：早期只改 HTML 产物，第二天 `news-auto.yml` 用旧生成器
  重写页面，修复消失。所有页面级修复必须落到数据源 / 生成器 / 收口层。
- **sitemap lastmod 全站同日**：CI checkout 会重置 mtime；`build_sitemap.py`
  依据页面真实内容日期生成，勿改回 mtime 方案。
- **中文文档名 git 转义**：`git status` 默认把中文名转八进制，曾导致 `docs`
  模块永远误判 CLEAN；`workarea.py` 已统一用 `git -c core.quotePath=false status`。
- **PAT 权限**：推送需 `repo` + `workflow` scope；不要用聊天记录里出现过的旧 token
  （见 `SEO_GEO系统收纳提报流程.md` §8 安全段，应已全部吊销）。
