# Anchormere · SEO / SEM / GEO 关键词地图

> 用途：把"SEO 自然流量 + SEM 付费投放 + GEO（生成式引擎优化/AEO）"统一到一套关键词与落地页体系，让品牌词、母品类词、长尾产品词都能被搜到，并全部导向 `contact.html` 的一键询单转化。
> 运营主体：深圳森亚实业有限公司（Shenzhen Senya Industrial Co., Ltd.）
> 站点：`https://anchormere.com` · GA4 测量 ID 已配置 `G-EZE1LV2MRH`（`assets/consent.js` 的 `GA4_ID`）
> 表单后端：Web3Forms 静默收单（`contact.html` 的 `access_key` 已配置，提交经服务端转发至 `Anchormere@gmail.com`，电话必填）

---

## 1. 策略分层（漏斗）

| 层级 | 意图 | 典型词 | 落地页 | 转化动作 |
|---|---|---|---|---|
| **品牌词** | 已知道我们 | anchormere, 锚泊, anchormere sourcing | `index.html` / `about.html` | 询单 / WhatsApp |
| **母品类词** | 找"中国采购/大湾区制造" | china sourcing agent, shenzhen manufacturing, GBA OEM, 大湾区代工 | `supply-base.html` `capabilities.html` | 选品类 → 询单 |
| **长尾产品词** | 找具体品类 OEM | tws earbuds oem shenzhen, pcb assembly shenzhen | 长尾落地页（见 §3） | 一键 Get a Quote |
| **对比/竞品词** | 比供应商 | anchormere vs [竞品], hqtronics alternative | 对应品类页 + `faq.html` | 询单 + 信任背书 |
| **GEO/AEO 问答** | 问"怎么/哪里" | where to manufacture earbuds in shenzhen, how to source PCBA china | 长尾页 + `llms.txt`（已部署） | 询单 |

---

## 2. 品牌词与母品类词（自然 + 付费都投）

**品牌词（精确匹配，防截流）**
- `anchormere`、`anchormere sourcing`、`anchormere 深圳森亚`、`锚泊 采购`、`buyeex`（商标词）
- 动作：品牌词设为"自有品牌保护"广告组，否定竞品；同时保证官网品牌词首位。

**母品类/主题词（短语+广泛，覆盖主题）**
- 英文：`china sourcing agent`、`shenzhen sourcing company`、`greater bay area manufacturing`、`OEM manufacturer China`、`China contract manufacturer`、`PCB assembly China`、`electronics manufacturing Shenzhen`、`private label electronics China`
- 中文：`深圳 采购代理`、`大湾区 代工`、`中国 OEM 制造`、`电子产品 贴牌`、`PCBA 采购 深圳`、`智能硬件 供应链`
- 落地页：`supply-base.html`（供应基地）、`capabilities.html`（能力）、`index.html`（首页）、`consumer-smart-electronics.html`、`smart-toys-devices.html`

---

## 3. 长尾产品词 → 落地页映射（已生成并持续扩充）

每个长尾页都已内置：双语 H1/H2、能力清单、规格/时效表、FAQ、Service JSON-LD、面包屑、hreflang、内链回母品类 + `contact.html` CTA。

