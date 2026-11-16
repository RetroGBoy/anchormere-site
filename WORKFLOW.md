# Anchormere 站点 · 模块化增量工作制度

> 本文件是工作方式的**唯一制度说明**，与 `scripts/modules.json`（分区与依赖）、`scripts/module_state.json`（内容哈希基线）共同构成一套**与模型无关**的协作协议。
> 任何新会话、新模型、新机器接手本项目：**先读这三个文件，再动手**；不需要、也不应该依赖聊天记录里的历史结论。

---

## 1. 制度要解决的问题

旧模式是"全量重跑型"：每次改动都重写全部页面、重复读取同一批文件十余遍、全量扫描校验、整站重新部署。由此产生四类消耗：

| 消耗 | 旧模式 | 本制度 |
|---|---|---|
| 磁盘写入 | 生成器无条件写全部页面，内容没变也产生 mtime 漂移与 git diff | 字节相同即跳过写盘，不进提交、不触发部署、不污染 sitemap lastmod |
| 重复 IO | `verify_seo.py` 把同一批 HTML 反复 `open()` 十余次 | 页面一次性读入内存缓存，全站只读一遍 |
| 无效扫描 | 每次都扫全站，包括没需求、没问题的板块 | 只对脏模块及其依赖闭包读取 / 重建 / 校验 |
| 认知重建 | 换模型后要重新理解全站、重新全量审查 | 状态、分区、依赖、红线全在仓库里，`handoff` 一条命令即可交接 |

核心目标**始终不变**：引流、询盘、关键词覆盖、转化路径。本制度只改工作方式，不动业务内容与线上效果。

---

## 2. 分区：工作区域按板块隔离

`scripts/modules.json` 的 `modules` 数组自上而下匹配，**第一个命中的模块即该文件归属，一个文件只属于一个模块**。未归属文件会被 `audit` / `status` 报警，防止制度出现盲区。

| 模块 id | 板块 | 策略 | 大致文件数 | 生成器 |
|---|---|---|---|---|
| `governance` | 制度与驱动器 | governance | 5 | — |
| `data-org` | Organization 单一数据源 | manual | 1 | — |
| `data-longtail` | 长尾页数据源 | manual | 1 | — |
| `data-depth` | 品类专属深度内容（差异化 / E-E-A-T） | manual | 1 | — |
| `data-cases` | 公开案例数据源（含来源 URL） | manual | 1 | — |
| `data-briefings` | 简报数据源 | manual | 1 | — |
| `social-domains` | 品牌域名文字动态展示（无图标资源，默认零侵入） | auto | 3 | `inject_social_domains.py` |
| `data-news` | 新闻去重状态 | auto | 1 | — |
| `engine` | 生成器 / 校验器代码 | manual | 20+ | — |
| `briefings` | 采购情报简报 | auto | 10 | `build_briefings.py` |
| `news-digest` | 每日新闻摘要 | **scheduled** | 42 | `news_digest.py` |
| `news-index` | 新闻列表 / 归档 | auto | 2 | 随 digest 生成 |
| `cases-hub` | 公开案例枢纽页 | auto | 1 | `build_cases.py` |
| `editorial` | 编辑标准 / 内容核验页 | auto | 1 | `build_editorial.py` |
| `longtail` | 长尾关键词品类页 | auto | 36 | `longtail.py` |
| `framework` | 框架页 / 核心转化路径 | **manual** | 28 | 人工维护 |
| `assets` | 静态资源 | manual | 若干 | 人工维护 |
| `config` | sitemap / robots / llms.txt 等 | config | 8 | `build_sitemap.py` |
| `ci` | GitHub Actions | manual | 4 | 人工维护 |
| `docs` | 报告与说明 | manual | 若干 | 人工维护 |
| `archive` | 部署包归档 | **frozen** | 1 | 不读不算 |

策略语义：

- **auto** — 由生成器产出，依赖变更时允许自动重建。
- **manual** — 人工维护页，自动流程**只读不写**，仅做校验。对应"没有问题的不做变动"。
- **scheduled** — 只由每日定时 CI 处理；增量流程默认**连扫描都跳过**。对应"没有需求的不用重新扫描"。
- **frozen** — 归档大文件，默认连哈希都不计算（省约 3 MB 无谓 IO），仅 `--include-frozen` 时纳入。
- **config / governance** — 前者由专用生成器重建，后者只触发状态重算、不触发页面重建。

---

## 3. 三条硬机制

