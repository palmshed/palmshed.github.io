import { send, sendPreflight, adapt } from "./_lib/http.js";

export default async function handler(req, res) {
  req = await adapt(req);
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return sendPreflight(res, origin);
  send(res, {
    captchaSiteKey: process.env.HCAPTCHA_SITE_KEY || "",
    captchaProvider: (process.env.CAPTCHA_PROVIDER || "hcaptcha").toLowerCase(),
  }, 200, origin);
}