| 落地页（slug.html） | 英文主词 | 中文主词 | 母品类 |
|---|---|---|---|
| `earbuds-oem-shenzhen.html` | TWS Earbuds OEM Shenzhen | TWS 耳机 OEM 深圳 | Consumer & smart electronics |
| `smart-toy-manufacturer-gba.html` | Smart Toy Manufacturer Greater Bay Area | 智能玩具制造商大湾区 | Smart toys & devices |
| `tablet-pcba-sourcing.html` | Tablet & Phone PCBA Sourcing China | 平板与手机 PCBA 采购中国 | Consumer & smart electronics |
| `wearable-oem-shenzhen.html` | Wearable OEM Shenzhen | 可穿戴 OEM 深圳 | Consumer & smart electronics |
| `smart-home-module-sourcing.html` | Smart Home Module Sourcing | 智能家居模组采购 | Consumer & smart electronics |
| `usb-c-charger-oem.html` | USB-C Charger OEM China | USB-C 充电器 OEM 中国 | Consumer & smart electronics |
| `educational-robot-manufacturer.html` | Educational Robot Manufacturer China | 教育机器人制造商中国 | Smart toys & devices |
| `oled-display-module-sourcing.html` | OLED & LCD Display Module Sourcing | OLED 与 LCD 显示模组采购 | Consumer & smart electronics |
| `plastic-injection-molding-shenzhen.html` | Plastic Injection Molding Shenzhen | 塑胶注塑深圳 | Greater Bay Area supply base |
| `metal-sheet-fabrication-dongguan.html` | Metal Sheet Fabrication Dongguan | 钣金加工东莞 | Greater Bay Area supply base |
| `pcb-assembly-shenzhen.html` | PCB Assembly Shenzhen | PCB 组装深圳 | Consumer & smart electronics |
| `iot-sensor-module-sourcing.html` | IoT Sensor Module Sourcing | IoT 传感器模组采购 | Consumer & smart electronics |
| `drone-parts-manufacturer-gba.html` | Drone Parts Manufacturer Greater Bay Area | 无人机零件制造商大湾区 | Greater Bay Area supply base |
| `ev-charger-components-sourcing.html` | EV Charger Components Sourcing | 充电桩部件采购 | Greater Bay Area supply base |

**买家身份 / 场景词（新增，2026-11-06）**——补足"找具体品类"之外的"我是谁、我要干什么"层。每个页均内置双语 H1/H2、FAQ（FAQPage JSON-LD）、Service 实体（GSC 商品摘要合规，无 offers）、面包屑、`en/x-default` hreflang、内链回 `supply-base.html` + `contact.html` CTA：

| 落地页（slug.html） | 英文主词 | 中文主词 | 买家角色 |
|---|---|---|---|
| `amazon-private-label-manufacturer.html` | Amazon Private Label Manufacturer China | 亚马逊贴牌制造商 | 跨境电商品牌卖家 |
| `china-sourcing-agent.html` | China Sourcing Agent & Procurement | 中国采购代理 / 国际贸易采购 | 贸易公司 / 采购商 |
| `import-from-china-guide.html` | How to Import from China (2026 Guide) | 如何从中国进口 | 进口新手（引流大词） |
| `hardware-startup-manufacturer.html` | Hardware Startup Manufacturer China | 硬件创业制造商 | 创业 / 众筹项目 |
| `verify-chinese-manufacturer.html` | How to Verify a Chinese Manufacturer | 如何核实中国工厂 | 风控 / 信任建立 |
| `cross-border-ecommerce-sourcing.html` | Cross-border e-commerce Sourcing Guangdong | 跨境电商采购广东 | 线上卖家（已增强） |

**SEM 投放建议**：每页开一个"仅该词"广告组，匹配类型用"词组/精确"，落地页用对应 slug 页（不要都用首页），质量得分更高、转化更便宜。

---

## 4. 竞品 / 对比广告组结构（防御+截流）

| 广告组 | 关键词示例 | 落地页 | 创意要点 |
|---|---|---|---|
| vs 平台型 | `hqtronics alternative`、`made-in-china agent vs`、`alibaba sourcing agent` | `supply-base.html` + `faq.html` | 强调"20+ 已审核工厂（vetted）、48h 报价、整柜拼柜" |
| vs 同行 | `shenzhen sourcing company`、`china sourcing agent review` | `about.html` + `capabilities.html` | 强调"深圳森亚实业有限公司实体、出口单证齐全" |
| 地域截流 | `shenzhen manufacturing partner`、`dongguan metal fabrication` | 对应长尾页 | 强调本地集群与时效 |

---

## 5. GEO / AEO（生成式引擎优化）

- 已部署 `llms.txt`（根目录），列出能力边界、典型买家长尾意图（含 2026 热词）、10 篇带外链来源标注的采购情报简报入口，供 ChatGPT/Perplexity 等引用。条目以 `llms.txt` 实时内容为准，不在本文写死数量。
- 每个长尾页的 FAQ 段落（含 FAQPage JSON-LD）直接回答"MOQ 多少 / 多久报价 / 怎么远程验厂 / 付款方式 / 是否做成品"——这些是 AI 摘要最爱抓取的结构化问答。
- 全站 FAQPage JSON-LD 已补 `speakable`，把语音助手与答案引擎指向页面真实存在的问答 DOM：长尾页 `.qa h3` / `.qa p`，早期框架页 `h3`。由 `html_finalize.py` 收口层保证，生成器与 CI 重生都不会带回旧态。
- 建议在长尾页持续补充"how to / where to / cost of"类段落，提升被 AI 答案引用的概率。

