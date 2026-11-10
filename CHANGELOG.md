# Changelog

本文件记录 anchormere.com 站点的**结构性变更**，用于换模型 / 换维护者时快速建立上下文。
格式遵循 Keep a Changelog 思路，倒序排列。日常资讯由 `news-auto.yml` 自动提交，
不逐条登记（见 `git log --grep='auto: daily news digest'`）。

核心目标（任何变更不得偏移）：**引流 → 询盘 → 关键词覆盖 → 转化路径**。
保护文件（`contact.html` / `index.html` / `assets/consent.js` / `assets/lang.js` /
`_headers` / `robots.txt`）禁止自动重建，改动须显式指定目标并在提交信息说明。

---

## [2026-11-10] · 质量巡检：修案例页死锚 + news 页脏 description（技术硬问题）

### 全站质量体检（132 页 / 131 sitemap URL）
技术健康、内容体量、结构化数据、可访问性、安全响应头、线上一致性多维巡检结论：
常规项全绿（title/description 唯一性 0 重复、H1 唯一、图片 alt 全覆盖、
外链 noopener 全覆盖、496 个 JSON-LD 块 0 解析失败、36 长尾页 Jaccard 0.428
且 >0.70 组合 0、独有词 7.9%）；线上 HSTS/CSP/X-Frame-Options/Referrer-Policy/
COOP/CORP 齐全，HTTP/2+3、Brotli、TLS 正常，sitemap 全 200。

### 修复的 2 类真 bug
- **案例枢纽页 4 个死锚**：`build_cases.py` 的 TOC 生成 `#reshoring` 等 4 个
  锚点，但分组 `<section>` 从未写 `id`，导航链接全部无效。已给 section 加 id 并重建。
- **4 个 news 页脏/过短 description**：RSS 抓到模板噪声「Comments」或极短副标题
  （8/29/56/59 字符），污染 description / desc-zh / og / twitter / JSON-LD 五处。
  `news_digest.py` 新增 `NOISE_SUMMARY` + `MIN_SERP_DESC=60` 兜底，用真实标题构造
  133–144 字符完整句（不编造事件/数据/背书）；存量 4 页一次性修复，5 字段统一。

### 制度固化（换模型仍有效）
`verify_seo.py` 新增两条闸门：`4d` meta description 60–170 字符且无 RSS 噪声词、
`4e` 站内锚点 `href=#id` 必须可跳转（0 死锚）。PASS 43 → 45。
同步 `modules.json` verify.global / `WORKFLOW.md` 不变量清单。

### 明确不改（设计取舍 / 非缺陷）
footer 用 h4 造成的 heading 跳级（131 页，属可访问性建议非 WCAG 失败项、
改动会触碰全站骨架与 protected 边界）；图片缺 width/height（CSS 已固定容器
尺寸、无实际 CLS）；404 页薄内容 / 无 JSON-LD / 无 twitter:card（404 本就不该
索引）；TTFB ~1s（`_headers` 为 protected，属 CDN 层）。按「无问题不改动」制度
保留，列为建议项。protected 与简报页零改动；核心目标（引流/询盘/关键词覆盖/
转化路径）不变。

---

## [2026-11-10] · 修复 news 页 canonical 指向 .html（GSC「备用网页 / 自动重定向」）

### 问题
GSC「网页索引编制」显示 85 页未编入索引，原因含「备用网页（有适当的规范标记）」
与「网页会自动重定向」。站内排查定位：54 个 news 页的 canonical / hreflang /
og:url / JSON-LD `mainEntityOfPage` 写成 `https://anchormere.com/xxx.html`，
而 Cloudflare Pages 把 `.html` 308 到 clean URL、sitemap 也是无扩展名形式。
Google 因此把 clean URL 判为「备用网页」、把 `.html` URL 判为「重定向」，两者都不收录。
`verify_seo.py` 第 4 节的 `norm()` 会剥掉 `.html`，所以这个错误一直被判为 PASS。

### 根治（数据源 → 生成器 → 收口层 → 闸门）
- `scripts/news_digest.py`：新增 `page_url`（去 `.html`），5 处 URL 字段统一用它，
  CI 每夜重生不会再带回。
- `scripts/html_finalize.py`：收口层不变量 5 → 6 条，绝对 URL 形式的 SEO URL
  （`href` / `og:url` / JSON-LD 内所有同域 `.html`，含 `BreadcrumbList.item`）
  强制 clean；刻意不碰 `contact.html`（protected）的表单 `redirect`
  （功能性 `value=`，非 SEO 字段）。