### 3.1 无变更不落盘（物理保证）

所有生成器写 HTML 统一经 `scripts/io_util.py::write_final()`：先调用 `html_finalize.normalize()` 归一化为**线上最终态**，再走 `write_if_changed()`，内容字节相同就直接返回、不写文件。非 HTML 产物（sitemap.xml、JSON 状态）用 `write_if_changed()`。

这里顺带根治了一个历史架构缺陷：以前生成器输出的是"中间态"（含 `.html` 内链、中文块缺 `lang`、Article 内联实体），必须靠后续 `site_normalize.py` 改回，因此**单独重跑一次生成器会先写 38 个文件、再被改回**，产生双重写盘与 mtime 漂移。现在归一化前置到写盘之前，生成器单独重跑即 **零写盘、零 diff**；`site_normalize.py` 保留为兜底检查（`--check` 应为 0 个）。

`scripts/html_finalize.py` 是纯函数模块，生成器与兜底扫描共用同一套规则，避免两处口径漂移。这样"没有问题的不做变动"不再靠自觉，而是脚本层强制，同时避免 mtime 漂移导致 `sitemap.xml` 的 `lastmod` 被误刷新成当天。

### 3.2 依赖闭包决定影响范围

注册表里每个模块声明 `invalidates`（本模块变更会波及哪些下游）。`workarea.py plan` 沿这些边做闭包扩散，只把闭包内的模块纳入重建与校验。

典型闭包：

```
data-longtail  →  longtail  →  config(sitemap)
data-cases     →  cases-hub + longtail → config(sitemap)
data-depth     →  editorial + longtail  → config(sitemap)
data-briefings →  briefings →  config(sitemap)
data-news      →  news-digest → news-index → config
engine         →  longtail + briefings + news-* + config   （并提示 framework 人工复核）
data-org       →  全部生成页 + config                      （并提示 framework 人工复核）
assets / config 变更 → 强制跑一次全站全局不变量
```

改一个关键词种子，只会重建长尾页集合和 sitemap；**新闻、简报、框架页一律不动**。

### 3.3 生成器范围闸门

`workarea.py apply` 通过环境变量 `WORKAREA_FILES` 下发本次允许处理的文件名。生成器在循环开头调用 `io_util.selected()`，范围外的文件**连读取都不发生**。单独手动运行脚本时环境变量为空，行为退化为全量，保持兼容。

---

## 4. 校验分层

| 层级 | 内容 | 何时跑 |
|---|---|---|
| **local（逐页）** | hreflang、中文版本声明、canonical、JSON-LD、Organization 一致性、E-E-A-T、`wordCount`、clean URL、`lang`、Article `@id` | 仅对脏模块闭包内的页面 |
| **global（全站不变量）** | 孤儿页、sitemap lastmod、robots AI 爬虫、IndexNow、GSC/Bing 验证、实体类型覆盖、SEO URL 绝对形式 clean URL（无 .html）、meta description 有效性（60–170 字符、无 RSS 噪声词）、站内锚点 0 死锚 | 每次校验跑一次（基于单次读取缓存，开销极小） |
| **full（全量复审）** | 上述全部，对全部页面 | 仅 `verify --all`、显式复审需求、或 `engine`/`data-org` 等强变更触发 |

`verify_seo.py` 退出码：`1 = FAIL 阻断推送`，`2 = WARN 提示`，`0 = PASS`。24 项 PASS 基线保持不变。

---

## 5. 红线：核心目标不变

`scripts/modules.json` 的 `protected` 列表包含 `contact.html`、`index.html`、`assets/consent.js`、`assets/consent.css`、`assets/lang.js`、`_headers`、`robots.txt`。自动重建与批量脚本**禁止写入**这些文件；`apply` 会在每次构建后比对快照，若生成器误写则立即还原并中止。

红线业务含义：引流、询盘、关键词覆盖、转化路径、GA4 / Consent Mode v2、CTA 跟踪不得因"顺带优化"被改动。需要改时必须显式声明目标文件与理由。

**结构化数据红线**：全站禁止声明 `@type: Product` / `Offer`，也禁止 `offers` / `aggregateRating` 字段。本站是 B2B 询价制、无固定价格与评价体系，Google 产品摘要会强制要求 `Product` 补齐 `offers` / `review` / `aggregateRating`；虚构这些字段既违反 Search Essentials，又会让站点被重新误归类为"电商/购物"。主题实体统一使用 `@type: Service`（关键词保留在 `name` / `description` / `serviceType`，实体链经 `provider.@id` 串联唯一 Organization），由 `verify_seo.py` 的 3d 全局闸门强制，不受增量范围影响。

