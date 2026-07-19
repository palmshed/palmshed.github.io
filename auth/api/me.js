import { db } from "./_lib/db.js";
import { send, sendPreflight, adapt } from "./_lib/http.js";
import { eq, and } from "drizzle-orm";
import { sessions, users } from "./_lib/schema.js";

function getCookie(req, name) {
  const header = req.headers.get("cookie") || "";
  for (const part of header.split(";")) {
    const [k, ...v] = part.trim().split("=");
    if (k === name) return decodeURIComponent(v.join("="));
  }
  return "";
}

export default async function handler(req, res) {
  req = await adapt(req);
  const origin = req.headers.get("origin") || "";
  if (req.method === "OPTIONS") return sendPreflight(res, origin);
  if (req.method !== "GET") return json({ error: "Method not allowed" }, 405, origin);

  const token = getCookie(req, "session");
  if (!token) return send(res, { ok: false }, 200, origin);

  const [session] = await db
    .select({ username: users.username, expires_at: sessions.expires_at })
    .from(sessions)
    .innerJoin(users, eq(users.id, sessions.user_id))
    .where(and(eq(sessions.token, token)))
    .limit(1);

  if (!session || session.expires_at < new Date()) return send(res, { ok: false }, 200, origin);
  return send(res, { ok: true, username: session.username }, 200, origin);
}
