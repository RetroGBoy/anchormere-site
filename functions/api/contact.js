// Anchormere contact form handler — Cloudflare Pages Function
// Route: POST /api/contact  (GET /api/contact redirects to the contact page)
// Sends the inquiry to a group-chat bot (DingTalk / WeCom / Feishu) via webhook.
// Configure ONE Pages env var:  CONTACT_WEBHOOK = the bot webhook URL (encrypt it).
// No DNS / DKIM / third-party signup required. Platform is auto-detected by host.

const WEBHOOK_ENV = "CONTACT_WEBHOOK";

function redirect(origin, status) {
  return Response.redirect(origin + "/contact.html?" + status, 302);
}

function cap(s, n) {
  return (s || "").toString().slice(0, n);
}

function buildText(form) {
  const name = cap(form.get("name"), 200).trim();
  const company = cap(form.get("company"), 200).trim();
  const email = cap(form.get("email"), 200).trim();
  const product_line = cap(form.get("product_line"), 100).trim();
  const qty = cap(form.get("qty"), 100).trim();
  const message = cap(form.get("message"), 5000).trim();
  return (
    "【Anchormere 新询盘】\n" +
    "客户: " + name + (company ? "（" + company + "）" : "") + "\n" +
    "邮箱: " + email + "\n" +
    "产品线: " + (product_line || "未填") + "\n" +
    "预估数量: " + (qty || "未填") + "\n" +
    "需求: " + message + "\n" +
    "时间: " + new Date().toISOString()
  );
}

// Format the payload for the detected platform.
function payloadFor(url, text) {
  let host = "";
  try { host = new URL(url).host; } catch (e) {}
  if (host.includes("dingtalk.com")) {
    return { msgtype: "text", text: { content: text } };
  }
  if (host.includes("feishu.cn") || host.includes("larksuite.com")) {
    return { msg_type: "text", content: { text: text } };
  }
  // 企业微信 (WeCom) and default
  return { msgtype: "text", text: { content: text } };
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = new URL(request.url).origin;
  const webhook = env && env[WEBHOOK_ENV];
  if (!webhook) {
    console.error("CONTACT_WEBHOOK is not configured");
    return redirect(origin, "error=1");
  }
  try {
    const form = await request.formData();

    // Honeypot: if filled, silently pretend success (don't notify on bots).
    if ((form.get("_gotcha") || "").toString().trim()) {
      return redirect(origin, "sent=1");
    }

    const name = cap(form.get("name"), 200).trim();
    const company = cap(form.get("company"), 200).trim();
    const email = cap(form.get("email"), 200).trim();
    const message = cap(form.get("message"), 5000).trim();

    if (!name || !company || !email || !message) return redirect(origin, "error=1");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return redirect(origin, "error=1");

    const text = buildText(form);
    const payload = payloadFor(webhook, text);

    const r = await fetch(webhook, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!r.ok) {
      const detail = await r.text().catch(() => "");
      console.error("webhook send failed:", r.status, detail);
      return redirect(origin, "error=1");
    }
    return redirect(origin, "sent=1");
  } catch (e) {
    console.error("contact function error:", e);
    return redirect(origin, "error=1");
  }
}

export async function onRequestGet(context) {
  const origin = new URL(context.request.url).origin;
  return Response.redirect(origin + "/contact.html", 302);
}
