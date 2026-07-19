import { pgTable, bigserial, text, timestamp, boolean } from "drizzle-orm/pg-core";

export const users = pgTable("users", {
  id: bigserial("id", { mode: "number" }).primaryKey(),
  username: text("username").notNull().unique(),
  password_hash: text("password_hash").notNull(),
  salt: text("salt").notNull(),
  email: text("email"),
  created_at: timestamp("created_at").notNull().defaultNow(),
});

export const sessions = pgTable("sessions", {
  token: text("token").primaryKey(),
  user_id: bigserial("user_id", { mode: "number" }).references(() => users.id),
  created_at: timestamp("created_at").notNull().defaultNow(),
  expires_at: timestamp("expires_at").notNull(),
});

export const passwordResets = pgTable("password_resets", {
  token: text("token").primaryKey(),
  user_id: bigserial("user_id", { mode: "number" }).references(() => users.id),
  created_at: timestamp("created_at").notNull().defaultNow(),
  expires_at: timestamp("expires_at").notNull(),
  used: boolean("used").notNull().default(false),
});
