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

export function json(body, status = 200, origin = "", extraHeaders = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json", ...corsHeaders(origin), ...extraHeaders },
  });
}

export function preflight(origin = "") {
  return new Response(null, { status: 204, headers: corsHeaders(origin) });
}

// Vercel Node runtime uses the (req, res) signature and does not honor a
// returned Response. Write the response to the Node ServerResponse instead.
export function send(res, body, status = 200, origin = "", extraHeaders = {}) {
  const headers = { "content-type": "application/json", ...corsHeaders(origin), ...extraHeaders };
  res.writeHead(status, headers);
  res.end(JSON.stringify(body));
}

export function sendPreflight(res, origin = "") {
  res.writeHead(204, corsHeaders(origin));
  res.end();
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

// Vercel Node functions receive a Node IncomingMessage. Convert it to a Web
// Request so the handlers can use req.headers.get / req.json() uniformly.
export async function adapt(req) {
  if (typeof req?.headers?.get === "function") return req;
  const headers = new Headers();
  for (const [k, v] of Object.entries(req.headers || {})) {
    if (v == null) continue;
    if (Array.isArray(v)) v.forEach((x) => headers.append(k, x));
    else headers.set(k, String(v));
  }
  const method = req.method || "GET";
  let body;
  if (method !== "GET" && method !== "OPTIONS") {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    body = Buffer.concat(chunks);
  }
  return new Request("https://placeholder.local", { method, headers, body });
}
