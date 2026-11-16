# Changelog

本文件记录 anchormere.com 站点的**结构性变更**，用于换模型 / 换维护者时快速建立上下文。
格式遵循 Keep a Changelog 思路，倒序排列。日常资讯由 `news-auto.yml` 自动提交，
不逐条登记（见 `git log --grep='auto: daily news digest'`）。

核心目标（任何变更不得偏移）：**引流 → 询盘 → 关键词覆盖 → 转化路径**。
保护文件（`contact.html` / `index.html` / `assets/consent.js` / `assets/lang.js` /
`_headers` / `robots.txt`）禁止自动重建，改动须显式指定目标并在提交信息说明。

---

## [2026-11-16] · 修复首次推送回退 CI 新闻状态 + 根治新闻页域名注入（二次 commit）

首个推送 commit（`230cc37`）上线后，`Modular workspace gate` 首次由非 bot 提交
触发（`module-gate.yml` 设 `if: github.actor != 'Anchormere Bot'`，此前 CI 自动
提交全部跳过闸门），暴露两个被长期掩盖的缺陷：

- **状态回退**：本地工作区不含 CI 在 11-11～11-15 生成的 20 个新闻页，且本地
  `news.html` / `news-archive.html` / `news_state.json` / `sitemap.xml` 是较旧
  快照。推送按「本地相对远端有差异」覆盖，把远端连续状态回退：去重记录
  78→58、sitemap 155→144、新闻索引不再链接 20 个页（孤儿页）。
- **新闻页缺域名块**：`news_digest.py` 自带独立 FOOTER，CI 生成链路从未执行
  `inject_social_domains.py`，因此 24 个新闻页都没有品牌域名文字；此前 bot
  提交跳过闸门所以 4f 从未对它们生效。

修复（本地与远端 CI 连续状态对齐 + 源头根治）：

- **回补**：从推送前远端 commit `a6c3454` 取回 20 个新闻页与 3 个状态文件
  原始字节，`news_state.posted` 恢复 78 条；全站 165 页注入域名块，
  sitemap 重建为 164 条 URL（含全部新闻页与 9 个 PCB 页）。
- **根治生成链路**：`.github/workflows/news-auto.yml` 在 `Normalize` 之后、
  `Rebuild sitemap` 与 `verify --gate` 之前新增幂等步骤
  `python3 scripts/inject_social_domains.py`，此后每日新生成的新闻页自动带
  域名块；无漂移时写 0 文件。
- **闸门漏洞根治**：`verify_seo.py` 的 `4f` 逐页检查原用 `S(pages)`，在
  `--global-only`（CI 无脏模块的 gate）下得到空集、逐页检查被静默跳过，
  增量模式也只查脏页——这是历史页缺陷能长期潜伏的机制原因。改为始终使用
  完整 `pages`（该模块已标 `force_global=true`），与「全局不变量始终使用完整
  页集」的既定语义一致；`--all` / `--global-only` / `verify --gate` 三模式复验全绿。
- **验证**：全站 `PASS=51 WARN=0 FAIL=0`；`workarea.py audit` PASS；
  165/165 页含域名块、`threads.net` 0 残留；注入器与 sitemap 幂等复跑 0 写入。

**制度教训（写入 WORKFLOW.md）**：以远端 tree 为 base 的增量推送，必须先把
本地工作区与远端 CI 自动生成的产物对齐，否则「本地相对远端有差异」会把
CI 连续状态误判为待覆盖的旧快照。

---

## [2026-11-16] · footer 动态域名文字改为自有品牌 Anchormere.com（全站同步检查）

用户指示「动态图标动态加载可以显示为 Anchormere.com，其他内容同步检查，不要有错漏」。
把 2026-11-15 的「平台域名」方案从 `www.threads.net` 整体改为**本站自有品牌域名**：

- **单一数据源** `scripts/social_links.json` 升到 v4：单条 profile
  `href=https://anchormere.com/`、`display=Anchormere.com`、
  `aria-label=Anchormere.com home`（中文「Anchormere.com 首页」）、
  `rel=noopener noreferrer`；`pages=["*"]`、`allow_protected=true` 不变。
  新增 `display` 字段承载品牌大小写，生成器与 4f 闸门强制其与 href 同源。
- **生成器** `scripts/inject_social_domains.py`：新增 `display_of()` / `norm_host()`，
  `validate()` 增加 charset 与同源校验；静态兜底文字、`data-domain`、`title`、
  占位宽度全部改用 display。保留 `--rollback` 与历史图标痕迹迁移。
- **加载器** `assets/social-domains.js`：仍 `defer` + `requestIdleCallback` +
  `URL()` 从 href 派生；读取 `data-domain` 的品牌写法用 `textContent` 动态写入，
  若与 href 不同源自动回退为真实 hostname，打 `data-domain-ready=1`。
  零 fetch / 零 innerHTML / 零图标资源 / 零 CLS 不变。
