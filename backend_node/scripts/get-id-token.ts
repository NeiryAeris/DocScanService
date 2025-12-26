import "dotenv/config";
import admin from "firebase-admin";

function die(msg: string): never {
  console.error(`[x] ${msg}`);
  process.exit(1);
}

function getServiceAccountJson(): any {
  // Try common env names (use the one you already have in your repo)
  const b64 =
    process.env.FIREBASE_SERVICE_ACCOUNT_BASE64 ||
    process.env.GOOGLE_SERVICE_ACCOUNT_BASE64 ||
    process.env.FIREBASE_ADMIN_SA_BASE64;

  if (!b64) {
    die(
      "Missing FIREBASE_SERVICE_ACCOUNT_BASE64 (or GOOGLE_SERVICE_ACCOUNT_BASE64 / FIREBASE_ADMIN_SA_BASE64) in .env"
    );
  }

  const raw = Buffer.from(b64, "base64").toString("utf-8").trim();
  try {
    return JSON.parse(raw);
  } catch (e) {
    die("Service account base64 is not valid JSON after decode");
  }
}

async function exchangeCustomTokenForIdToken(apiKey: string, customToken: string) {
  const url = `https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key=${encodeURIComponent(
    apiKey
  )}`;

  const res = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ token: customToken, returnSecureToken: true }),
  });

  const json = await res.json();
  if (!res.ok) {
    console.error(json);
    die("Failed to exchange custom token for ID token (check FIREBASE_WEB_API_KEY)");
  }

  return {
    idToken: json.idToken as string,
    refreshToken: json.refreshToken as string,
    expiresIn: json.expiresIn as string,
    localId: json.localId as string,
  };
}

async function main() {
  const apiKey = process.env.FIREBASE_WEB_API_KEY?.trim();
  if (!apiKey) die("Missing FIREBASE_WEB_API_KEY in .env (starts with AIza...)");

  const sa = getServiceAccountJson();

  if (!admin.apps.length) {
    admin.initializeApp({
      credential: admin.credential.cert(sa),
    });
  }

  const uid = (process.env.DEV_UID || "dev-local").trim();

  // Create custom token (valid for ~1 hour for exchange)
  const customToken = await admin.auth().createCustomToken(uid, {
    dev: true,
    source: "pc-script",
  });

  // Exchange to Firebase ID token
  const { idToken, refreshToken, expiresIn, localId } = await exchangeCustomTokenForIdToken(
    apiKey,
    customToken
  );

  console.log("\n✅ Firebase ID token generated via Admin custom token");
  console.log("uid:", localId);
  console.log("expiresIn:", expiresIn, "seconds");

  console.log("\nID_TOKEN:\n" + idToken);
  console.log("\nREFRESH_TOKEN (optional):\n" + refreshToken);

  console.log("\nPaste into backend_node/.env:");
  console.log(`TEST_FIREBASE_ID_TOKEN=${idToken}\n`);
}

main().catch((e) => die(String(e)));
