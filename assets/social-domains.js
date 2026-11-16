/*
 * Anchormere · 品牌域名文字动态展示（defer / 空闲期 / 零请求）
 * -------------------------------------------------------------
 * 按用户要求：不使用任何平台图标、徽标或 SVG 资源，也不发起 fetch /
 * 第三方请求。footer 只显示一个指向本站自有域名首页的文字链接，
 * 展示文字为品牌化写法 Anchormere.com。
 *
 * 设计不变量（改动请同步 scripts/verify_seo.py 的 4f 闸门）：
 *  1. 静态兜底：域名文字本就在初始 HTML 的占位 <span> 内 —— 爬虫、
 *     不执行 JS 的抓取器、禁用 JS 或脚本加载失败的浏览器都能看到；
 *  2. 动态展示：本脚本在页面加载过程中从 <a href> 用 URL() 派生域名，
 *     读取 data-domain 的品牌化写法并用 textContent 重新写入占位，
 *     同时打 data-domain-ready 标记 —— 若 display 与 href 不同源，
 *     自动回退为真实 hostname，域名与链接恒一致；
 *  3. 零网络请求：不 fetch、不 new Image、不插入 <svg>/<img>/<style>；
 *  4. 零 CLS：占位尺寸在静态 HTML 已锁定，写入的是等长文字，
 *     不改变任何几何尺寸；
 *  5. 只用 textContent，绝不 innerHTML，无注入面；
 *  6. 不碰 lang.js / consent.js，不注册长期监听，不覆盖既有节点。
 */
(function () {
  "use strict";

  function norm(s) {
    var v = String(s || "").toLowerCase();
    return v.indexOf("www.") === 0 ? v.slice(4) : v;
  }

  function showDomain(slot) {
    var a = slot.closest ? slot.closest("a.social-domain") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (!href.startsWith("https://")) return;
    var host = "";
    try {
      host = new URL(href, window.location.href).hostname;
    } catch (e) {
      return;                       // 非绝对 URL：保留静态兜底文字
    }
    if (!host) return;
    var display = slot.getAttribute("data-domain") || host;
    if (norm(display) !== norm(host)) display = host;   // 同源一致性校正
    slot.textContent = display;     // 动态展示（幂等，等长写入）
    a.setAttribute("data-domain-ready", "1");
  }

  function run() {
    var slots = document.querySelectorAll("[data-domain-slot]");
    for (var i = 0; i < slots.length; i++) showDomain(slots[i]);
  }

  function schedule() {
    if (typeof window.requestIdleCallback === "function") {
      window.requestIdleCallback(run, { timeout: 2000 });
    } else {
      window.addEventListener("load", run, { once: true });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", schedule, { once: true });
  } else {
    schedule();
  }
})();
