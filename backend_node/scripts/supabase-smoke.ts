import { createClient } from "@supabase/supabase-js";
import dotenv from "dotenv";

dotenv.config();

const url = process.env.SUPABASE_URL!;
const key = process.env.SUPABASE_SERVICE_ROLE_KEY!;

if (!url || !key) {
  throw new Error("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY");
}

const sb = createClient(url, key, { auth: { persistSession: false } });

async function main() {
  const { data, error } = await sb
    .from("drive_accounts")
    .select("user_id")
    .limit(1);

  if (error) throw error;
  console.log("✅ Supabase OK. drive_accounts rows sample:", data);
}

main().catch((e) => {
  console.error("❌ Supabase failed:", e?.message ?? e);
  process.exit(1);
});