---

## 6. 转化埋点（已上线）

- 全站 `assets/consent.js` 同意后注入 GA4（`G-EZE1LV2MRH`，已配置）。
- 转化事件：
  - `generate_lead` — 表单提交（contact.html 的 RFQ 表单，Web3Forms AJAX POST 成功后触发）
  - `contact_click` — 点击任意 `contact.html` / `.btn-quote` / `.btn-primary` CTA
  - `whatsapp_click` — 点击右下角 WhatsApp 浮窗
- 在 GA4 中把上述三个事件标记为"关键事件（转化）"，并在 Google Ads 里导入，用于 SEM 出价优化。

---

## 7. 上线前待办（需用户提供）

1. **GA4 测量 ID**：已配置 `G-EZE1LV2MRH`（`assets/consent.js` 的 `GA4_ID`）✅ 已完成。
2. **表单后端**：已改用 Web3Forms 静默收单（`contact.html` 的 `access_key` 已配置，转发至 `Anchormere@gmail.com`，电话必填）✅ 已完成。
3. **Search Console / IndexNow**：`robots.txt` 已指向 `sitemap.xml`；`b1700fd697c7492b958b22d8d2adf646.txt` 为 IndexNow key，建议在 Bing/IndexNow 提交。
4. **定期扩词**：长尾种子在 `scripts/longtail_seeds.json`，新增品类直接加一条再跑 `python3 scripts/longtail.py` + `python3 scripts/build_sitemap.py` 即可。

---

## 8. 维护脚本

| 脚本 | 作用 | 何时跑 |
|---|---|---|
| `scripts/longtail.py` | 由 36 条种子生成长尾落地页（含品类专属工程要点 + E-E-A-T 审核署名） | 新增品类时 |
| `scripts/build_sitemap.py` | 扫描全站 `*.html` 生成 `sitemap.xml`（当前 121 条 URL，含业务页 + 资讯 + 简报 + 归档，CI 自动重建；数字以脚本实时输出为准） | 增删页面后 / 每次资讯生成后 |
| `scripts/seo_inject.py` | 给既有页注入 Organization/Breadcrumb/FAQ/Service JSON-LD + hreflang | 改模板后 |
| `scripts/inject_ga4.py` | 给缺 `consent.js` 的页面补齐（已全站覆盖） | 新增页面时 |
| `scripts/news_digest.py` | 每日抓取科技/制造/采购源 → 中英双语摘要落地页（含权威外链 + 明文 URL 来源标注 + 专有名词 + `citation`）→ `/news` 索引封顶 48 篇 + 自动归档分页 → 重建 sitemap | GitHub Actions 每日 cron（北京时间 09:00，含 `workflow_dispatch` 兜底） |
| `scripts/build_briefings.py` | 由 `scripts/briefings.json` 渲染 10 篇采购情报简报（每篇 10 条要点 + 术语表 + 完整 URL 来源标注） | 新增/修订简报内容时 |
| `scripts/enhance_news_citations.py` | 幂等升级历史 digest 页：补明文 URL 来源标注、类目权威外链、专有名词、`Article.citation` | 生成器模板升级后 |
| `scripts/verify_seo.py` | 全站 SEO 验证闭环 + 全局不变量闸门（clean URL 内链 / WCAG lang / 实体 @id 串联 / 无 Product-Offer / `meta keywords` ≤200 字符 / FAQPage `speakable` 等）。项数以 `workarea.py verify --all` 实时输出为准，不在本文写死 | 每次改动后 / CI 提交前闸门 |
| `scripts/site_normalize.py` | 调用收口层对全站 HTML 做幂等规范化（五条不变量，只在内容变化时写文件） | CI 每日 digest 后、sitemap 前；本地生成页后也一样 |
| `scripts/html_finalize.py` | **收口层**：五条全站不变量（clean URL / `lang="zh-CN"` / Article @id / `meta keywords` ≤200 / FAQPage `speakable`）。生成器经 `write_final()` 写盘即最终态，杜绝「CI 重生带回旧模板」 | 新增不变量时；改动须同步 `verify_seo.py` 闸门 |
| `scripts/workarea.py` | 模块化增量制度：`status / plan / apply / verify / init / audit / handoff / freeze`，按内容哈希与依赖闭包只处理脏模块 | 每次改动前后；换模型交接时先看 `handoff` |
| `scripts/health_check.py` | 线上真实响应巡检（核心页状态 / canonical / hreflang / sitemap / 追踪埋点 / 收口层不变量软校验）；CRITICAL 会让 CI 失败并邮件通知 | 每日 `site-health.yml` 自动跑 |
| `scripts/submit_indexnow.py` | 通知 Bing 系引擎重新抓取 | 增删页面 / 回滚后 |

