/**
 * POST /api/lead — real form endpoint (Cloudflare Pages Function).
 *
 * SAFE BY DEFAULT: until both secrets exist, this returns 503 and the site's
 * forms keep their honest mailto flow. Nothing user-facing changes by deploying it.
 *
 * To activate (owner steps, ~10 minutes):
 *   1. Cloudflare dashboard > Turnstile > Add site: treecareofbuffalo.com and
 *      *.treecareofbuffalo.pages.dev (invisible widget). Copy sitekey + secret.
 *   2. resend.com > API key. Until the domain moves off Wix DNS (~Oct 21) the
 *      sender must be onboarding@resend.dev; after the move, verify
 *      treecareofbuffalo.com and switch FROM below to leads@treecareofbuffalo.com.
 *   3. From the repo root:
 *        npx wrangler pages secret put TURNSTILE_SECRET --project-name=treecareofbuffalo
 *        npx wrangler pages secret put RESEND_API_KEY  --project-name=treecareofbuffalo
 *   4. Front-end flip (agent task): add the Turnstile script + widget to the
 *      estimate form, and in assets/site.js swap the mailto branch for
 *      fetch('/api/lead', {method:'POST', body:new FormData(form)}) with the
 *      existing success/failure UI. Keep mailto as the catch fallback.
 */

const DEST = "business@treecareofbuffalo.com";
const FROM = "onboarding@resend.dev"; // switch to leads@treecareofbuffalo.com after domain verify

/* The live site is served by GitHub Pages at treecareofbuffalo.com, so the form
   POSTs here cross-origin. Allow the production hosts plus the Cloudflare branch
   previews (for testing the flipped form before merge). */
function corsOrigin(request) {
  const origin = request.headers.get("origin") || "";
  if (
    origin === "https://treecareofbuffalo.com" ||
    origin === "https://www.treecareofbuffalo.com" ||
    /^https:\/\/[a-z0-9-]+\.treecareofbuffalo\.pages\.dev$/.test(origin)
  ) {
    return origin;
  }
  return null;
}

function json(status, body, origin) {
  const headers = { "content-type": "application/json" };
  if (origin) {
    headers["access-control-allow-origin"] = origin;
    headers["vary"] = "Origin";
  }
  return new Response(JSON.stringify(body), { status, headers });
}

export function onRequestOptions({ request }) {
  const origin = corsOrigin(request);
  if (!origin) return new Response(null, { status: 403 });
  return new Response(null, {
    status: 204,
    headers: {
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "POST, OPTIONS",
      "access-control-allow-headers": "content-type",
      "access-control-max-age": "86400",
      "vary": "Origin",
    },
  });
}

export async function onRequestPost({ request, env }) {
  const origin = corsOrigin(request);
  if (!env.TURNSTILE_SECRET || !env.RESEND_API_KEY) {
    return json(503, { ok: false, error: "endpoint not configured" }, origin);
  }

  const data = await request.formData();

  // Honeypot: pretend success so bots move on. Field name must stay a
  // nonsense token no browser autofills (see DESIGN.md; never "company").
  if ((data.get("tcob-trap") || "").toString().trim() !== "") {
    return json(200, { ok: true }, origin);
  }

  const token = data.get("cf-turnstile-response");
  if (!token) return json(400, { ok: false, error: "missing turnstile token" }, origin);

  const verify = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      secret: env.TURNSTILE_SECRET,
      response: token.toString(),
      remoteip: request.headers.get("cf-connecting-ip") || "",
    }),
  }).then((r) => r.json());
  if (!verify.success) return json(403, { ok: false, error: "turnstile failed" }, origin);

  const f = (k) => (data.get(k) || "").toString().trim().slice(0, 2000);
  const urgent = f("urgent") !== "";
  const name = f("name");
  const phone = f("phone");
  if (name.length < 2 || phone.replace(/\D/g, "").length < 10) {
    return json(400, { ok: false, error: "name and phone required" }, origin);
  }

  const body = [
    urgent ? "URGENT: tree on structure / blocking access" : "",
    `Name: ${name}`,
    `Phone: ${phone}`,
    `Address or cross street: ${f("address")}`,
    "",
    "About the tree:",
    f("details"),
    "",
    `Photos: ${f("photos-count") || "0"} selected on the form (they arrive by text)`,
    `Page: ${request.headers.get("referer") || "unknown"}`,
  ].filter((l) => l !== null).join("\n");

  const send = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      authorization: `Bearer ${env.RESEND_API_KEY}`,
      "content-type": "application/json",
    },
    body: JSON.stringify({
      from: `Tree Care of Buffalo website <${FROM}>`,
      to: [DEST],
      subject: (urgent ? "URGENT tree work request" : "Free estimate request") + ` from ${name}`,
      text: body,
    }),
  });
  if (!send.ok) return json(502, { ok: false, error: "mail send failed" }, origin);

  return json(200, { ok: true });
}
