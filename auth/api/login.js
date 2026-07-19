import { db } from "./_lib/db.js";
import { verifyPassword, newSessionToken, sessionExpiry } from "./_lib/auth.js";
import { verifyCaptcha } from "./_lib/captcha.js";
import { json, send, sendPreflight, setSessionCookie, readBody, adapt } from "./_lib/http.js";
import { eq } from "drizzle-orm";
import { users, sessions } from "./_lib/schema.js";

export default async function handler(req, res) {
  req = await adapt(req);
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return sendPreflight(res, origin);
  if (req.method !== "POST") return send(res, { error: "Method not allowed" }, 405, origin);

  const { username, password, captcha } = await readBody(req);
  if (!username || !password) return send(res,{ error: "Missing fields" }, 400, origin);
  if (!(await verifyCaptcha(captcha))) return send(res,{ error: "Captcha failed" }, 400, origin);

  const [user] = await db.select().from(users).where(eq(users.username, username)).limit(1);
  if (!user) return send(res,{ error: "Invalid credentials" }, 401, origin);

  const ok = await verifyPassword(password, user.salt, user.password_hash);
  if (!ok) return send(res,{ error: "Invalid credentials" }, 401, origin);

  const token = newSessionToken();
  const expiresAt = sessionExpiry();
  await db.insert(sessions).values({ token, user_id: user.id, expires_at: expiresAt });

  return send(res, { ok: true }, 200, origin, { "set-cookie": setSessionCookie(token, expiresAt) });
}