`news-watchdog.yml` 每日 05:00 UTC 检查 `news-auto` 最近成功运行，超 26h 或最近一次失败且已过 2h 时通过 `workflow_dispatch` 自动补跑，不复制生成逻辑。变更台账见 `CHANGELOG.md`，回滚步骤见 `ROLLBACK.md`。

---

## 9. 内容质量与实体权威度（2026-11-07 优化）

- **品类独有内容**：28 条种子各含 `expertise` 字段（工艺/技术要点、买家核对清单、质检与验厂重点 + 2 条专属 FAQ，中英双语），由 `scripts/longtail.py` 渲染为独立区块。28 页两两相似度 **0.607 → 0.488**、相似度 >0.70 的组合 **56 → 0**、前 6 个 h2 完全相同的页 **26 → 14**，消除"批量模板页"特征；平均正文（≥4 字符词）**310 → 401**。（本节为当时 28 条种子时的快照）
- **E-E-A-T 审核署名**：每个长尾页含可见 "Reviewed by the Anchormere sourcing desk" 与 `WebPage.lastReviewed` / `reviewedBy` 结构化数据，二者成对一致并由 `verify_seo.py` 校验。
- **实体单一数据源**：`scripts/org_entity.json` 是全站唯一 Organization 定义（含 `contactPoint` / `telephone` / 街道级 `address` / `logo` / `knowsAbout` / `@id`）。`longtail.py`、`seo_inject.py`、`news_digest.py` 均读取该文件，**109 个页面实体 100% 一致**（含 news 页与归档页），CI 每夜重生不漂移。
- **未编造信息**：未添加 `foundingDate` / `sameAs`（需真实注册信息与外部 URL，待用户提供后直接补入 `scripts/org_entity.json`）；公司资质不提供，站内不新增资质板块、不设占位字段，避免虚构实体信号。
- **回归清理**：`seo_inject.py` 残留的 `Offer`/`offers` 电商字段已移除，防止重注入时带回 GSC 购物误归类。

---

## 10. 新闻外链、来源标注与专有名词（2026-11-07 增强）

- **10 篇全新简报**（非改动既有内容）：跨境电商合规、Incoterms 与到岸成本、OEM/ODM/贴牌、PCBA/SMT 能力表、验厂审核、HS 编码与原产地、出口认证、低 MOQ 试产、充电桩标准、AI 数据中心硬件。每篇 10 条可核对要点，共 **100 条**中英双语内容。
- **外链与来源标注**：`scripts/briefings.json` 是唯一引用池，含 **45 个已 HTTP 校验（43×200 + 2×202，零死链）** 的公开标准机构 / 政府来源 URL。正文以编辑性引用嵌入外链，页尾 "Sources & references" 逐条打印**完整链接网址**（`Source URL:`），可复制、可点击、可独立核验；`Article.citation` 同步声明引用关系。
- **专有名词**：76 个行业术语定义（英文释义 + 中文简注），10 篇简报各带 10–11 条 "Key terms" 词汇表并输出 `DefinedTermSet` 结构化数据；正文术语可点击跳转对应词条。
- **既有 42 篇 digest 页**：按类目补 2 个权威外链、1 个轮转专有名词、明文 URL 来源标注与 `Article.citation`；`content-kind` / `card-title` meta 让索引卡片区分「采购情报简报」与「自动摘要」。
- **根治**：`news_digest.py` 每日生成的新页自动带上述三要素，且引用池与简报共用同一份 `briefings.json`；归档页模板补上 Organization 实体（单一数据源）。CI 每夜重建不会覆盖或漂移。
- **口径边界**：外链均为编辑性引用，明确声明与来源无隶属、不主张背书；未编造认证或第三方背书。全站 `title>60=0`、`desc>155=0`、377 个 JSON-LD 块全部合法、10 篇简报两两相似度最高 0.469（无 >0.70 组合）。

