# Anchormere 官网部署包（Cloudflare Pages · Git 方式）

大湾区供应链整合商 B2B 独立站（Anchormere 锚泊）。本目录即站点根，上传/推送即上线。

## 本地预览
```bash
cd 本目录
python3 -m http.server 8102
# 浏览器打开 http://localhost:8102
```

## 部署到 Cloudflare Pages（Git 自动部署）
1. 登录 GitHub，新建一个空仓库（如 `anchormere-site`）。
2. 在本地执行（把 `<你的仓库URL>` 换成第 1 步的地址）：
   ```bash
   git remote add origin <你的仓库URL>
   git branch -M main
   git push -u origin main
   ```
3. 登录 Cloudflare → **Workers & Pages** → **Create** → **Pages** → **Connect to Git** → 选该仓库。
4. 构建设置：Framework preset 选 `None`；Build command 留空；Build output directory 填 `/`（根目录）。
5. 部署完成后在 **Custom domains** 绑定 `anchormere.com`（NS 已切到 Cloudflare，免费自动签发 SSL）。
6. 之后每次 `git push` 即自动重新部署。

## 询盘表单说明
- 当前用 **mailto 兜底**：访客提交即唤起邮件发至 `info@anchormere.com`，无需任何第三方账号，立即可用。
- 进阶（站内静默收单、不依赖访客邮件客户端）：注册 Formspree 免费档（50 单/月），把 `contact.html` 表单的
  `action="mailto:info@anchormere.com"` 改为 `action="https://formspree.io/f/你的ID"`，并删掉 `enctype="text/plain"`。

## 上线前仍需你补充的字段（当前以 [待填] 标注）
| 项 | 影响 | 位置 |
|----|------|------|
| GA4 测量 ID | 无流量分析（不影响展示） | `assets/consent.js` 的 `G-【待填】` |
| 实体地址 | 法律页披露缺口 | 各页 footer + Privacy/Terms |
| 注册号 | 法律主体信息不全 | about / supply-base / index 的 Legal 栏 |
| 产品规格/认证/实拍图 | 转化信任素材 | 各内容页 `[待填]` |

> 注：产品规格等无需你逐项填写——买家会在询盘表单里说明需求并发到你邮箱，内容页占位仅作示例。
