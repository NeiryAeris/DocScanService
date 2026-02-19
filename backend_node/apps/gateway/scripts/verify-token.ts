import "dotenv/config";
import { createClient } from "@supabase/supabase-js";

async function main() {
  const url = process.env.SUPABASE_URL;
  const anon = process.env.SUPABASE_ANON_KEY;
  const email = process.env.TEST_EMAIL;
  const password = process.env.TEST_PASSWORD;

  if (!url) throw new Error("SUPABASE_URL is missing");
  if (!anon) throw new Error("SUPABASE_ANON_KEY is missing");
  if (!email) throw new Error("TEST_EMAIL is missing");
  if (!password) throw new Error("TEST_PASSWORD is missing");

  const supabase = createClient(url, anon);

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password
  });

  if (error) throw error;

  const token = data.session?.access_token;
  if (!token) throw new Error("No access_token returned (session is null)");

  console.log("access_token:", token);
  console.log("user:", data.user?.email);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});