---

## 6. 标准作业流程（SOP）

```bash
# 0) 接手 / 换模型后第一件事：读交接单
python3 scripts/workarea.py handoff

# 1) 看状态（默认零内容读取，只比 git diff 与基线）
python3 scripts/workarea.py status

# 2) 声明本次要动的板块，先看影响范围（不执行）
python3 scripts/workarea.py plan --module longtail
#    或按文件声明：plan --change scripts/longtail_seeds.json
#    或改了某页：  plan --change about.html

# 3) 确认计划无误后执行：只重建闭包、只校验脏模块
python3 scripts/workarea.py apply --module longtail

# 4) 推送前最小闸门（无变更时只跑全局不变量）
python3 scripts/workarea.py verify --gate

# 5) 仅在显式复审需求时做全量
python3 scripts/workarea.py verify --all
python3 scripts/workarea.py audit
```

规则：

- **没有需求时什么都不做**。`status` 全 CLEAN 时，`apply` 会直接输出"不重建、不扫描、不写盘"并退出。
- **不要为了"顺手刷新"全量重跑生成器**；用 `--module` 精确声明。
- **判断变化一律用内容哈希，不用 mtime**（CI checkout 会把全站 mtime 重置成当天）。
- `status --deep` 强制内容哈希复核；`status --include-frozen` 才把归档纳入。
- 临时让某板块完全退出扫描：`python3 scripts/workarea.py freeze <id>` / `unfreeze <id>`。
- 新增文件后必须跑 `audit`，把新文件补进 `modules.json` 的对应模块，否则制度有盲区。

---

## 7. 换模型 / 换会话 / 换机器的交接协议 ⭐

这是本制度最重要的用途。设计前提：**认知不存于对话，只存于仓库**。

1. `module_state.json` 纳入 git，记录每个模块的内容哈希、文件数、上次验证时间与结论。
2. 新环境 clone 后先跑一次 `status --deep`（一次全量内容哈希，开销约几十毫秒）复核基线，之后 `status` 回到零内容读取的增量模式。state 随代码一起提交，因此**每次正常提交后基线恰好落后 1 个 commit 属预期，不提示**；只有落后多个提交或无法判定（换机器 / 换模型 / 他人连续提交）时才提示深扫。
3. 状态写入本身幂等：只有模块哈希或验证结论实质变化才落盘，避免 CI 在没有新内容时产生"只更新时间戳"的空提交与无意义部署。
4. `python3 scripts/workarea.py handoff` 打印自包含检查单：事实来源、五条硬纪律、禁止事项、标准命令、当前脏模块。把它贴给新模型即可，无需搬运聊天记录。
5. `llms.txt` 内含 `Maintenance & governance` 小节，外部 AI 抓取站点时也能读到同一套分区约定。
6. 制度本身（`WORKFLOW.md` / `modules.json` / `workarea.py` / `io_util.py`）归 `governance` 模块，变更只触发状态重算，**不会误触发全站页面重建**。

因此：换模型不会导致"重新理解全站 → 全量重跑 → 全量扫描"的资源浪费，也不会因为不记得历史结论而改坏核心页。

---

## 8. CI 闸门

| 工作流 | 原行为 | 现行为 |
|---|---|---|
| `news-auto.yml` | 每日全量 digest → 全站 normalize → 全站 sitemap → 全量 verify → 提交 | 先跑 digest，再由 `workarea.py` 只处理 `news-*` + `config` 闭包；**无新内容时不写盘、不提交**；提交前 `verify --gate` |
| `module-gate.yml` | — | 新增：push / PR 时 `audit` + `verify --gate`，FAIL 阻断 |
| `site-health.yml` | 每日线上探活 | 不变（线上监控与本地增量无关，仍需每日） |
| `indexing-submit.yml` | 每日提交 sitemap | 不变；仅在 sitemap 实际变化时才有新 URL 可提 |

**注意**：`site-health.yml` 与 `indexing-submit.yml` 保持全量/每日，因为它们监控的是线上真实状态，不属于"无需求不扫描"的本地模块范畴。

### 8.1 以远端 tree 为 base 推送时，必须先对齐 CI 产物 ⭐

