"use client";

import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL as string;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;

// Single browser client, read-only in practice: all writes go through API
// routes so they can be validated server-side (see supabase/schema.sql RLS notes).
export const supabaseBrowser = createClient(url, anonKey, {
  auth: { persistSession: false },
});