- **4f 闸门改为数据源驱动**：期望值全部从 `social_links.json` 推导，逐页校验
  `href` / `display` / `aria-label` 与配置逐字一致、display 与 href 同源、
  占位锁定、双语属性、禁止 `noscript` 与第三方 CDN；新增全站 `threads.net`
  残留检查、动态加载器 `new URL(` / `data-domain-ready` / `textContent` /
  `requestIdleCallback` 不变量检查；`data-domain` 正则放开品牌大小写。
- **制度同步**：`modules.json` 的 `social-domains` title / note、`WORKFLOW.md` §10
  与模块表；`llms.txt` 与 `SEO与SEM关键词地图.md` 核查后无相关登记，无需改动。
- **全站 145 页重注入**：旧 `www.threads.net` 块整段替换，其它内容零改动；
  生成器二次运行 0 写入；`verify_seo.py --all` 与 `workarea.py audit` 全通过。
- **边界**：链接指向本站首页，不声称任何社媒官方账号 / 合作 / 认证，
  `Organization.sameAs` 不在此模块改动。
- **推送状态**：2026-11-16 已随单个 commit 推送上线（含此前积压的 PCB 板块
  与社媒域名文字方案）。用户侧提供 PAT 后，以远端 main tree 为 `base_tree`
  构造单个 commit，经 Git Data API 更新 main ref；推送前 GitHub 连接器未授权
  （OAuth 网关返回 `Connector "github" is not authorized`），故先暂存本地。
  凭据用后立即清理，并建议用户在 GitHub 设置中吊销该 PAT。

---

## [2026-11-15] · PCB 产业链板块 + 上下游 / AI 趋势长尾词

用户问「业务内容有没有 PCB 相关的，如果没有请添加相关板块以及上下游长尾词，
特别是热门趋势 AI 相关等」。审查结论：站点**已有零散 PCB / PCBA 内容**
（`pcb-assembly-shenzhen` / `pcba-contract-manufacturer` / `tablet-pcba-sourcing` /
`ai-data-center-sourcing` 等），但**没有板块枢纽、没有上下游产业链长尾词、
没有 PCB × AI 趋势词**。按「核心目标不变、既有页零改动」补齐：

- **新增数据源**：`scripts/pcb_board.json`（上中下游 3 段分组、8 个 cluster
  slug、6 条 2026 AI 算力趋势词、4 条联网校验返回 200 的公开来源完整 URL、
  边界与免责声明、FAQ）；`scripts/build_pcb_hub.py` 渲染枢纽页。
- **新增枢纽页**：`pcb-supply-chain.html`（`CollectionPage + hasPart` /
  `BreadcrumbList` / `WebPage.citation` / `FAQPage`，趋势词表、完整
  `Source URL:` 明文、编辑标准页与案例枢纽内链）。
- **新增 8 个长尾页**（`cluster=pcb`，mother 反链枢纽页）：上游
  `ccl-copper-clad-laminate-sourcing`（FR-4 / 高 Tg / prepreg / IPC-4101）、
  `low-loss-m8-m9-laminate`（HVLP / Q-glass / Dk-Df）；中游
  `high-layer-count-pcb-ai-server`（20–30 层 / 40+ 背板）、
  `hdi-msap-anylayer-pcb`、`abf-fcbga-ic-substrate`；下游
  `800g-1-6t-optical-module-pcb`、`ai-server-pcba-ems`、
  `liquid-cooling-cold-plate-sourcing`（冷板 / UQD / CDU）。
- **真源纯追加**：`longtail_seeds.json` 36→44（0 行删除）、
  `longtail_depth.json` pages 36→44 / 新增 `clusters.pcb`；176 条工程笔记与
  44 个页级 h2 全部唯一，3g 相似度闸门继续通过。
- **制度同步**：`modules.json` 新增 `data-pcb` / `pcb-hub` 模块（排在 `engine`
  之前先认领），`longtail` 登记 44 页，`data-longtail` 增加 `pcb-hub` 依赖；
  `verify_seo.py` 新增 `3h` 数据源驱动闸门（分组 / 趋势 / 来源 / 归属 /
  枢纽内链 / 反链 / sitemap）；`WORKFLOW.md` §11、`llms.txt`、
  `SEO与SEM关键词地图.md` §16 同步。
- **验证**：全站 `PASS=51 WARN=0 FAIL=0`；`workarea.py audit` 归属完整；
  既有 136 个 HTML 逐页 sha256 比对**零改动**；sitemap 144 条 URL；
  新增 9 页已注入社媒域名文字（4f）。
- **边界**：标准名仅编辑性引用，不主张认证；层数 / 材料等级 / 交期为公开
  报道的行业典型区间，**不是** Anchormere 报价、能力或承诺；不编造客户 /
  价格 / 资质，不预留资质占位；公开来源非客户项目、非背书。
