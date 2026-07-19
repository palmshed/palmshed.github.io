import postgres from "postgres";
import { drizzle } from "drizzle-orm/postgres-js";
import "dotenv/config";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) throw new Error("DATABASE_URL is not set");

const globalForDb = globalThis;
const client = globalForDb.__pg || (globalForDb.__pg = postgres(connectionString, { max: 1 }));
export const db = drizzle(client);
