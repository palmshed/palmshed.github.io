import { randomBytes, scrypt, timingSafeEqual, randomUUID } from "crypto";

const KEYLEN = 64;

function scryptAsync(password, salt, keylen) {
  return new Promise((resolve, reject) => {
    scrypt(password, salt, keylen, (err, derived) => {
      if (err) reject(err);
      else resolve(derived);
    });
  });
}

export async function hashPassword(password, salt = randomBytes(16).toString("hex")) {
  const derived = await scryptAsync(password, salt, KEYLEN);
  return { hash: derived.toString("hex"), salt };
}

export async function verifyPassword(password, salt, expectedHash) {
  const derived = await scryptAsync(password, salt, KEYLEN);
  const expected = Buffer.from(expectedHash, "hex");
  return derived.length === expected.length && timingSafeEqual(derived, expected);
}

export function newSessionToken() { return randomUUID(); }
export function newResetToken() { return randomBytes(32).toString("hex"); }
export function sessionExpiry(days = 30) { return new Date(Date.now() + days * 86400000); }
export function resetExpiry(hours = 1) { return new Date(Date.now() + hours * 3600000); }