- **状态**：本批先本地落地，2026-11-16 用户侧提供 PAT 后随同一单 commit
  推送上线；此前 GitHub 通道不可用（连接器未授权 / 无凭据），故暂存本地。

## [2026-11-15] · 同日修订：去掉图标，改为动态展示域名文字（无图标资源）

用户明确要求「为什么要用 threads 图标？直接动态展示域名即可」。图标方案
（SVG 资源 / fetch / 品牌徽标合规 / 失败降级）对「显示一个域名文字」属于过度设计，
整体拆除，改为纯文字动态展示：

- **删除**：`assets/threads.svg`、`assets/social-icons.js`、
  `scripts/inject_social_icons.py`（不再有任何图标 / 徽标 / 图片资源）。
- **新增**：`assets/social-domains.js`（defer + `requestIdleCallback`，从 `<a href>`
  用 `URL()` 派生域名并 `textContent` 写入；**零 fetch、零第三方请求、零 SVG**）、
  `scripts/inject_social_domains.py`（幂等可逆生成器）。
- 静态 HTML 保留 `<a href>` + `aria-label` + `data-zh-attrs` + `title` +
  **初始就可见的域名文字**（放在锁定尺寸的占位内），→ 0 CLS；域名由 `href`
  单一派生，配置里不存第二份文案。爬虫、禁用 JS、脚本加载失败的浏览器都能
  读到域名；`defer` 脚本再从 `href` 派生并动态写入一次（动态展示 + 一致性校正）。
- 生成器**内置历史图标痕迹迁移**：`strip_block()` 同时清理新旧两套标记块与
  script，从图标版重跑可一次替换干净，`--rollback` 可回到 `HEAD` 字节一致。
- 制度同步：模块 id `social-icons` → `social-domains`（`modules.json` 路径 / 构建命令
  / 全局不变量描述、`WORKFLOW.md` §10 与模块表；`llms.txt` 只泛述制度文件、无模块
  清单，故无需改动）、`verify_seo.py` 4f 闸门改为校验域名文字 / 占位 / 零图标资源
  / 无第三方热链，并强制检查 `threads.svg` / `social-icons.js` /
  `inject_social_icons.py` 不得残留。
- 核心目标、引流 / 询盘 / 关键词覆盖 / 转化路径、其余页面内容均不变；仍以平台域名
  `https://www.threads.net/` 启用，`pages=["*"]`、`allow_protected=true` 在此显式声明。

---

## [2026-11-15] · 新增社媒图标动态加载模块（默认零侵入 / 可逆）

- 新增 `scripts/social_links.json` 单一数据源、`assets/threads.svg`（本地反白版，
  不热链 Meta CDN）、`assets/social-icons.js`（defer + `requestIdleCallback` +
  同域 fetch 注入 + 失败文字降级）、`scripts/inject_social_icons.py`（幂等生成器）。
- **初始 HTML 只输出静态语义**（`<a href>` + 固定 24×24 占位 + `aria-label` +
  `data-zh-attrs`），图标本体在页面加载空闲期动态注入；不执行 JS 的爬虫仍能读到
  外链，注入不改变布局尺寸 → 0 CLS，不抢 LCP，不引入第三方请求。
- **默认零侵入**：`profiles` / `pages` 为空时生成器连页面都不读取，全站 HTML
  零写盘、零 diff、零部署；`protected` 核心转化页默认跳过。清空配置后
  `--rollback` 一键还原。真实主页 URL 到位前不编造、不预置占位值。
- 登记 `modules.json` 的 `social-icons` 模块（排在 `engine` / `assets` 之前先认领
  文件）、`verify_seo.py` 4f 闸门（未启用时 no-op PASS；启用后校验静态链接、
  占位尺寸、双语 aria、rel 与无第三方热链）。初版默认零侵入，全站页面零改动。

### 同日激活：按用户指示改用平台域名

- `profiles[].href` 使用 `https://www.threads.net/`，`pages=["*"]` 全站 footer，
  `allow_protected=true` 显式放行 `index.html` / `contact.html`（按制度在此声明）。
- **链接语义修正**：域名入口不等于公司账号，故 `aria-label` 只用平台名 `Threads`、
  `rel` 去掉 `me`（仅保留 `noopener noreferrer`），不声称官方账号、不暗示合作。
  `rel` 改为按 profile 可配置，只有真实自有账号页才允许加 `me`。
- 生成器写入 **136 个 HTML 页面**；逐页与 `HEAD` 比对证明：剥离「1 行 defer 脚本 +
  1 个 footer 标记块」后**字节完全一致**，其余内容零改动（`git diff` 的 52 个
  deletion 只是 footer 单行被拆成多行的行级表示，原内容完整保留）。
- 全站 `verify_seo.py` `PASS=46 WARN=0 FAIL=0`；生成器二次运行 `0 页写入`；
  Chromium 抽测首页与长尾页：域名链接静态可见、图标空闲期动态注入、24×24 锁定。

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