GitHub 通道可用 PAT / API 但本地无法 `git pull` 时，推送走 `Git Data API`
单 commit：以远端 `main` 的 tree 为 `base_tree`，只提交「本地相对远端有差异」
的路径，`base_tree` 未提及的路径自动保留。**这一步有个必须先做的动作**：

> 推送前，先把远端 CI 自动生成的产物同步回本地，否则「本地相对远端有差异」
> 会把本地较旧的快照误判为待覆盖内容，把 CI 连续状态整体回退。

CI 自动生成、本地工作区通常落后的产物（每日 `news-auto.yml` 提交）：

- `news-20*.html`（每日新增新闻页）
- `news.html` / `news-archive*.html`（索引与归档，链接全部新闻页）
- `news_state.json`（去重记录，条数只增不减）
- `sitemap.xml`（含全部新闻页；由 `build_sitemap.py` 从本地全站 html 重建）

正确顺序：① 取回推送前远端 commit 的上述文件原始字节 → ② 本地跑
`inject_social_domains.py`（若该模块启用）与 `build_sitemap.py` → ③
`verify_seo.py --all` + `workarea.py audit` → ④ 再构造单 commit 推送。

**校验锚点**：`news_state.json` 的 `posted` 条数不得比远端少；sitemap URL 数
不得少于远端；`verify_seo.py` 的孤儿页与 `4f` 闸门必须全绿。这三个数字任一
回退，都说明本地快照落后于远端，禁止推送。

**为什么闸门没提前拦住**：`module-gate.yml` 设了
`if: github.actor != 'Anchormere Bot'`，bot 自己的每日提交跳过闸门，所以 CI
产物的缺陷只在**人工 / 非 bot 提交**时才会首次暴露。因此不要以「远端 CI 一直
success」推断产物合规；推送前必须本地全量复验。（2026-11-16 实录）

**生成链路根治**：`news_digest.py` 使用独立 FOOTER，每日新页不会自动带站点级
footer 模块。凡新增「全站每页都必须成立」的不变量（如 `4f` 品牌域名文字），
必须同步在 `news-auto.yml` 的 `Normalize` 之后、闸门之前加入对应幂等注入步骤，
否则新生成的新闻页会持续不合规。

---

## 9. 状态文件失效与维护

- `module_state.json` 缺失 → `status` 提示 `init`；`init` 应在一次 `verify --all` PASS 之后执行，把当前状态记为可信基线。
- 手工绕过制度直接改了页面 → 下次 `status` 通过 git diff 发现该模块 DIRTY，`plan` 会把它纳入闭包，不会漏检。
- 新增生成器 / 数据源 / 页面 → 更新 `modules.json`（`audit` 会强制校验归属完整与 `invalidates` 引用有效），新生成器必须调用 `write_if_changed()` 与 `selected()`。
- **新增页面的顺序**：先在 `modules.json` 的 `paths` 写入新 slug，再跑 `apply`。`assign()` 对显式声明但尚未落盘的路径也归属该模块（2026-11-08 修复），否则新页会被挡在 `WORKAREA_FILES` 之外，出现「只重建旧页、新页不生成」。
- **中文 / 非 ASCII 文件名**：`git_changed()` 使用 `git -c core.quotePath=false status`（2026-11-08 修复），否则中文文档名被 git 转成八进制转义，与 `walk_files()` 的 Unicode 路径对不上，该模块永远显示 CLEAN，换模型接手时会漏判。
- `governance` 模块变更只影响 `HEAD` 与状态认知；按交接协议跑一次 `status --deep` 即可，**不会触发全站页面重建**。

---

## 10. 品牌域名文字动态展示：无图标资源的可逆模块

`social-domains` 模块回答的是「域名能否在网页响应加载过程中动态展示」。结论是
**能，且不需要任何图标**：用户明确要求不使用平台图标 / 徽标 / SVG，
footer 只放一个指向**本站自有域名首页**的**文字链接**，动态展示文字为品牌化写法 `Anchormere.com`。

| 层 | 放什么 | 时机 | 为什么 |
|---|---|---|---|
| 静态 HTML（生成器输出） | `<a href>`、`aria-label`、`data-zh-attrs`、`title`、**静态可见的域名文字**、锁定尺寸的占位 | 响应内容本身 | 爬虫与不执行 JS 的抓取器能读到真实外链与域名文字；禁用 JS / 脚本加载失败也不会空白；占位锁定尺寸 → 0 CLS |
| `<script defer>` | `assets/social-domains.js` | HTML 解析期下载，`DOMContentLoaded` 后注册 | 与 `consent.js` / `lang.js` 同模式，不阻塞解析 |
| `requestIdleCallback` | 从 `<a href>` 用 `URL()` 派生域名、校验 `data-domain` 同源后写入品牌文字 | 首屏渲染后的空闲期 | 域名是「动态展示」的；单一数据源是 href，`display` 只承载品牌大小写且被闸门强制同源 |

