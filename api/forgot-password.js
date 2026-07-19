import { db } from "./_lib/db.js";
import { newResetToken, resetExpiry } from "./_lib/auth.js";
import { verifyCaptcha } from "./_lib/captcha.js";
import { json, readBody } from "./_lib/http.js";
import { eq } from "drizzle-orm";
import { users, passwordResets } from "./_lib/schema.js";

// Sends a reset link via Resend. In dev (RESEND_DISABLED=true) it logs the token.
async function sendResetEmail(email, token) {
  const link = `${process.env.PUBLIC_BASE_URL || ""}/login.html?reset=${token}`;
  if (process.env.RESEND_DISABLED === "true" || !process.env.RESEND_API_KEY) {
    console.log(`[reset] ${email} -> ${link}`);
    return;
  }
  await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${process.env.RESEND_API_KEY}`,
    },
    body: JSON.stringify({
      from: process.env.RESEND_FROM || "auth@palmshed.io",
      to: email,
      subject: "Reset your Palmshed password",
      html: `<p>Click to reset your password: <a href="${link}">${link}</a></p><p>This link expires in 1 hour.</p>`,
    }),
  });
}

export default async function handler(req) {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const { username, captcha } = await readBody(req);
  if (!username) return json({ error: "Missing fields" }, 400);
  if (!(await verifyCaptcha(captcha))) return json({ error: "Captcha failed" }, 400);

  const [user] = await db.select().from(users).where(eq(users.username, username)).limit(1);
  // Always return success to avoid user enumeration.
  if (user && user.email) {
    const token = newResetToken();
    await db.insert(passwordResets).values({ token, user_id: user.id, expires_at: resetExpiry() });
    await sendResetEmail(user.email, token);
  }

  return json({ ok: true });
}
