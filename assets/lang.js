/*
 * Anchormere language switcher — full bilingual engine (EN / 中文).
 * Detection order: saved choice -> Cloudflare Geo (cdn-cgi/trace) -> browser language -> English.
 * Every translatable element carries data-zh (Chinese innerHTML). English is captured once as data-en.
 * Also localizes <title>, meta description/OG/Twitter, element attributes (data-zh-attrs), and emits hreflang.
 */
(function () {
  "use strict";

  // Regions where Chinese is the expected UI language.
  var ZH_REGIONS = ["CN", "HK", "TW", "MO", "SG"];

  // Runtime dictionary for any call-to-action not yet carrying data-zh.
  var CTA_DICT = {
    "Request a Quote": "获取报价",
    "Get a Quote": "获取报价",
    "WhatsApp us": "WhatsApp 联系",
    "Verify Us Remotely": "远程验厂",
    "View line →": "查看系列 →",
    "Ask for list →": "索取清单 →",
    "Read more →": "阅读更多 →",
    "Browse the full Greater Bay Area supply-base map →": "浏览完整大湾区供应基地地图 →",
    "All news & insights →": "全部资讯与洞察 →",
    "Open a conversation →": "开启沟通 →",
    "Book a live look →": "预约实况查看 →",
    "Send": "发送",
    "Back to home": "返回首页",
    "💬 WhatsApp": "💬 WhatsApp 咨询"
  };

  function getStored() {
    try { return localStorage.getItem("am-lang"); } catch (e) { return null; }
  }
  function setStored(l) {
    try { localStorage.setItem("am-lang", l); } catch (e) {}
  }

  function geoLang() {
    // Cloudflare injects visitor country into /cdn-cgi/trace as `loc=XX`.
    return fetch("/cdn-cgi/trace")
      .then(function (r) { return r.text(); })
      .then(function (t) {
        var m = t.match(/loc=([A-Z]{2})/);
        if (m && ZH_REGIONS.indexOf(m[1]) > -1) return "zh";
        return null;
      })
      .catch(function () { return null; });
  }

  function browserLang() {
    var l = (navigator.language || navigator.userLanguage || "").toLowerCase();
    if (l.indexOf("zh") === 0) return "zh";
    return null;
  }

  function decide() {
    var s = getStored();
    if (s) return Promise.resolve(s);
    return geoLang().then(function (g) { return g || browserLang() || "en"; });
  }

  var _titleEN, _descEN;
  function applyMeta(lang) {
    var zhTitle = document.querySelector('meta[name="title-zh"]');
    var zhDesc = document.querySelector('meta[name="desc-zh"]');
    if (lang === "zh") {
      if (zhTitle && zhTitle.getAttribute("content")) document.title = zhTitle.getAttribute("content");
      if (zhDesc) {
        var c = zhDesc.getAttribute("content");
        var d = document.querySelector('meta[name="description"]'); if (d) d.setAttribute("content", c);
        var og = document.querySelector('meta[property="og:description"]'); if (og) og.setAttribute("content", c);
        var tw = document.querySelector('meta[name="twitter:description"]'); if (tw) tw.setAttribute("content", c);
      }
    } else {
      if (_titleEN) document.title = _titleEN;
      if (_descEN) {
        var d2 = document.querySelector('meta[name="description"]'); if (d2) d2.setAttribute("content", _descEN);
        var og2 = document.querySelector('meta[property="og:description"]'); if (og2) og2.setAttribute("content", _descEN);
        var tw2 = document.querySelector('meta[name="twitter:description"]'); if (tw2) tw2.setAttribute("content", _descEN);
      }
    }
  }

  function applyAttrs(lang) {
    var nodes = document.querySelectorAll("[data-zh-attrs]");
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      var map;
      try { map = JSON.parse(n.getAttribute("data-zh-attrs")); } catch (e) { continue; }
      if (!n.getAttribute("data-en-attrs")) n.setAttribute("data-en-attrs", JSON.stringify(captureAttrs(n, map)));
      for (var key in map) {
        if (!map.hasOwnProperty(key)) continue;
        n.setAttribute(key, lang === "zh" ? map[key] : JSON.parse(n.getAttribute("data-en-attrs"))[key]);
      }
    }
  }
  function captureAttrs(n, map) {
    var o = {};
    for (var k in map) { if (map.hasOwnProperty(k)) o[k] = n.getAttribute(k) || ""; }
    return o;
  }

  function applyLang(lang) {
    document.documentElement.lang = (lang === "zh") ? "zh-CN" : "en";

    // 1) Explicit data-zh elements (nav / footer / headings / paragraphs / lists … any element).
    var nodes = document.querySelectorAll("[data-zh]");
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n.getAttribute("data-en")) n.setAttribute("data-en", n.innerHTML);
      n.innerHTML = (lang === "zh") ? n.getAttribute("data-zh") : n.getAttribute("data-en");
    }

    // 2) CTA buttons / links not yet carrying data-zh (per-page text, matched against dictionary).
    var sel = "a.btn-primary, a.btn-ghost, a.btn-quote, .cta a, .card a, button, a.wa-float";
    var btns = document.querySelectorAll(sel);
    for (var j = 0; j < btns.length; j++) {
      var b = btns[j];
      if (b.hasAttribute("data-zh")) continue;
      var key = b.textContent.trim();
      if (CTA_DICT[key]) {
        if (!b.getAttribute("data-en")) b.setAttribute("data-en", key);
        b.textContent = (lang === "zh") ? CTA_DICT[key] : b.getAttribute("data-en");
      }
    }

    // 3) Attributes (title / placeholder / aria-label …).
    applyAttrs(lang);

    // 4) Document title + meta description.
    applyMeta(lang);

    // 5) Highlight active switch button.
    var sw = document.getElementById("langSwitch");
    if (sw) {
      var sbtns = sw.querySelectorAll("button");
      for (var k = 0; k < sbtns.length; k++) {
        sbtns[k].classList.toggle("active", sbtns[k].getAttribute("data-lang") === lang);
      }
    }
  }

  function addHreflang() {
    if (document.querySelector('link[hreflang]')) return;
    var url = location.href.split("#")[0];
    var head = document.head;
    [["x-default", url], ["en", url], ["zh-CN", url]].forEach(function (p) {
      var l = document.createElement("link");
      l.rel = "alternate"; l.hreflang = p[0]; l.href = p[1];
      head.appendChild(l);
    });
  }

  function buildSwitch() {
    var nav = document.querySelector("nav .container") || document.querySelector(".mainnav");
    if (!nav) return;
    if (document.getElementById("langSwitch")) return;
    var wrap = document.createElement("span");
    wrap.id = "langSwitch";
    wrap.className = "lang-switch";
    wrap.innerHTML =
      '<button type="button" data-lang="en">EN</button>' +
      '<span class="sep">|</span>' +
      '<button type="button" data-lang="zh">中文</button>';
    nav.appendChild(wrap);
    wrap.querySelector('[data-lang="en"]').addEventListener("click", function () { setStored("en"); applyLang("en"); });
    wrap.querySelector('[data-lang="zh"]').addEventListener("click", function () { setStored("zh"); applyLang("zh"); });
  }

  function init() {
    _titleEN = document.title;
    var d0 = document.querySelector('meta[name="description"]');
    _descEN = d0 ? d0.getAttribute("content") : "";
    addHreflang();
    buildSwitch();
    decide().then(function (lang) { applyLang(lang); });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
