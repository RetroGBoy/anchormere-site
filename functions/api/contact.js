// Anchormere contact form handler — Cloudflare Pages Function
// Route: POST /api/contact  (GET /api/contact redirects to the contact page)
// Sends the inquiry to info@anchormere.com via MailChannels — no third-party signup.
// Optional DKIM signing: set a Pages secret "DKIM_PRIVATE_KEY" (PKCS8 PEM) to sign mail
// and keep it out of the spam folder. DNS records are listed in the deploy checklist.

const TO_EMAIL = "info@anchormere.com";
const TO_NAME = "Anchormere Sales";
const FROM_EMAIL = "noreply@anchormere.com";
const FROM_NAME = "Anchormere Contact Form";
const DKIM_DOMAIN = "anchormere.com";
const DKIM_SELECTOR = "milter";

function redirect(origin, status) {
  return Response.redirect(origin + "/contact.html?" + status, 302);
}

function cap(s, n) {
  return (s || "").toString().slice(0, n);
}

export async function onRequestPost(context) {
  const { request, env } = context;
  const origin = new URL(request.url).origin;
  try {
    const form = await request.formData();

    // Honeypot: if filled, silently pretend success (don't tip off bots).
    if ((form.get("_gotcha") || "").toString().trim()) {
      return redirect(origin, "sent=1");
    }

    const name = cap(form.get("name"), 200).trim();
    const company = cap(form.get("company"), 200).trim();
    const email = cap(form.get("email"), 200).trim();
    const product_line = cap(form.get("product_line"), 100).trim();
    const qty = cap(form.get("qty"), 100).trim();
    const message = cap(form.get("message"), 5000).trim();

    if (!name || !company || !email || !message) return redirect(origin, "error=1");
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) return redirect(origin, "error=1");

    const body =
      "New RFQ from Anchormere website\n" +
      "================================\n\n" +
      "Name:         " + name + "\n" +
      "Company:      " + company + "\n" +
      "Email:        " + email + "\n" +
      "Product line: " + (product_line || "(not specified)") + "\n" +
      "Est. qty:     " + (qty || "(not specified)") + "\n\n" +
      "Message:\n" + message + "\n\n" +
      "Submitted at: " + new Date().toISOString() + "\n" +
      "Source:       " + origin + "\n";

    const payload = {
      personalizations: [{ to: [{ email: TO_EMAIL, name: TO_NAME }] }],
      from: { email: FROM_EMAIL, name: FROM_NAME },
      reply_to: { email: email, name: name },
      subject: "New RFQ — " + company + (product_line ? " (" + product_line + ")" : ""),
      content: [{ type: "text/plain", value: body }],
    };

    // Sign with DKIM when the secret is configured (recommended).
    if (env && env.DKIM_PRIVATE_KEY) {
      payload.dkim_domain = DKIM_DOMAIN;
      payload.dkim_selector = DKIM_SELECTOR;
      payload.dkim_private_key = env.DKIM_PRIVATE_KEY;
    }

    const r = await fetch("https://api.mailchannels.net/tx/v1/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!r.ok) {
      const detail = await r.text().catch(() => "");
      console.error("MailChannels send failed:", r.status, detail);
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
