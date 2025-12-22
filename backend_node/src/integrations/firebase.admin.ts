import admin from "firebase-admin";

function loadServiceAccount() {
  const b64 = process.env.FIREBASE_SERVICE_ACCOUNT_BASE64;
  if (b64) {
    const jsonStr = Buffer.from(b64, "base64").toString("utf-8");
    return JSON.parse(jsonStr);
  }

  const raw = process.env.FIREBASE_SERVICE_ACCOUNT_JSON;
  if (raw) return JSON.parse(raw);

  throw new Error(
    "Missing FIREBASE_SERVICE_ACCOUNT_BASE64 or FIREBASE_SERVICE_ACCOUNT_JSON"
  );
}

let initialized = false;

export function getFirebaseAdmin() {
  if (!initialized) {
    const serviceAccount = loadServiceAccount();

    admin.initializeApp({
      credential: admin.credential.cert(serviceAccount as admin.ServiceAccount),
    });

    initialized = true;
  }

  return admin;
}
