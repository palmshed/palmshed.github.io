import { json, preflight } from "./_lib/http.js";

export default async function handler(req) {
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return preflight(origin);
  return json({
    captchaSiteKey: process.env.HCAPTCHA_SITE_KEY || "",
    captchaProvider: (process.env.CAPTCHA_PROVIDER || "hcaptcha").toLowerCase(),
  }, 200, origin);
}
