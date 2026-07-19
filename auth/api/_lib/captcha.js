const HCAPTCHA_URL = "https://api.hcaptcha.com/siteverify";
const TURNSTILE_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify";

export async function verifyCaptcha(token) {
  if (!token) return false;
  const secret = process.env.CAPTCHA_SECRET;
  if (!secret) {
    if (process.env.CAPTCHA_DISABLED === "true") return true;
    return false;
  }
  const provider = (process.env.CAPTCHA_PROVIDER || "hcaptcha").toLowerCase();
  const url = provider === "turnstile" ? TURNSTILE_URL : HCAPTCHA_URL;
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ secret, response: token }).toString(),
    });
    const data = await res.json();
    return Boolean(data.success);
  } catch {
    return false;
  }
}
