import { db } from "./_lib/db.js";
import { hashPassword } from "./_lib/auth.js";
import { verifyCaptcha } from "./_lib/captcha.js";
import { json, preflight, readBody } from "./_lib/http.js";
import { eq } from "drizzle-orm";
import { users } from "./_lib/schema.js";

export default async function handler(req) {
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return preflight(origin);
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405, origin);

  const { username, password, email, captcha } = await readBody(req);
  if (!username || !password) return json({ error: "Missing fields" }, 400, origin);
  if (password.length < 8) return json({ error: "Password too short (min 8)" }, 400, origin);
  if (!(await verifyCaptcha(captcha))) return json({ error: "Captcha failed" }, 400, origin);

  const [existing] = await db.select().from(users).where(eq(users.username, username)).limit(1);
  if (existing) return json({ error: "Username taken" }, 409, origin);

  const { hash, salt } = await hashPassword(password);
  await db.insert(users).values({ username, password_hash: hash, salt, email: email || null });

  return json({ ok: true }, 201, origin);
}
