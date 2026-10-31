# Anchormere 站点 · SEO / GEO 系统收纳与提报流程（SOP）

> 运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）
> 站点：`https://anchormere.com`（Cloudflare Pages，源站 GitHub `RetroGBoy/anchormere-site` `main`）
> 适用范围：本 SOP 覆盖站点所有「自然搜索（SEO）+ 生成式引擎优化（GEO/AEO）」资产的**归集管理（收纳）**与**上线/收录（提报）**全流程。
> 版本：2026-10-31 · 当前站点状态：51 个业务页、10 篇资讯、GA4 `G-EZE1LV2MRH`、表单 Web3Forms 静默收单。

---

## 0. 为什么需要这套流程

站点 SEO/GEO 能力不是一次性工程，而是**持续运转的系统**：每天有自动化内容生成、每周有长尾词扩充、每次改动都要安全上线并被搜索引擎/AI 引擎收录。若没有「收纳—提报」闭环，会出现三类问题：

- **散**：关键词、页面、结构化数据各管各的，无法统一对账；
- **卡**：自动化跑出 bug（如分类 KeyError）无人发现，资讯断更；
- **盲**：上线了但搜索引擎/AI 没收录，流量白白流失。

本流程把「资产怎么归集、改动怎么上线、收录怎么提报、效果怎么复盘」固化成可执行的步骤。

---

## 1. 名词定义

| 术语 | 含义 | 在本系统对应 |
|------|------|--------------|
| **SEO** | 搜索引擎优化，让 Google/Bing 等把页面排到前面 | 长尾页、结构化数据、sitemap、关键词地图 |
| **GEO / AEO** | 生成式引擎优化，让 ChatGPT / Perplexity / Gemini / Claude 在回答时引用我们 | `llms.txt`、`robots.txt` 放行 AI 爬虫、清晰的事实型内容 |
| **收纳** | 把分散的 SEO/GEO 资产**系统化归集、分层、归档、去重** | 关键词地图、长尾页生成、资讯索引封顶归档、结构化数据注入 |
| **提报** | 把内容/站点**提交上线部署**，并**向索引平台提报收录**，必要时**向上汇报** | Git→Cloudflare 部署、GSC/Bing 提交、CI 自动推送、周报 |

一句话：**收纳是把家收拾好，提报是把家亮出来。**

---

## 2. 系统总览（已部署能力矩阵）

| 能力 | 实现方式 | 入口文件 / 脚本 | 触发方式 |
|------|----------|----------------|----------|
| 关键词体系 | 品牌/母品类/长尾/竞品/问答五层漏斗 | `SEO与SEM关键词地图.md` | 人工维护 |
| 长尾落地页 | 14 个双语落地页，含 FAQ/规格/JSON-LD | `scripts/longtail.py` + `longtail_seeds.json` | 按需人工跑 |
| 结构化数据 | hreflang(en/zh-CN/x-default)、Breadcrumb、Product、FAQ JSON-LD | `scripts/seo_inject.py`（幂等） | 页面改动后跑 |
| GA4 转化 | 同意门控加载 + `generate_lead`/`contact_click`/`whatsapp_click` | `assets/consent.js`（GA4 `G-EZE1LV2MRH`） | 全站注入 |
| 询单回收 | Web3Forms 静默收单（转发 Gmail），电话必填 | `contact.html` | 访客实时 |
| 资讯自动生成 | 每日抓取→中英摘要→落地页→索引封顶 48 + 归档 | `scripts/news_digest.py` + CI | 每日自动 |
| sitemap | 收录所有业务页（含资讯、归档） | `scripts/build_sitemap.py` | 每次生成后 |
| GEO 资产 | `llms.txt`（给 AI 的事实卡）、`robots.txt`（放行 AI 爬虫） | 根目录静态文件 | 部署即生效 |
| 索引提报（IndexNow） | 全量 sitemap 推送 Bing/Yandex/Seznam/Naver | `scripts/submit_indexnow.py` + 根目录 `<key>.txt` | 每日 CI + 手动 |
| 上线部署 | 静态构建 → Cloudflare Pages 边缘缓存 | GitHub Actions + Cloudflare | push 即部署 |

