import { google } from "googleapis";
import { env } from "../config/env";

export const requireGoogleOauthConfig = () => {
  if (!env.googleOauthClientId || !env.googleOauthClientSecret || !env.googleOauthRedirectUri) {
    throw new Error("Missing GOOGLE_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI");
  }
};

export const makeOauth2Client = () => {
  requireGoogleOauthConfig();
  return new google.auth.OAuth2(
    env.googleOauthClientId,
    env.googleOauthClientSecret,
    env.googleOauthRedirectUri
  );
};

export const makeDriveClient = (refreshToken: string) => {
  const oauth2 = makeOauth2Client();
  oauth2.setCredentials({ refresh_token: refreshToken });
  return google.drive({ version: "v3", auth: oauth2 });
};

// Minimal scopes needed for “app folder + upload + read”
export const DRIVE_SCOPES = [
  "https://www.googleapis.com/auth/drive.file",
  "https://www.googleapis.com/auth/drive.metadata.readonly",
];
