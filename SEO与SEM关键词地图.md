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

每个长尾页都已内置：双语 H1/H2、能力清单、规格/时效表、FAQ、Product JSON-LD、面包屑、hreflang、内链回母品类 + `contact.html` CTA。

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

**SEM 投放建议**：每页开一个"仅该词"广告组，匹配类型用"词组/精确"，落地页用对应 slug 页（不要都用首页），质量得分更高、转化更便宜。

---

## 4. 竞品 / 对比广告组结构（防御+截流）

| 广告组 | 关键词示例 | 落地页 | 创意要点 |
|---|---|---|---|
| vs 平台型 | `hqtronics alternative`、`made-in-china agent vs`、`alibaba sourcing agent` | `supply-base.html` + `faq.html` | 强调"20+ 认证工厂、48h 报价、整柜拼柜" |
| vs 同行 | `shenzhen sourcing company`、`china sourcing agent review` | `about.html` + `capabilities.html` | 强调"深圳森亚实业有限公司实体、出口单证齐全" |
| 地域截流 | `shenzhen manufacturing partner`、`dongguan metal fabrication` | 对应长尾页 | 强调本地集群与时效 |

---

## 5. GEO / AEO（生成式引擎优化）

- 已部署 `llms.txt`（根目录），列出 8 条典型买家长尾意图，供 ChatGPT/Perplexity/文心等引用。
- 每个长尾页的 FAQ 段落（含 FAQPage JSON-LD）直接回答"MOQ 多少 / 多久报价 / 怎么远程验厂 / 付款方式 / 是否做成品"——这些是 AI 摘要最爱抓取的结构化问答。
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
| `scripts/longtail.py` | 由种子生成 14 个长尾落地页 | 新增品类时 |
| `scripts/build_sitemap.py` | 扫描全站 `*.html` 生成 `sitemap.xml`（当前约 59 条 URL，含业务页 + 资讯 + 归档，CI 自动重建） | 增删页面后 / 每次资讯生成后 |
| `scripts/seo_inject.py` | 给既有页注入 Organization/Breadcrumb/FAQ/Product JSON-LD + hreflang | 改模板后 |
| `scripts/inject_ga4.py` | 给缺 `consent.js` 的页面补齐（已全站覆盖） | 新增页面时 |
| `scripts/news_digest.py` | 每日抓取科技/制造/采购源 → 中英双语摘要落地页 → `/news` 索引封顶 48 篇 + 自动归档分页 → 重建 sitemap | GitHub Actions 每日 cron（北京时间 09:00，含 `workflow_dispatch` 兜底） |
