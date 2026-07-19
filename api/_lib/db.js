// Shared DB client. Requires DATABASE_URL (Vercel Postgres).
import { drizzle } from "drizzle-orm/postgres-js";
import postgres from "postgres";
import "dotenv/config";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  throw new Error("DATABASE_URL is not set");
}

// Reuse the client across invocations (Vercel keeps the module alive).
const globalForDb = globalThis;
const client = globalForDb.__pg || (globalForDb.__pg = postgres(connectionString, { max: 1 }));

export const db = drizzle(client);
export { client };
