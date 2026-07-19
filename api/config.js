import { json } from "./_lib/http.js";

// Public client config. Never expose secrets here.
export default async function handler() {
  return json({
    captchaSiteKey: process.env.HCAPTCHA_SITE_KEY || "",
    captchaProvider: (process.env.CAPTCHA_PROVIDER || "hcaptcha").toLowerCase(),
  });
}
