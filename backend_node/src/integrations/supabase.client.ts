import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { env } from "../config/env";

let _client: SupabaseClient | null = null;

export const getSupabaseAdmin = (): SupabaseClient => {
  if (_client) return _client;

  if (!env.supabaseUrl || !env.supabaseServiceRoleKey) {
    throw new Error("Missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY (needed for Drive integration)");
  }

  _client = createClient(env.supabaseUrl, env.supabaseServiceRoleKey, {
    auth: { persistSession: false },
  });

  return _client;
};
