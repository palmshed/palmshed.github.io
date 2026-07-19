import { db } from "./_lib/db.js";
import { verifyPassword, newSessionToken, sessionExpiry } from "./_lib/auth.js";
import { verifyCaptcha } from "./_lib/captcha.js";
import { json, setSessionCookie, readBody } from "./_lib/http.js";
import { eq } from "drizzle-orm";
import { users, sessions } from "./_lib/schema.js";

export default async function handler(req) {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const { username, password, captcha } = await readBody(req);

  if (!username || !password) return json({ error: "Missing fields" }, 400);
  if (!(await verifyCaptcha(captcha))) return json({ error: "Captcha failed" }, 400);

  const [user] = await db.select().from(users).where(eq(users.username, username)).limit(1);
  if (!user) return json({ error: "Invalid credentials" }, 401);

  const ok = await verifyPassword(password, user.salt, user.password_hash);
  if (!ok) return json({ error: "Invalid credentials" }, 401);

  const token = newSessionToken();
  const expiresAt = sessionExpiry();
  await db.insert(sessions).values({ token, user_id: user.id, expires_at: expiresAt });

  return new Response(JSON.stringify({ ok: true }), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "set-cookie": setSessionCookie(token, expiresAt),
    },
  });
}