- `scripts/verify_seo.py` 新增闸门 `4c`：检查原始字符串（含 JSON-LD 块），
  PASS 42 → 43。
- 一次性 `site_normalize.py` 归一化 54 个 news 页的 5 类 URL 字段。

### 边界与核验
- protected 文件零改动；`site_normalize --check` 0；全站归一化幂等。
- 线上 sitemap 131 URLs 全 200、clean URL、无 404 / 重定向；canonical 自引用 131/131。
- 唯一保留的同域 `.html` 绝对 URL 是 `contact.html` 表单 redirect（故意，功能所需）。
- 核心目标（引流 / 询盘 / 关键词覆盖 / 转化路径）不变。

---

## [2026-11-09] · 长尾页差异化（降 scaled content 风险）+ 内容权威性 E-E-A-T

### 新增
- `scripts/longtail_depth.json`：36 页品类专属深度内容唯一数据源。144 条全局
  唯一的工程/采购笔记、36 个 RFQ 决策场景、144 条公开标准引用（全英文，含适用
  范围）、216 条品类术语、36 个页级专属 h2、36 条下单前核验动作。
- `scripts/build_editorial.py` → `editorial-standards.html`：E-E-A-T Trust 枢纽，
  含可核验内容台账、四条编辑原则、明确不主张事项、更正渠道、AboutPage/FAQPage
  结构化数据；36 个长尾页均内链至此页。
- `scripts/longtail.py` 渲染深度区块；`WebPage` 增 `citation` / `dateModified` /
  `reviewedBy` 角色 / `isBasedOn`，新增 `DefinedTermSet`。

### 量化结果（复现评估报告口径实测）
- 平均可见正文 **988 → 1,240 词**；两两 Jaccard **0.437 → 0.418**；相似度
  >0.70 组合 **1 → 0**；**前 6 个 h2 完全相同的最多页数 19/36 → 1/36**（36 种
  结构）。严格 set 口径独有词占比 7.1% → 8.2%：分母含转化骨架 292 个共享词，
  不以堆砌方式刷到 25%，改以结构不变量固化。

### 边界与制度
- 标准名仅作编辑性引用，**不主张持有任何认证**；数字为典型区间、按 RFQ 确认；
  公开案例保留完整来源 URL 且非客户项目。公司资质不提供、不预留空间（沿用决定）。
- `scripts/verify_seo.py` 新增全局闸门 `3g`（10 项），PASS 24 → 42。
- `scripts/modules.json` 新增 `data-depth` / `editorial` 两模块（共 20 个），
  `data-depth` 排在 `engine` 前以确保 `scripts/*.json` 归属正确。
- protected 文件零改动；核心目标（引流 / 询盘 / 关键词覆盖 / 转化路径）不变。

---

## [2026-11-08] · 公开案例编排（联网核验 + 来源 URL 标注）

### 新增
- `scripts/case_references.json`：11 条真实公开案例的单一数据源，来自 Reuters、
  QIMA、U.S. CBP 裁定 / EAPA 案卷、上市公司年报，逐条带完整 `Source URL:` 明文、
  中英摘要与采购启示；口径明确为「行业参考，非 Anchormere 客户项目 / 背书」。
- `scripts/build_cases.py` → `sourcing-case-studies.html`：案例枢纽页，含
  `CollectionPage` / `FAQPage` / `WebPage` 结构化数据、醒目免责声明与询盘 CTA。
- 36/36 个长尾页的「案例分享」板块追加「公开报道的真实案例（附来源网址）」区块：
  每页按主题匹配最多 2 条案例，带明文来源 URL、外链与指向枢纽页的内链。

### 变更 / 清理
- `README.md` 移除「注册号…可补填」预留项：公司资质不提供、站内不新增资质板块
  或占位字段；`Organization.sameAs` / `foundingDate` 待外部 URL 到位后直接补入
  `org_entity.json`，当前不预置空值。
- `scripts/verify_seo.py` 新增全局闸门 3f：校验枢纽页与案例区块的来源 URL 明文、
  免责声明、枢纽页内链，并禁止把公开案例表述为自家客户。
- `scripts/modules.json` 新增 `data-cases` / `cases-hub` 两个模块（共 18 个），
  `WORKFLOW.md` / `llms.txt` / 关键词地图 §14 同步登记。
- `protected` 文件零改动；核心目标（引流 / 询盘 / 关键词覆盖 / 转化路径）不变。

---

## [2026-11-08] · 可直接执行批次（P2 收尾 + 监控兜底 + 回滚预案）