---

## 11. 独立复审与验证闭环加固（2026-11-07）

- **验证脚本自身缺陷**：① 孤儿页检测原先把 `canonical` / `hreflang` 的 `<link href>` 也算作入链，而每页 canonical 都指向自身，导致"无孤儿页"永远 PASS —— 改为只统计 `<a>` 导航链接并排除自引用；② 核心实体检查的 `if` 缩进错误，只检查 `@type` 列表最后一项，已移入循环。
- **中文替代版本声明统一**：`assets/lang.js` 的 `addHreflang()` 原先注入 `hreflang=zh-CN`（指向同一 URL），与静态 `en` / `x-default` 冲突；49 个新闻页还带 `og:locale:alternate=zh_CN`（其余 60 页没有）。站点无独立中文 URL 且 GEO 不打中文市场，故统一删除，生成器与 `enhance_news_citations.py` 幂等清理均已根治；运行时 `document.documentElement.lang="zh-CN"`（无障碍）保留。
- **sitemap lastmod 真实性**：原用文件 mtime，CI checkout 会把全站 mtime 重置为当天，109 条 lastmod 全为同一天（虚假全站更新信号）；改为从各页 `Last updated` / `datePublished` / `lastReviewed` 提取，现分布 **9 个不同日期**。同时把首页从 `/index`（线上 308 重定向、与 canonical 不符、且落在健康检查采样区间）改为根 URL `https://anchormere.com/`（200）。
- **Article.wordCount 准确性**：简报原只统计英文要点 + 术语释义，声明 343–437 词，实际可见正文 774–1005 词；改为按渲染后 `<section class="l1">` 统计可见英文词，10 篇声明值与实际**完全一致**。
- **验证闭环**：`verify_seo.py` 由 18 项扩到 **21 项**（新增中文版本声明、wordCount、sitemap lastmod 三项），当前 **PASS=21 / WARN=0 / FAIL=0**。已模拟 CI 生成新 digest 页，确认无 `zh_CN` 声明、引用/术语/citation/日期/canonical 齐全，重建不漂移。
- **核心目标不变**：引流、询盘、关键词覆盖、转化路径与全部外链/正文内容未削弱；以上均为技术性、标准合规类硬修复。

---

## 12. 第三轮独立复审：内链口径、无障碍与 CI 闸门（2026-11-07）