**零图标、零网络请求**：本模块不 `fetch`、不 `new Image`、不插入 `<svg>`/`<img>`、
不热链第三方 CDN，也没有任何品牌徽标合规负担。`verify_seo.py` 4f 会强制检查
`assets/threads.svg` / `social-icons.js` / `inject_social_icons.py` 不得残留、页面
内不得出现 `SOCIAL-ICONS` / `data-social-slot` 历史痕迹，且域名块内不得有
`<svg>` / `<img>`。

红线（由 `verify_seo.py` 4f 强制）：

- **不把 `<a href>` 或 `Organization.sameAs` 交给 JS 注入** —— Googlebot 第二波
  渲染有延迟，Bing / AI 抓取器多数不执行 JS，动态注入等于没写。`sameAs` 仍属
  `data-org` 模块，真实 URL 到位后单独补，不在此模块内顺手改全站 JSON-LD。
- **域名只从 href 派生** —— 生成器用 `urlparse` 写 `data-domain` 供闸门校验，
  运行时 JS 用 `URL()` 解析；`display` 只承载品牌大小写（`Anchormere.com`），
  `validate()` 与 4f 都要求它小写去 www. 后与 href 的 hostname 完全一致，
  避免链接与文字失配。配置里不存在第二份独立文案。
- **不碰 `assets/lang.js`** —— 中文 `aria-label` 走既有 `data-zh-attrs` 机制，
  动态写入的 slot 恒为 `aria-hidden`，不参与双语引擎。
- **不碰核心转化路径** —— `index.html` / `contact.html` 等 `protected` 页默认跳过，
  需 `allow_protected=true` 且提交信息显式说明。

当前状态与回滚（2026-11-16 按用户指示**改为展示自有品牌域名 Anchormere.com**）：

- `href` = `https://anchormere.com/`（本站首页），`display` = `Anchormere.com`，
  `aria-label` = `Anchormere.com home`（中文「Anchormere.com 首页」），
  `pages=["*"]` 全站 footer，`allow_protected=true` 已在此显式声明。
- **不再指向任何第三方平台**：旧版 `www.threads.net` 已从全站 145 页清除，
  4f 闸门逐页检查不得残留 `threads.net`；链接指向本站首页，不声称任何社媒
  官方账号 / 合作 / 认证，`Organization.sameAs` 不在此模块改动。
- 每页仅新增「1 行 defer 脚本 + 1 个 footer 标记块」，逐页剥离后与 `HEAD` 字节一致；
  生成器幂等（二次运行 0 写入）。生成器**内置历史图标痕迹迁移**：`strip_block()`
  会同时清掉新旧两套标记块与 script，因此从图标版重跑可一次替换干净，
  `--rollback` 也能清回 `HEAD` 字节一致，不依赖聊天记录。

```bash
# 查看影响范围 / 重建 / 校验
python3 scripts/workarea.py plan --change scripts/social_links.json
python3 scripts/workarea.py apply --module social-domains
python3 scripts/workarea.py verify --all
# 一键还原：清空 profiles / pages 后
python3 scripts/inject_social_domains.py --rollback
```

把 `profiles` / `pages` 清空后生成器**连页面都不读取**，直接退出，所以停用态下
`apply --all` 不会为这个模块产生任何 IO、mtime 漂移或部署。

## 11. PCB 产业链板块：上下游 / AI 趋势的增量维护

`data-pcb` + `pcb-hub` + `longtail` 三个模块回答「业务里有没有 PCB 板块、
上下游和 AI 热词怎么持续扩」。结论是**按 Pillar-Cluster 建板块，不改动任何既有页**：

