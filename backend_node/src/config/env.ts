// backend_node/src/config/env.ts
import dotenv from 'dotenv';

dotenv.config();

const required = (name: string) : string => {
  const value = process.env[name];
  if (!value) throw new Error(`missing required env var: ${name}`);
  return value;
};

export const env = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: Number(process.env.PORT) || 4000,
  pythonServiceUrl: required("PYTHON_SERVICE_URL"),
  pythonInternalToken: process.env.PYTHON_INTERNAL_TOKEN || process.env.INTERNAL_TOKEN || (() => { throw new Error("missing required env var: PYTHON_INTERNAL_TOKEN or INTERNAL_TOKEN"); })(),
  jwtSecret: required("JWT_SECRET"),

  firebaseServiceAccountJson: process.env.FIREBASE_SERVICE_ACCOUNT_JSON,
  firebaseServiceAccountBase64: process.env.FIREBASE_SERVICE_ACCOUNT_BASE64,

  // ✅ Supabase (required only if you use Drive endpoints)
  supabaseUrl: process.env.SUPABASE_URL,
  supabaseServiceRoleKey: process.env.SUPABASE_SERVICE_ROLE_KEY,

  // ✅ Google OAuth (required only if you use Drive endpoints)
  googleOauthClientId: process.env.GOOGLE_OAUTH_CLIENT_ID,
  googleOauthClientSecret: process.env.GOOGLE_OAUTH_CLIENT_SECRET,
  googleOauthRedirectUri: process.env.GOOGLE_OAUTH_REDIRECT_URI,

  driveAppFolderName: process.env.DRIVE_APP_FOLDER_NAME || "DocScanService",
};
