import { db } from "./_lib/db.js";
import { hashPassword } from "./_lib/auth.js";
import { send, sendPreflight, readBody, adapt } from "./_lib/http.js";
import { eq, and } from "drizzle-orm";
import { users, passwordResets } from "./_lib/schema.js";

export default async function handler(req) {
  req = await adapt(req);
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return sendPreflight(res, origin);
  if (req.method !== "POST") return send(res,{ error: "Method not allowed" }, 405, origin);

  const { token, password } = await readBody(req);
  if (!token || !password) return send(res,{ error: "Missing fields" }, 400, origin);
  if (password.length < 8) return send(res,{ error: "Password too short" }, 400, origin);

  const [reset] = await db
    .select()
    .from(passwordResets)
    .where(and(eq(passwordResets.token, token), eq(passwordResets.used, false)))
    .limit(1);

  if (!reset || reset.expires_at < new Date()) {
    return send(res,{ error: "Invalid or expired token" }, 400, origin);
  }

  const { hash, salt } = await hashPassword(password);
  await db.update(users).set({ password_hash: hash, salt }).where(eq(users.id, reset.user_id));
  await db.update(passwordResets).set({ used: true }).where(eq(passwordResets.token, token));

  return send(res,{ ok: true }, 200, origin);
}
