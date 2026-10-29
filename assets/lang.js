/*
 * Anchormere language switcher — region-aware UI localization (interface level).
 * Detection order: saved choice -> Cloudflare Geo (cdn-cgi/trace) -> browser language -> English.
 * Body content stays English (Chinese subtitles already exist); only the UI shell is localized.
 */
(function () {
  "use strict";

  // Regions where Chinese is the expected UI language.
  var ZH_REGIONS = ["CN", "HK", "TW", "MO", "SG"];

  // Runtime dictionary for call-to-action buttons / links (varies per page).
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

  function applyLang(lang) {
    document.documentElement.lang = (lang === "zh") ? "zh-CN" : "en";

    // 1) Explicit data-zh elements (nav / footer links, column titles).
    var nodes = document.querySelectorAll("[data-zh]");
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n.getAttribute("data-en")) n.setAttribute("data-en", n.textContent);
      n.textContent = (lang === "zh") ? n.getAttribute("data-zh") : n.getAttribute("data-en");
    }

    // 2) CTA buttons / links (per-page text, matched against dictionary).
    var sel = "a.btn-primary, a.btn-ghost, a.btn-quote, .cta a, .card a, button, a.wa-float";
    var btns = document.querySelectorAll(sel);
    for (var j = 0; j < btns.length; j++) {
      var b = btns[j];
      if (b.hasAttribute("data-zh")) continue; // already handled above
      var key = b.textContent.trim();
      if (CTA_DICT[key]) {
        if (!b.getAttribute("data-en")) b.setAttribute("data-en", key);
        b.textContent = (lang === "zh") ? CTA_DICT[key] : b.getAttribute("data-en");
      }
    }

    // 3) Highlight active switch button.
    var sw = document.getElementById("langSwitch");
    if (sw) {
      var sbtns = sw.querySelectorAll("button");
      for (var k = 0; k < sbtns.length; k++) {
        sbtns[k].classList.toggle("active", sbtns[k].getAttribute("data-lang") === lang);
      }
    }
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
    wrap.querySelector('[data-lang="en"]').addEventListener("click", function () {
      setStored("en"); applyLang("en");
    });
    wrap.querySelector('[data-lang="zh"]').addEventListener("click", function () {
      setStored("zh"); applyLang("zh");
    });
  }

  function init() {
    buildSwitch();
    decide().then(function (lang) { applyLang(lang); });
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", init);
})();
