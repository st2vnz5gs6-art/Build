import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL as string;

/**
 * Service-role client for use in API routes / server components only.
 * Bypasses RLS — never import this into client code.
 */
export function supabaseServer() {
  const serviceKey = process.env.SUPABASE_SERVICE_ROLE_KEY as string;
  return createClient(url, serviceKey, {
    auth: { persistSession: false },
  });
}

/** Anon client for server-side reads that should stay within RLS. */
export function supabaseServerAnon() {
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY as string;
  return createClient(url, anonKey, {
    auth: { persistSession: false },
  });
}
