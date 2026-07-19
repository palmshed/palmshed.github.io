import { db } from "./_lib/db.js";
import { hashPassword } from "./_lib/auth.js";
import { json, readBody } from "./_lib/http.js";
import { eq, and } from "drizzle-orm";
import { users, passwordResets } from "./_lib/schema.js";

export default async function handler(req) {
  if (req.method !== "POST") return json({ error: "Method not allowed" }, 405);

  const { token, password } = await readBody(req);
  if (!token || !password) return json({ error: "Missing fields" }, 400);
  if (password.length < 8) return json({ error: "Password too short" }, 400);

  const [reset] = await db
    .select()
    .from(passwordResets)
    .where(and(eq(passwordResets.token, token), eq(passwordResets.used, false)))
    .limit(1);

  if (!reset || reset.expires_at < new Date()) {
    return json({ error: "Invalid or expired token" }, 400);
  }

  const { hash, salt } = await hashPassword(password);
  await db.update(users).set({ password_hash: hash, salt }).where(eq(users.id, reset.user_id));
  await db.update(passwordResets).set({ used: true }).where(eq(passwordResets.token, token));

  return json({ ok: true });
}
