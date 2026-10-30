/* Anchormere — GDPR-style cookie/consent manager
 * 默认不加载任何第三方追踪；用户接受后才注入 GA4 与转化事件。
 * 如需启用分析，在 GA4_ID 填入你的测量 ID 即可；留空则完全不加载。 */
(function () {
  var GA4_ID = 'G-EZE1LV2MRH'; // ← GA4 测量 ID（在 consent 接受后加载）
  var KEY = 'anm_consent';
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
  function injectGA() {
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
    gtag('js', new Date());
    gtag('config', GA4_ID, { send_page_view: true });
    setupConversions();
  }
  function showBanner() {
    if (document.getElementById('anm-consent')) return;
    var b = document.createElement('div');
    b.id = 'anm-consent';
    b.innerHTML =
      '<div class="anm-cc-inner">' +
      '<p>We use cookies for analytics (only after you accept) and to improve your experience. ' +
      'Inquiry data is sent via our form processor. See our <a href="privacy.html">Privacy Policy</a>. ' +
      '<button id="anm-reject" class="anm-cc-btn secondary" type="button">Reject</button> ' +
      '<button id="anm-accept" class="anm-cc-btn" type="button">Accept</button></p></div>';
    document.body.appendChild(b);
    document.getElementById('anm-accept').onclick = function () {
      try { localStorage.setItem(KEY, 'accepted'); } catch (e) {}
      b.remove(); injectGA();
    };
    document.getElementById('anm-reject').onclick = function () {
      try { localStorage.setItem(KEY, 'rejected'); } catch (e) {}
      b.remove();
    };
  }
  var c = null;
  try { c = localStorage.getItem(KEY); } catch (e) {}
  if (c === 'accepted') {
    injectGA();
  } else if (c !== 'rejected') {
    if (document.readyState !== 'loading') showBanner();
    else document.addEventListener('DOMContentLoaded', showBanner);
  }
})();