---

## 3. 收纳流程（资产归集与归档）

### 3.1 关键词收纳
- **主账本**：`SEO与SEM关键词地图.md`，按「品牌词 / 母品类词 / 长尾产品词 / 竞品对比词 / GEO 问答词」五层维护。
- **规则**：每新增一个长尾页，必须先在地图 §3 登记「slug ↔ 英文主词 ↔ 中文主词 ↔ 母品类」四联映射。
- **SEM 联动**：长尾页与广告组一一对应（词组/精确匹配），落地页用对应 slug，不共用首页。

### 3.2 长尾落地页收纳
- **种子**：`scripts/longtail_seeds.json`（每个种子含 slug、双语标题、能力点、规格三元组 `[en_param, en_value, zh_value]`、FAQ）。
- **生成**：`python3 scripts/longtail.py` → 输出双语 H1/H2、能力清单、规格时效表、FAQ、**Product + Breadcrumb + FAQ JSON-LD**、面包屑、hreflang、回链母品类 + `contact.html` CTA。
- **去重/幂等**：重复跑不会污染已有内容；新增 slug 才生成新页。

### 3.3 资讯内容收纳（自动 + 封顶）
- **来源**：`news_digest.py` 每日从科技/制造/采购源抓取，经 `BLOCK` 离题清单过滤 + 相关性排序，生成 4 篇中英双语摘要落地页。
- **索引封顶**：`/news` 仅保留**最新 48 篇**卡片；超出部分自动分页到 `news-archive.html`、`news-archive-2.html`…（每页 48），**永不无限膨胀**。
- **归档入口**：`/news` 页脚提供「查看更早的资讯 →」入口，旧文章不丢失。
- **意义**：访客打开 `/news` 永远轻量（始终 ≤48 卡），单篇文章页恒为约 12KB，不会因累积而变卡/占内存。

