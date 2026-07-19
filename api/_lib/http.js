// Shared JSON helpers + cookie handling.
export function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

export function setSessionCookie(token, expiresAt) {
  const expires = Math.floor(expiresAt.getTime() / 1000);
  return `session=${token}; HttpOnly; SameSite=Lax; Path=/; Expires=${new Date(expires * 1000).toUTCString()}`;
}

export function clearSessionCookie() {
  return "session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0";
}

export async function readBody(req) {
  try {
    return await req.json();
  } catch {
    return {};
  }
}