- **内链 308 重定向**：全站 110 页共 **3785 个 `.html` 站内链接**，线上统一被 Cloudflare Pages 308 到无扩展名 URL，而 canonical / sitemap 早已是无扩展名 —— 内部链接与权威 URL 自相矛盾、每次点击多一跳。新增 `scripts/site_normalize.py`（幂等，只在内容变化时写文件）统一改为 clean URL（`index.html` → `/`，其余 → `/<slug>`），并在 CI 每日 digest 后自动调用；`health_check.py` 的检查目标同步改为 clean URL，避免脚本自身仍依赖 308 路径。
- **WCAG 2.1 AA 3.1.2**：全站 **1133 个中文片段**（852 个 `<p class="cn">` + 281 个 `<span>`）在英文默认状态下无 `lang`，属于 Language of Parts 不达标。统一补 `lang="zh-CN"`；因中文 UI 是同一文档的客户端渲染，`lang.js` 把根 `lang` 切到 `zh-CN` 时这些片段仍是中文，两种状态均成立，无冲突。
- **实体串联**：52 篇新闻/简报的 `Article.author` / `publisher` 原先内联重复 Organization 对象，页面另有 `@id=https://anchormere.com/#organization` 的完整实体块。改为 `{"@id": ...}` 引用，让实体图串联（对应最初「实体结构化数据串联」方向）；`@id` 读取 `org_entity.json`，不硬编码。
- **页内死锚**：低 MOQ 简报正文两处引用 `[[nnn|NNN agreement]]`，但 `nnn` 不在该页术语列表，渲染出 2 个 `#term-nnn` 死锚。数据源 `briefings.json` 把 `nnn` 补入该页 `terms`（NNN 定义本就在 glossary），重生成后 `DefinedTermSet` 与页内 id 对齐；全站页内死锚 0。
- **CI 质量闸门**：`news-auto.yml` 每日自动 `git push`，此前**从不运行验证脚本**（历史上 CI 曾把 `zh-CN` / `Offer` 残留带回）。现于 commit 前插入 `python3 scripts/verify_seo.py`，任一 FAIL 即终止任务、不提交；并新增 normalize 步骤，防止新生成页把旧口径带回来。
- **验证闭环**：`verify_seo.py` 由 21 项扩到 **24 项**（新增 clean URL 内链、中文片段 lang、Article 实体 @id 串联），当前 **PASS=24 / WARN=0 / FAIL=0**。整条生成链路重跑前后文件哈希完全一致（幂等）；CI 模拟新 digest 页经规范化后 10 项不变量全通过。
- **终检数据**：110 HTML / 109 页面；`title>60=0`、`desc>155=0`、377 个 JSON-LD 块全部合法、页内死锚 0、外链缺 `noopener` 0、站内 `.html` 链接残留 0、中文块缺 lang 0、口径残留（`certified factories` / `no MOQ` / `Offer` / `Formspree` / `zh-CN hreflang`）全 0；简报两两相似度最高 0.469（无 >0.70 组合）。
- **核心目标不变**：引流、询盘、关键词覆盖、转化路径与全部外链/正文内容未削弱；以上均为技术性、标准合规类硬修复，按长期授权直接执行。

---

## 13. 热搜词诊断与扩词（2026-11-08）

### 13.1 诊断结论

对现有 28 条种子、`org_entity.json` 的 28 条 `knowsAbout` 与 §2 母品类词做了一次
「是否属于目标群体当期热搜词」复核，依据为 2025–2026 年公开的采购趋势资料与
买家实际检索问句：

- 现有词条属于**稳定的交易意图长尾词**（品类 OEM、代工模式、找厂、验厂、进口流程），
  采购意图强、转化价值高，但**不是 2026 年的趋势型热搜词**。
- 命中趋势的仅约 6 条：`low MOQ` / `small batch`（2026 已成默认）、
  `how to import from China`、`Amazon private label`、`EV charger components`、
  `drone parts`。
- **两类高热主题完全缺席**：
  1. **政策 / 成本剧变**：美国 800 美元小额免税终止、欧盟 150 欧元低值免税取消，
     使 `landed cost` 建模从可选表格变成采购决策中心；`China Plus One` 多元化被
     多数供应链高管列为 2026 首要战略；HS/HTS 归类成为「利润中心」而非文书工作。
  2. **2026 爆发品类**：AI 原生硬件与智能眼镜、服务/清洁/人形机器人、
     便携与家庭储能、电动两轮车、轻量化户外露营装备。

结论：**不是所有现有词条都属于目标群体热搜词**，故按长期授权直接扩词。

### 13.2 新增热词落地页（8 条，非改动既有内容）

| 落地页（slug） | 目标热搜词（英文主词） | 类型 | cluster |
|---|---|---|---|
| `china-landed-cost-2026` | landed cost from China 2026 / de minimis exemption ended / total landed cost calculator | 引流大词·买家指南 | knowledge |
| `china-plus-one-sourcing` | China Plus One sourcing / dual sourcing strategy / Vietnam vs China manufacturing | 引流大词·买家指南 | knowledge |
| `hts-code-tariff-classification` | HTS code classification / HS code for China imports / Section 301 duty / rules of origin | 引流大词·买家指南 | knowledge |
| `ai-hardware-smart-glasses-oem` | AI hardware manufacturer China / smart glasses OEM Shenzhen / AI wearable ODM | 爆发品类 | electronics |
| `service-robot-manufacturer-china` | service robot manufacturer China / commercial cleaning robot OEM / humanoid robot components | 爆发品类 | industrial |
| `portable-power-station-oem` | portable power station OEM China / home energy storage manufacturer / LiFePO4 battery pack assembly | 爆发品类 | industrial |
| `e-bike-manufacturer-china` | e-bike manufacturer China / electric two-wheeler OEM Guangdong / e-bike parts supplier GBA | 爆发品类 | industrial |
| `outdoor-camping-gear-oem` | lightweight camping gear OEM China / folding camping furniture OEM / low MOQ outdoor products | 爆发品类 | industrial |

