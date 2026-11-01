/* Anchormere — GDPR / Google Consent Mode v2 cookie manager
 *
 * 最优策略（合规 + 不过度低估流量）：
 *  1) 页面加载即注入 GA4，但默认 analytics_storage='denied'。
 *     Google 此时仅发送【匿名 cookieless ping】（不写 cookie、不记录可识别身份），
 *     用于聚合流量估算与转化建模；不含 PII，符合 GDPR / ePrivacy。
 *  2) 访客 Accept → consent='granted'，解锁完整测量与转化事件（generate_lead 等）。
 *  3) 访客 Reject → 保持 denied，不存储完整数据（仍发匿名 ping，属 Google 标准合规行为）。
 *
 * 如需启用分析，在 GA4_ID 填入测量 ID；留空则完全不加载。 */
(function () {
  var GA4_ID = 'G-EZE1LV2MRH'; // ← GA4 测量 ID
  var KEY = 'anm_consent';

  function loadGA() {
    if (window.__anm_ga) return;
    if (!GA4_ID) return; // 未配置则不加载
    window.__anm_ga = true;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA4_ID;
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;
    // Consent Mode v2：默认拒绝（仅匿名 cookieless ping）
    gtag('consent', 'default', {
      analytics_storage: 'denied',
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied',
      wait_for_update: 500
    });
    gtag('js', new Date());
    gtag('config', GA4_ID, { send_page_view: true });
    setupConversions();
  }

  function grantConsent() {
    if (window.gtag) {
      window.gtag('consent', 'update', {
        analytics_storage: 'granted',
        ad_storage: 'granted',
        ad_user_data: 'granted',
        ad_personalization: 'granted'
      });
    }
    try { localStorage.setItem(KEY, 'accepted'); } catch (e) {}
  }

  function track(name, params) {
    if (window.gtag) window.gtag('event', name, params || {});
  }

  function setupConversions() {
    if (window.__anm_conv) return;
    window.__anm_conv = true;
    // 表单提交（Formspree 走整页 POST，sendBeacon 会在跳转前发出）
    document.addEventListener('submit', function (e) {
      var f = e.target;
      if (!f || f.tagName !== 'FORM') return;
      track('generate_lead', { event_category: 'lead', event_label: 'rfq_form' });
    });
    // 询单/报价 CTA 点击 + WhatsApp 点击
    document.addEventListener('click', function (e) {
      var a = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!a) return;
      var href = a.getAttribute('href') || '';
      if (href.indexOf('contact.html') > -1 ||
          a.classList.contains('btn-quote') ||
          a.classList.contains('btn-primary')) {
        track('contact_click', { event_category: 'cta', event_label: href });
      }
      if (a.classList.contains('wa-float')) {
        track('whatsapp_click', { event_category: 'cta' });
      }
    });
  }

  function showBanner() {
    if (document.getElementById('anm-consent')) return;
    var b = document.createElement('div');
    b.id = 'anm-consent';
    b.innerHTML =
      '<div class="anm-cc-inner">' +
      '<p>We use cookies for analytics. Before you accept, we only collect ' +
      'anonymous, cookieless usage signals (no personal data) to estimate traffic. ' +
      'Accept to enable full analytics. Inquiry data is sent via our form processor. ' +
      'See our <a href="privacy.html">Privacy Policy</a>. ' +
      '<button id="anm-reject" class="anm-cc-btn secondary" type="button">Reject</button> ' +
      '<button id="anm-accept" class="anm-cc-btn" type="button">Accept</button></p></div>';
    document.body.appendChild(b);
    document.getElementById('anm-accept').onclick = function () {
      grantConsent(); b.remove();
    };
    document.getElementById('anm-reject').onclick = function () {
      try { localStorage.setItem(KEY, 'rejected'); } catch (e) {}
      b.remove();
    };
  }

  // 入口：先加载（默认 denied）→ 应用已存偏好 → 未决定时显示横幅
  loadGA();
  var c = null;
  try { c = localStorage.getItem(KEY); } catch (e) {}
  if (c === 'accepted') grantConsent();
  if (c !== 'accepted' && c !== 'rejected') {
    if (document.readyState !== 'loading') showBanner();
    else document.addEventListener('DOMContentLoaded', showBanner);
  }
})();
