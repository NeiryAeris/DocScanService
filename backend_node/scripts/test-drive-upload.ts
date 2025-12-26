import "dotenv/config";
import fs from "fs";
import path from "path";
import { exec } from "child_process";

const GW = process.env.GW_BASE_URL || "http://127.0.0.1:4000/api";
const RAW = process.env.TEST_FIREBASE_ID_TOKEN || "";
const IDTOKEN = RAW.trim().replace(/^Bearer\s+/i, "");
const DEFAULT_FILE = process.env.TEST_UPLOAD_PATH || "";
const AUTO_OPEN = (process.env.AUTO_OPEN_BROWSER || "true").toLowerCase() === "true";
const SYNC_AFTER = (process.env.TEST_SYNC_AFTER_UPLOAD || "true").toLowerCase() === "true";

function assertLooksLikeJwt(token: string) {
  if (!token) die("Missing TEST_FIREBASE_ID_TOKEN in .env");
  if (token.startsWith("ya29.")) {
    die("You put a Google ACCESS token (ya29...). Need Firebase ID token (eyJ...).");
  }
  const parts = token.split(".");
  if (parts.length !== 3) {
    die(
      `Token doesn't look like a JWT. Parts=${parts.length}. ` +
      `Make sure TEST_FIREBASE_ID_TOKEN is ONLY the raw token, no 'Bearer ', no quotes, no newlines.`
    );
  }
  if (!token.startsWith("eyJ")) {
    console.warn("⚠️ Token doesn't start with eyJ... still trying, but it likely isn't a Firebase ID token.");
  }
}

function die(msg: string): never {
  console.error("❌", msg);
  process.exit(1);
}

function prettyCause(e: any) {
  const c = e?.cause;
  if (!c) return null;
  return {
    name: c?.name,
    code: c?.code,
    errno: c?.errno,
    syscall: c?.syscall,
    address: c?.address,
    port: c?.port,
    message: c?.message,
  };
}

async function pingGateway() {
  try {
    const r = await fetch(`${GW}/health`, { method: "GET" });
    const t = await r.text();
    if (!r.ok) throw new Error(`Health returned ${r.status}: ${t}`);
    console.log("✅ Gateway reachable:", `${GW}/health`);
  } catch (e: any) {
    console.error("❌ Cannot reach gateway:", `${GW}/health`);
    console.error("   Tip: run `npm run dev` in backend_node, and confirm port.");
    console.error("   Error:", e?.message ?? e);
    const cause = prettyCause(e);
    if (cause) console.error("   Cause:", cause);
    process.exit(1);
  }
}

function mimeFromExt(filePath: string): string {
  const ext = path.extname(filePath).toLowerCase();
  switch (ext) {
    case ".pdf": return "application/pdf";
    case ".png": return "image/png";
    case ".jpg":
    case ".jpeg": return "image/jpeg";
    case ".txt": return "text/plain";
    default: return "application/octet-stream";
  }
}

function openBrowser(url: string) {
  if (!AUTO_OPEN) return;
  const safe = `"${url.replace(/"/g, '\\"')}"`;
  const cmd =
    process.platform === "win32"
      ? `start "" ${safe}`
      : process.platform === "darwin"
      ? `open ${safe}`
      : `xdg-open ${safe}`;

  exec(cmd, (err) => {
    if (err) console.warn("⚠️ Could not auto-open browser. Open manually:", url);
  });
}

async function sleep(ms: number) {
  await new Promise((r) => setTimeout(r, ms));
}

async function httpJson<T>(
  method: string,
  url: string,
  body?: any,
  extraHeaders?: Record<string, string>
): Promise<T> {
  const headers: Record<string, string> = {
    "Authorization": `Bearer ${IDTOKEN}`,
    ...(extraHeaders || {}),
  };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  let res: Response;
  try {
    res = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (e: any) {
    console.error("❌ Network error calling:", url);
    console.error("   Error:", e?.message ?? e);
    const cause = prettyCause(e);
    if (cause) console.error("   Cause:", cause);
    throw e;
  }

  const text = await res.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }

  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText} -> ${typeof data === "string" ? data : JSON.stringify(data)}`);
  }
  return data as T;
}

async function httpUpload(filePath: string) {
  const buf = fs.readFileSync(filePath);
  const mime = mimeFromExt(filePath);
  const filename = path.basename(filePath);

  const fd = new FormData();
  fd.append("file", new Blob([buf], { type: mime }), filename);

  let res: Response;
  try {
    res = await fetch(`${GW}/drive/upload`, {
      method: "POST",
      headers: { "Authorization": `Bearer ${IDTOKEN}` },
      body: fd,
    });
  } catch (e: any) {
    console.error("❌ Network error calling:", `${GW}/drive/upload`);
    console.error("   Error:", e?.message ?? e);
    const cause = prettyCause(e);
    if (cause) console.error("   Cause:", cause);
    throw e;
  }

  const text = await res.text();
  let data: any = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = text; }

  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText} -> ${typeof data === "string" ? data : JSON.stringify(data)}`);
  }
  return data;
}

async function ensureLinked() {
  const status = await httpJson<{ linked: boolean; folderId: string | null }>("GET", `${GW}/drive/status`);
  if (status.linked) return status;

  console.log("ℹ️ Drive not linked yet. Starting OAuth...");
  const start = await httpJson<{ url: string }>("GET", `${GW}/drive/oauth2/start`);
  console.log("👉 Open this URL to link Drive:\n", start.url);
  openBrowser(start.url);

  for (let i = 0; i < 90; i++) {
    await sleep(2000);
    const s = await httpJson<{ linked: boolean; folderId: string | null }>("GET", `${GW}/drive/status`);
    if (s.linked) return s;
  }

  die("Drive still not linked. Finish OAuth in the browser, then re-run.");
}

async function main() {
    assertLooksLikeJwt(IDTOKEN);
  if (!IDTOKEN) die("Missing TEST_FIREBASE_ID_TOKEN in backend_node/.env");

  await pingGateway();

  const filePath = process.argv[2] || DEFAULT_FILE;
  if (!filePath) die("Provide a file path arg or set TEST_UPLOAD_PATH in .env");
  if (!fs.existsSync(filePath)) die(`File not found: ${filePath}`);

  console.log("GW:", GW);
  console.log("FILE:", filePath);

  const status = await ensureLinked();
  console.log("✅ Drive linked. folderId =", status.folderId);

  const folder = await httpJson<{ folderId: string }>("POST", `${GW}/drive/folder/init`);
  console.log("✅ Folder ensured:", folder.folderId);

  const uploaded = await httpUpload(filePath);
  console.log("✅ Uploaded to Drive:", uploaded);

  if (SYNC_AFTER) {
    const sync = await httpJson<any>("POST", `${GW}/drive/sync`);
    console.log("✅ Sync result:", sync);
  }

  console.log("🎉 Done.");
}

main().catch((e: any) => {
  console.error("❌ Test failed:", e?.message ?? e);
  const cause = prettyCause(e);
  if (cause) console.error("Cause:", cause);
  process.exit(1);
});
