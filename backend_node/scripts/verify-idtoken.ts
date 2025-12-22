import "dotenv/config";
import { getFirebaseAdmin } from "../src/integrations/firebase.admin";

async function main() {
  const token = process.env.ID_TOKEN;

  if (!token) {
    console.error("❌ GOOGLE_ID_TOKEN not found in .env");
    process.exit(1);
  }

  const admin = getFirebaseAdmin();

  try {
    const decoded = await admin.auth().verifyIdToken(token);

    console.log("✅ ID TOKEN IS VALID");
    console.log("────────────────────────");
    console.log("uid:", decoded.uid);
    console.log("email:", decoded.email);
    console.log("name:", decoded.name);
    console.log("picture:", decoded.picture);
    console.log("issuer:", decoded.iss);
    console.log("audience:", decoded.aud);
    console.log("expires at:", new Date(decoded.exp * 1000).toISOString());
    console.log("────────────────────────");
  } catch (err: any) {
    console.error("❌ ID TOKEN INVALID");
    console.error(err.message || err);
    process.exit(2);
  }
}

main();
