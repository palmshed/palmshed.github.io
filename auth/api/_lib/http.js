// CORS for cross-origin calls from the GitHub Pages site.
const ALLOWED = (process.env.ALLOWED_ORIGIN || "https://palmshed.github.io").split(",").map((s) => s.trim());

export function corsHeaders(origin) {
  const allow = ALLOWED.includes(origin) ? origin : ALLOWED[0];
  return {
    "Access-Control-Allow-Origin": allow,
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Headers": "content-type",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
  };
}

export function json(body, status = 200, origin = "") {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...corsHeaders(origin) },
  });
}

export function preflight(origin = "") {
  return new Response(null, { status: 204, headers: corsHeaders(origin) });
}

export function setSessionCookie(token, expiresAt) {
  return `session=${token}; HttpOnly; SameSite=Lax; Path=/; Expires=${new Date(expiresAt.getTime() / 1000 * 1000).toUTCString()}`;
}

export function clearSessionCookie() {
  return "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0";
}

export async function readBody(req) {
  try { return await req.json(); } catch { return {}; }
}
