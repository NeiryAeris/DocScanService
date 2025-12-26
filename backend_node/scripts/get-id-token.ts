import "dotenv/config";

const API_KEY = process.env.FIREBASE_WEB_API_KEY!;
const EMAIL = process.env.TEST_USER_EMAIL!;
const PASSWORD = process.env.TEST_USER_PASSWORD!;

function die(msg: string): never {
  console.error("❌", msg);
  process.exit(1);
}

async function main() {
  if (!API_KEY) die("Missing FIREBASE_WEB_API_KEY in .env");
  if (!EMAIL) die("Missing TEST_USER_EMAIL in .env");
  if (!PASSWORD) die("Missing TEST_USER_PASSWORD in .env");

  const url = `https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${API_KEY}`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD, returnSecureToken: true }),
  });

  const data: any = await res.json();
  if (!res.ok) {
    throw new Error(JSON.stringify(data));
  }

  // Print ONLY the token (easy to pipe)
  console.log(data.idToken);
}

main().catch((e: any) => {
  console.error("❌ Failed:", e?.message ?? e);
  process.exit(1);
});
