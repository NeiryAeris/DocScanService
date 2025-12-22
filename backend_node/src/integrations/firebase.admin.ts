import admin from "firebase-admin";
import { env } from "../config/env";

function loadServiceAccount(): any {
  if (env.firebaseServiceAccountJson) {
    return JSON.parse(env.firebaseServiceAccountJson);
  }
  if (env.firebaseServiceAccountBase64) {
    const raw = Buffer.from(env.firebaseServiceAccountBase64, "base64").toString("utf8");
    return JSON.parse(raw);
  }
  return null;
}

export function getFirebaseAdmin() {
  if (admin.apps.length) return admin;

  const sa = loadServiceAccount();
  if (sa) {
    // normalize private key newlines if they got escaped
    if (sa.private_key && typeof sa.private_key === "string") {
      sa.private_key = sa.private_key.replace(/\\n/g, "\n");
    }
    admin.initializeApp({
      credential: admin.credential.cert(sa),
    });
    return admin;
  }

  // fallback (only works if GOOGLE_APPLICATION_CREDENTIALS / ADC is set)
  admin.initializeApp({
    credential: admin.credential.applicationDefault(),
  });
  return admin;
}