### 新增
- `.github/workflows/news-watchdog.yml`：每日 05:00 UTC 检查 `news-auto` 最近一次
  成功运行，超 26h 或最近一次失败且已过 2h 时，经 `workflow_dispatch` 自动补跑。
  不复制生成逻辑，完整复用原链路。
- `CHANGELOG.md`、`ROLLBACK.md`：变更台账与分级回滚预案。

### 变更
- `scripts/html_finalize.py`：收口层新增两条全站不变量
  1. `meta keywords` 按逗号词边界收敛到 ≤200 字符（41 页超标；Google 忽略该标签，
     零关键词损失，LSI 词仍保留在正文 / FAQ / 结构化数据里）；
  2. `FAQPage` JSON-LD 补 `speakable`，选择器按页面 DOM 自适应
     （长尾页 `.qa h3` / `.qa p`，早期框架页 `h3`）。
  放在收口层而非各生成器，是为杜绝历史上多次出现的「CI 重生带回旧模板」。
- `scripts/verify_seo.py`：新增全局闸门 3e（keywords 长度 + FAQPage speakable），
  始终全量扫描，FAIL 阻断推送。
- `scripts/health_check.py`：线上抽样软校验上述两项（WARN 级，避免 Cloudflare
  Pages 部署延迟造成误报）。
- `SEO与SEM关键词地图.md` §5 / §8：修正 sitemap URL 数（109 → 121），
  移除易漂移的写死校验项数，补登记收口层 / 模块化 / 巡检脚本。

### 本批明确**不做**（避免编造或越权）
- `Organization.foundingDate`、`sameAs`：需真实注册信息与 LinkedIn 等 URL，不编造。
- `Article.author`：全站 0 页缺失，已由收口层统一以 `@id` 串联唯一 Organization。
- GA4 关键事件标记 / Google Ads 导入、GSC 词级迭代、SEM 实投、GEO 引擎实测基线：
  需后台 OAuth 授权或用户拍板，不属于「可直接执行」范围。

---

## [2026-11-08] · `bd16af2` 热搜词诊断与扩词
新增 8 个 2026 目标群体高热词落地页（landed cost 2026 / China+1 / HTS 税则 /
AI 硬件智能眼镜 / 服务机器人 / 便携储能 / 电助力车 / 户外露营装备），
同步 `modules.json`、`llms.txt`、关键词地图 §13、`README.md`、`WORKFLOW.md`。
修复 `workarea.assign()` 未落盘新页被范围闸门排除、以及中文文档名被 git
八进制转义导致 `docs` 永远误判 CLEAN 两个制度缺陷。

## [2026-11-07] · `060547d` GSC 产品摘要根治
线上 34 页仍为 `@type: Product` 且缺 `offers/review/aggregateRating`。补齐会虚构
价格与评价并重新误归类为电商；全站改 `Service` 承载主题实体，新增全局不变量闸门
禁止 `Product/Offer/offers/aggregateRating`。需在 GSC 点「验证修复」。

## [2026-11-07] · `8fbc525` 模块化增量工作制度
新增 `scripts/modules.json`（16 模块 / protected / 策略 / invalidates）、
`module_state.json`、`workarea.py`（status/plan/apply/verify/init/audit/handoff/freeze）、
`io_util.py`（`write_if_changed` / `write_final` / `selected` / 内容哈希）、
`html_finalize.py`、`.github/workflows/module-gate.yml`。
目标：**没有问题的不做变动，没有需求的不用重新扫描，换模型也能直接运行制度**。

## [2026-11-07] · `cdc8907` / `1526b1e` 内容质量与权威度
10 篇带权威外链、明文 `Source URL:` 来源标注与专有名词的采购情报简报；
42 篇 digest 补 `Article.citation`；28 条长尾种子补品类专属工艺要点、
E-E-A-T 审核署名、Glossary；全站实体收敛到单一数据源。

## [2026-11-07] · `aad7cf8` / `be698c5` 两轮独立复审
修复 sitemap lastmod 同日漂移、`/index` 308、`wordCount` 不实、3785 个 `.html`
内链 308、1133 个中文块缺 `lang`、52 页 author/publisher 内联重复、死锚；
建立 CI 验证闸门。

## [2026-11-06] · `9dd98d6` 方案 A
移除 `Product/Offer` 电商字段，消除 GSC 购物误归类；确立「引流 + 询盘」口径。

---

维护约定：每批结构性改动在提交后补上实际 commit sha；生成器逻辑变更必须同步
`modules.json` 的影响声明并跑 `workarea.py audit`；任何页面级修复必须能追溯到
生成器 / 数据源 / 收口层，禁止只改 HTML 产物。