### 3.4 结构化数据收纳
- `seo_inject.py` **幂等**注入：先剥离旧注入（不跨 `</script>`），再写 hreflang、`BreadcrumbList`、`@type: Product`（产品页）、`FAQPage`。
- 跑法：`python3 scripts/seo_inject.py`（任何页面改动后执行，确保 JSON-LD/多语言标签齐全）。
- 验证：用 [Google Rich Results Test](https://search.google.com/test/rich-results) 抽测 1–2 页。

### 3.5 GEO 资产收纳
- `llms.txt`：给 AI 系统的「事实卡」——公司定位、品类、能力、信任要素，纯文本、无营销废话，便于 AI 直接引用。
- `robots.txt`：**显式放行** `GPTBot` / `ChatGPT-User` / `PerplexityBot` / `ClaudeBot` / `Google-Extended` / `Applebot`（竞品未放行，抢早鸟红利）。
- 二者随部署即生效，改动后需确认 `sitemap.xml` 同步引用。

### 3.6 转化回收
- 所有询单入口（表单、WhatsApp、邮箱）统一上报 GA4 事件；`generate_lead` 是核心转化指标，用于衡量 SEO/GEO 真实 ROI。

---

## 4. 提报流程（上线与收录）

### 4.1 代码提报 → 部署（标准发布路径）

```bash
# 1) 本地改动后，先跑脚本保证 SEO 资产完整
python3 scripts/seo_inject.py
python3 scripts/build_sitemap.py

# 2) 自检（占位符/死链/邮箱一致性）
grep -rn "YOUR_" . --include=*.html || echo "无占位符残留"

# 3) 提交并推送到 main（Cloudflare Pages 自动部署）
git add -A
git commit -m "feat: ..."
git push origin main        # 含 workflow 文件时，token 需具备 workflow 作用域
```

> 部署即生效：Cloudflare Pages 监听 `main`，push 后约 1 分钟内全球边缘上线。

### 4.2 收录提报（让搜索引擎/AI 发现）

| 平台 | 动作 | 频率 |
|------|------|------|
| **Google Search Console** | 提交 `https://anchormere.com/sitemap.xml`；新页用「URL 检查 → 请求编入索引」 | 首次全量提交 + 新页即时（**需 owner 的 Google 账号，无法用 API 自动化**） |
| **Bing / Yandex / Seznam / Naver（IndexNow）** | `scripts/submit_indexnow.py` 全量推送 sitemap 至 `api.indexnow.org`；密钥发布于根目录 `<key>.txt` | 每日 CI 03:17 UTC + 手动 `workflow_dispatch`，已自动化 ✅ |
| **GEO / AI 引擎** | 确保 `llms.txt`、`robots.txt` 放行 AI 爬虫；内容事实清晰、可被抓取 | 部署即生效，季度复核 |
| **Schema 校验** | Rich Results Test 抽测结构化数据 | 每次大改后 |

> **收录提报补全说明（2026-10-31）**：此前「IndexNow 自动提报」为待办，本次已落地——新增 `scripts/submit_indexnow.py` 与 `.github/workflows/indexing-submit.yml`，并补交根目录密钥文件 `b1700fd697c7492b958b22d8d2adf646.txt`。Bing 系引擎现已自动收录；**Google 侧仍需 owner 在 GSC 手动提交一次 sitemap.xml**（API 需 Google OAuth，沙箱无法代操作）。
>
> GEO 没有「提交入口」，靠的是**内容可被抓取 + 事实清晰 + llms.txt 引导**。不要做 cloaking，AI 与搜索引擎看到的内容必须一致。

### 4.3 自动提报（CI 每日）

- **工作流**：`.github/workflows/news-auto.yml`，每日北京时间 09:00（UTC 01:00）调度，并含 `build_sitemap.py` 步骤。
- **行为**：生成当日资讯 → 重建 `/news` 索引（封顶 48）→ 重建 sitemap → commit 并 push → Cloudflare 自动部署。
- **索引提报工作流**：`.github/workflows/indexing-submit.yml`，每日 03:17 UTC 调度 + 手动 `workflow_dispatch`，调用 `scripts/submit_indexnow.py` 把全量 sitemap 推送至 IndexNow（Bing/Yandex/Seznam/Naver）。
- **可靠性注意**：GitHub 共享 runner 的 cron 曾出现**不点火**（历史运行仅手动触发过）；目前以 `workflow_dispatch` 手动补跑兜底。若连续两日未自动生成，需人工触发并检查日志。

---

## 5. 端到端流程总图

```
[关键词地图]──登记──▶[长尾种子/资讯源]──▶[脚本生成]
                                            │
                          ┌─────────────────┼─────────────────┐
                          ▼                 ▼                 ▼
                    [longtail.py]     [news_digest.py]    [seo_inject.py]
                    长尾落地页         每日资讯+封顶归档     结构化数据注入
                          └─────────────────┼─────────────────┘
                                            ▼
                                    [build_sitemap.py]   ← 收录清单
                                            ▼
                              [git push main] ──▶ [Cloudflare Pages 部署]
                                            ▼
                       ┌────────────────────────────────────┐
                       ▼                    ▼               ▼
              [GSC/Bing 提交sitemap]   [AI 抓取 llms.txt]   [GA4 转化回收]
              (收录提报)               (GEO 提报)          (效果回流)
                       └────────────────────────────────────┘
                                            ▼
                                  [周度复盘：流量/收录/转化]
```

---

## 6. 监控与复盘

### 6.1 上线前健康检查清单
- [ ] 无占位符残留（`YOUR_` / `REPLACE` / `example.com`）
- [ ] 全站邮箱统一 `Anchormere@gmail.com`、WhatsApp 统一 `+8619068984158`、微信 `SenyaSz`
- [ ] `seo_inject.py` 已跑（hreflang + JSON-LD 齐全）
- [ ] `build_sitemap.py` 已跑，新页在 sitemap
- [ ] GA4 同意门控与转化事件接线正常

### 6.2 CI 运行监控
- 每日查 GitHub Actions（`actions/workflows`）是否有 `news-auto` 运行、结论是否为 `success`。
- 失败优先看日志：曾因 `FRAMING` 缺 `procurement` 键导致 `KeyError` 中断（已修 `0b85fd3`），同类缺失键已做兜底 `.get(primary, FRAMING["gba"])`。

### 6.3 效果指标
| 指标 | 看板 | 目标 |
|------|------|------|
| 自然/直接流量 | GA4「获客 → 流量获取」 | 长尾词逐步起量 |
| `generate_lead` 次数 | GA4 事件 | 随流量线性增长 |
| 收录覆盖率 | GSC「网页索引 → 已编入索引」 | sitemap 页 100% 收录 |
| GEO 可见度 | ChatGPT/Perplexity 实测提问 | 品类问题能引用 anchormere |

### 6.4 周期复盘
- **周**：资讯是否正常生成、是否有 bug 致失败、本周新增长尾页登记。
- **月**：关键词地图更新、GA4 漏斗、GEO 引擎实测引用情况。
- **季**：`llms.txt`/`robots.txt` 复核、归档页体量评估、技术债清理。

---

## 7. 角色与节奏（RACI 简表）

| 事项 | 负责人 | 频率 | 工具 |
|------|--------|------|------|
| 关键词地图维护 | 运营/SEO | 周 | `SEO与SEM关键词地图.md` |
| 长尾页扩充 | 运营+技术 | 按需 | `longtail.py` |
| 资讯自动化 | 系统（CI） | 每日 | `news_digest.py` |
| 结构化数据/ sitemap | 技术 | 每次改动 | `seo_inject.py` / `build_sitemap.py` |
| 部署上线 | 技术 | 按需 | Git → Cloudflare |
| 收录提报 | SEO | 首提+周 | GSC / Bing |
| 效果复盘 | 全员 | 周/月/季 | GA4 + 本 SOP §6 |

---

## 8. 风险、待办与安全

**已修复风险**
- `news_digest.py` 的 `FRAMING` 缺 `procurement` 键会令每日自动化崩溃 → 已补键 + 兜底（提交 `0b85fd3`）。
- `/news` 无限累积致页面变重 → 已加 48 封顶 + 归档分页（提交 `d8685a6`）。

**待办 / 持续项**
- GitHub Actions cron 可靠性弱，建议加「超 24h 未生成则自动补跑」兜底任务。
- 关键词地图 `.md` 的旧 GA4 占位 / Formspree 字段已同步为 `G-EZE1LV2MRH` / Web3Forms ✅（提交于本批次）。
- **收录提报补全** ✅（2026-10-31）：新增 `scripts/submit_indexnow.py` + `.github/workflows/indexing-submit.yml`，补交根目录密钥文件 `b1700fd697c7492b958b22d8d2adf646.txt`，Bing 系引擎自动收录已落地；Google GSC 仍需 owner 手动首次提交 sitemap.xml（见 §4.2）。
- **跨平台关联词扩充** ✅（2026-10-31）：14 个长尾页新增 `related`（Google/Bing/Baidu/1688/Alibaba/Amazon/Made-in-China 关联检索词词云）与 `related_qa`（B2B 平台买家常见问题），已渲染「跨平台关联检索词」区块并并入 meta keywords 与 FAQPage JSON-LD（`scripts/longtail.py` + `longtail_seeds.json`）。

**安全（重要）**
- 聊天记录中曾出现 3 个 GitHub PAT（`ghp_jt8M…`、`ghp_SjOr…`、`ghp_Zwro…`），其中 `ghp_Zwro…` 具备 `admin` 权限。建议立即到 GitHub → Settings → Developer settings → PAT **全部吊销**，换一个仅限本仓库、最小权限（含 `workflow`）的新 token。
- 凭证勿再粘贴进聊天/代码；`Web3Forms access_key` 与 `GA4_ID` 已写入仓库，属正常运行所需，但仓库应为私有或限制可见性。
