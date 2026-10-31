# Anchormere SEO 收录与目录提交计划

> 站点：`https://anchormere.com`（Cloudflare Pages，已部署）
> 生成日期：2026-10-29
> 目标：让 Google / Bing / Yandex / 百度 等搜索引擎收录全站，并进入高价值 B2B 目录

---

## 一、已自动完成（无需你操作）

| 动作 | 状态 | 说明 |
|------|------|------|
| **IndexNow 全站提交** | ✅ HTTP 202 已接受 | 一次性把 59 个 URL 推送给 **Bing / Yandex / Naver / Seznam / Yep**。密钥文件已上线：`https://anchormere.com/b1700fd697c7492b958b22d8d2adf646.txt` |
| **Yandex sitemap ping** | ✅ HTTP 200 | 已通知 Yandex 抓取 sitemap |
| **全站 canonical** | ✅ 59/59 页 | 消除 clean URL（`/about` 与 `/about.html`）重复收录风险 |
| **全站 Open Graph + Twitter Card** | ✅ 59/59 页 | 社交分享/链接预览带图带标题 |
| **全站结构化数据 (JSON-LD)** | ✅ 59/59 页 | Organization + Article + FAQ + CollectionPage，利于富媒体摘要 |
| **robots.txt** | ✅ | 放行 Google/Bing/Yandex 及 GPTBot/Perplexity/Claude 等 AI 爬虫；已声明 `Sitemap` 与 `Host` |
| **sitemap.xml** | ✅ 59 条 clean URL | 已提交给各搜索引擎 |

> 注：Bing 旧版 `bing.com/ping` 接口已废弃（返回 410），其功能已由 IndexNow 完全替代，无需担心。

---

## 二、需要你手动完成（高价值，搜索引擎官方入口）

以下入口**必须登录你的账号**才能提交，无法由脚本代劳。建议按顺序处理，前两项优先级最高。

### 1. Google Search Console（必做，海外流量主入口）
1. 打开 https://search.google.com/search-console 用你的 Google 账号登录
2. 添加资源 → 网址前缀 `https://anchormere.com` → 验证方式选 **HTML 标记** 或 **Google Analytics**（当前 GA4 未启用，建议选 HTML 标记，我会帮你生成验证文件）
3. 验证通过后：左侧 **站点地图** → 提交 `https://anchormere.com/sitemap.xml`
4. 左侧 **URL 检查** → 逐个粘贴首页 URL 点「请求编入索引」
5. GA4 已启用：测量 ID `G-EZE1LV2MRH`，由 `assets/consent.js` 在 Cookie 同意后门控加载，并上报 `generate_lead` 等转化事件

> 沙箱网络无法直连 google.com，故 Google 这一步只能由你在中完成；完成后通常 1–4 周开始收录。

### 2. 百度搜索资源平台（如做中文/国内买家流量，必做）
1. 打开 https://ziyuan.baidu.com 登录百度账号 → 添加网站 `https://anchormere.com` → 完成验证
2. 左侧 **链接提交 → 主动推送**：获取你的 **token**
3. 用仓库内已备好的 `baidu_urls.txt`（22 个 URL），执行：
   ```bash
   curl -X POST "http://data.zz.baidu.com/urls?site=https://anchormere.com&token=你的TOKEN" \
        -H "Content-Type: text/plain" --data-binary @baidu_urls.txt
   ```
4. 也可在「站点地图」处提交 `https://anchormere.com/sitemap.xml`

### 3. Bing Webmaster Tools（可选，已被 IndexNow 覆盖）
- IndexNow 已推送，Bing 会自行抓取。如需看数据：https://www.bing.com/webmasters 添加站点即可。

### 4. Google 商家档案 / Bing Places（本地信任信号，可选）
- Google Business Profile：https://business.google.com （需实体地址验证，有利于「深圳/中国 采购」类本地搜索）
- Bing Places：https://www.bingplaces.com

---

## 三、行业 B2B 目录 / 平台（手动入驻，按目标市场选）

| 平台 | 适用市场 | 入驻成本 | 备注 |
|------|----------|----------|------|
| **Alibaba.com** | 全球 B2B | 会员费 | 权重最高，建议做金品诚企/验厂认证 |
| **Made-in-China.com** | 全球 B2B | 会员费 | 南京焦点科技，机械/电子买家多 |
| **GlobalSources.com** | 欧美买家 | 会员费 | 展会+线上，质量买家 |
| **Thomasnet** | 北美工业 | 免费/付费 | 工业采购目录，匹配「rack / cable / OEM」 |
| **Europages** | 欧洲 B2B | 免费基础 | 欧洲买家目录 |
| **Kompass** | 全球企业库 | 付费 | 大公司数据库 |
| **IndustryNet** | 北美制造 | 免费 | 制造商目录 |

> 入驻时**统一使用**：公司名「深圳森亚实业有限公司 / Anchormere」、官网 `https://anchormere.com`、邮箱 `Anchormere@gmail.com`、地址「中国广东深圳市光明区特发工业园B座」，保持 NAP（名称/地址/电话）一致，利于本地 SEO 权重。

---

## 四、不推荐 / 风险提示

- **免费文章目录、链接农场、群发目录**：多数已被 Google 标记为低质量，外链反而**拉低**权重，不要做。
- **需付费买「高 PR 外链」的服务**：多为垃圾站，风险大于收益。
- **自动提交机器人**：不要用第三方工具批量群发目录，易触发搜索引擎惩罚。
- 优先用「真实行业平台 + 官方搜索引擎入口 + 自然外链（行业博客客座文章、展会官网链接）」。

---

## 五、后续可做的 SEO 增强（可选）

1. **启用 GA4 + Search Console 数据联动**：填 `GA4_ID` 后看真实词报告，反哺内容。
2. **图片 SEO**：当前 19 张图已带 `alt`；可加 `width/height` 防布局抖动，并补充 `srcset` 适配移动端。
3. **外链建设**：争取 3–5 个行业相关站点（展会、协会、客户案例站）的自然反向链接。
4. **内容持续更新**：保持每月 2–4 篇 Greater Bay Area / 制造供应链主题文章，巩固「China sourcing partner」相关词。
5. **结构化数据扩展**：产品页可加 `Product`/`Offer` 富摘要；FAQ 页已用 `FAQPage`，可加 `HowTo` 等。

---

## 附：本批提交的 59 个 URL（clean URL）

完整可推送的 URL 列表见同目录 `baidu_urls.txt`（一行一个，已含全部业务页与资讯文章，可直接用于百度主动推送与 IndexNow 复核）。