每条均含 8 项能力清单、8 行规格表、12 个相关词、5 条买家问答、2 条品类参考、
品类专属 `expertise`（工艺 / 买家核对清单 / QC / 专属 FAQ，中英双语），
以及 ≤60 字符的 SERP 标题与 ≤155 字符的描述。

### 13.3 口径与边界

- **GEO 不打中文市场**：新增词以英文为主，中文仅作页面内客户端语言切换，
  不新增独立中文 URL、不投放中文市场。
- **不编造信息**：关税税率、认证与准入、电芯与算法能力均明确写出责任边界 ——
  Anchormere 只负责出口侧单证、物理制造与整合，不充当进口商记录、不发布约束性
  归类/税率裁定、不出具 UN38.3 / IEC / 型式认证报告、不做芯片设计与核心算法研发。
  具体税率与合规以买家持牌报关行、指定实验室与入境当日官方税则为准。
- **核心目标不变**：引流、询盘、关键词覆盖、转化路径与 GA4 / Consent Mode / CTA 跟踪
  未削弱；新增页均内链回母品类与 `contact.html` CTA。
- **增量落地**：仅 `data-longtail → longtail → config` 闭包重建；`org_entity.json`
  的 `knowsAbout` 未扩（属 `data-org` 强依赖，扩它会触发全站复验），主题信号由
  新页自身的 `Service` 实体、`llms.txt` 意图与 Pages 入口承载。
- 枢纽页（`index.html` 属 protected）与新闻/简报/框架页零改动；新页入链来自
  长尾页的 `related` 区与 buyer-guide 区，sitemap 自动收录。

### 13.4 复核方法

以后复核热搜词只需：对照当期买家检索问句与采购趋势资料，检查
`scripts/longtail_seeds.json` 的 `kw` / `related` 与 `llms.txt` 的
"Typical buyer searches we answer" 小节；缺口以新增种子方式补齐，
按 `WORKFLOW.md` 的增量流程重建，不改既有页正文。

## 14. 公开案例编排与来源标注（2026-11-08）

- **案例来源**：`scripts/case_references.json` 是唯一数据源，收录 11 条联网核验的真实公开案例——Reuters（Shein 越南保税仓 15→6 公顷、供应商回流番禺）、QIMA《2026 Q3 Barometer》（中国占北美验货量 35%）与后续分析、Asia Tech Lens（China+1 三变量）、TRADLINX（Apple 印度产能）、U.S. CBP 裁定 N357652 / NY N428911 / EAPA 案 8247、Tandom 归类税差算例、安克创新 2025 年报与媒体中心。
- **来源标注**：每条案例在枢纽页与长尾页均保留完整 `Source URL:` **明文**，并附可点击外链；`citation` 写入 `CollectionPage.hasPart` 结构化数据。用户要求的「保留外链链接网址作为来源标注」在本批落地。
- **口径边界**：明确声明为行业公开案例，**不是** Anchormere 客户项目、合作或背书；「采购启示（Buyer takeaway）」为本站对公开事实的解读，不代表原来源结论。`verify_seo.py` 闸门 3f 阻断「无来源案例」与「our client / our customer」等背书措辞。
- **覆盖**：`sourcing-case-studies.html` 枢纽页 + 36/36 个长尾页案例板块（每页按主题匹配最多 2 条），形成 41→76 条案例引用与 36 条枢纽页内链，兼顾关键词覆盖与可核验权威度。
- **资质处理**：按用户决定，资质不提供、不预留板块或占位字段；`sameAs` 待外部 URL 到位后补入，当前不预置空值。
