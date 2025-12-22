import dotenv from 'dotenv';

dotenv.config();

const required = (name: string) : string => {
    const value = process.env[name];
    if (!value) {
        throw new Error(`missing required env var: ${name}`);
    }
    return value;
};

export const env = {
  nodeEnv: process.env.NODE_ENV || "development",
  port: Number(process.env.PORT) || 4000,
  pythonServiceUrl: required("PYTHON_SERVICE_URL"),
  pythonInternalToken: required("PYTHON_INTERNAL_TOKEN"),
  jwtSecret: required("JWT_SECRET"),

  // ✅ Firebase (optional at app boot; required when firebase middleware runs)
  firebaseServiceAccountJson: process.env.FIREBASE_SERVICE_ACCOUNT_JSON,
  firebaseServiceAccountBase64: process.env.FIREBASE_SERVICE_ACCOUNT_BASE64,
};