| 模块 | 唯一真源 / 产物 | 谁驱动谁 |
|---|---|---|
| `data-pcb`（manual） | `scripts/pcb_board.json`（上中下游 3 段、8 个 cluster slug、6 条 2026 AI 趋势词、4 条公开来源完整 URL、边界声明）、`scripts/build_pcb_hub.py` | 变更 → 重建 `pcb-hub` + `config`（sitemap） |
| `pcb-hub`（auto） | `pcb-supply-chain.html` 枢纽页（`CollectionPage + hasPart`、`FAQPage`、趋势词表、`Source URL:` 明文） | 由 `data-pcb` 驱动；读取 `longtail_seeds.json` 取 8 个页标题 |
| `longtail`（auto） | 8 个 `cluster=pcb` 长尾页，mother 统一指向枢纽页 | 由 `data-longtail` / `data-depth` 驱动 |

**为什么枢纽页不是孤儿页**：8 个 cluster 页的 CTA 用 `mother` 反链
`/pcb-supply-chain`，孤儿页检测（只计 `<a>` 导航链接）据此通过；**没有改动
`index.html` / `supply-base.html` 等任何既有页**，既有页仍指向原有母品类。

**内容边界（写进数据源与页面，3h 闸门强制）**：标准名（IPC / IEC / JEDEC /
IEEE / PCI-SIG / UL）只作编辑性引用；层数、Dk/Df、载板面积、交期都是公开
报道的行业典型区间，**不是** Anchormere 报价、能力或承诺；不主张任何认证，
不编造客户 / 价格 / 资质，不预留资质占位；公开来源保留完整 `Source URL:` 明文，
明确非客户项目、非背书。热门趋势词按 2026 公开报道校准（AI server PCB 20–30 层、
40+ 层背板、M8/M9 低损耗 CCL 与 HVLP / Q-glass、ABF / FC-BGA、HDI / mSAP /
Anylayer、800G / 1.6T 光模块板、液冷与供电）。

**换模型怎么扩这个板块**（不需要读聊天记录）：

1. 加词：把新 seed（`cluster: "pcb"`、`mother` 指向 `pcb-supply-chain.html`）
   追加到 `longtail_seeds.json`，把对应的页级专属 h2 / 4 条工程笔记 /
   6 个术语 / 4 条标准 / 决策场景 / 核验动作追加到 `longtail_depth.json`
   的 `pages`（`cluster: "pcb"`）；笔记与 h2 必须全局唯一（3g 闸门）。
2. 把新 slug 加入 `pcb_board.json` 对应分组的 `pages`，并同步
   `modules.json` 中 `longtail.paths`。
3. 用范围闸门只生成新增页，避免重跑覆盖既有页：

   ```bash
   WORKAREA_FILES="new-slug,pcb-supply-chain" python3 scripts/longtail.py
   WORKAREA_FILES="pcb-supply-chain" python3 scripts/build_pcb_hub.py
   python3 scripts/inject_social_domains.py   # 新页补 footer 域名文字（4f）
   python3 scripts/build_sitemap.py
   python3 scripts/workarea.py audit && python3 scripts/verify_seo.py --all
   ```

   也可以直接 `python3 scripts/workarea.py plan --change scripts/pcb_board.json`
   让依赖闭包自动定范围；生成器统一走 `io_util.write_final()` / `selected()`，
   内容相同不落盘。
4. `3h` 闸门从三个数据源推导期望值（分组页数、AI 趋势、来源 URL、
   cluster 归属、枢纽内链、反链、sitemap 收录），不写死页数；漏一环就 FAIL。

**一个刻意的例外（别当成漏做）**：公开案例区块由 `case_references.json`
的 `slugs` 按主题匹配，11 条案例里没有 PCB 材料 / 制板 / 载板主题，因此
8 个 cluster 页**不渲染** `class="case-refs"` 区块，也不硬挂不相关案例
（硬挂会破坏主题相关性、带回 scaled content 风险）。枢纽页已承载 4 条公开
来源完整 URL 与案例枢纽页内链；每页的 E-E-A-T 由工程笔记、公开标准引用、
术语表、决策场景、复核署名与编辑标准页内链支撑，3g 闸门全部通过。后续若补入
PCB 主题的真实公开案例，只需在 `case_references.json` 给该案例的 `slugs`
追加目标页，再用 `WORKAREA_FILES` 限定只重建这些页，避免覆盖既有页。

**不碰的东西**：`protected` 核心转化页、`assets/lang.js`、既有 36 个长尾页与
28 个框架页的既定内容；社媒域名模块对新页照常注入，规则不变。

## 12. 一句话总结

**按板块声明改动 → 依赖闭包定范围 → 内容相同不写盘 → 只校验脏模块 → 状态写回仓库 → 换模型照章接手。** 全站页面不再因为改一个词而整体重跑；没有问题的板块永远保持原样。
