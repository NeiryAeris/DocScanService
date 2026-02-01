import { Readable } from "stream";
import jwt from "jsonwebtoken";
import { env } from "../config/env";
import { getSupabaseAdmin } from "../integrations/supabase.client";
import { DRIVE_SCOPES, makeDriveClient, makeOauth2Client } from "../integrations/google.drive";
import { pythonClient } from "../integrations/python.client";
import * as aiService from "./ai.service";

type DriveAccountRow = {
  user_id: string;
  refresh_token: string;
  folder_id: string | null;
};

const supabase = () => getSupabaseAdmin();

const must = <T>(v: T | undefined | null, msg: string): T => {
  if (v === undefined || v === null) throw new Error(msg);
  return v;
};

export const makeOauthStartUrl = (userId: string) => {
  const oauth2 = makeOauth2Client();

  // state = signed JWT so callback can map back to Firebase uid safely
  const state = jwt.sign(
    { uid: userId, nonce: String(Date.now()) },
    env.jwtSecret,
    { expiresIn: "10m" }
  );

  const url = oauth2.generateAuthUrl({
    access_type: "offline",
    prompt: "consent",
    scope: DRIVE_SCOPES,
    state,
    include_granted_scopes: true,
  });

  return { url };
};

export const handleOauthCallback = async (code: string, state: string) => {
  const payload = jwt.verify(state, env.jwtSecret) as any;
  const userId = must(payload?.uid, "Invalid state (missing uid)");

  const oauth2 = makeOauth2Client();
  const { tokens } = await oauth2.getToken(code);

  // refresh_token might be absent if user already consented before
  if (!tokens.refresh_token) {
    // If we already have one stored, keep it. Otherwise tell user to revoke and re-link.
    const { data: existing } = await supabase()
      .from("drive_accounts")
      .select("refresh_token")
      .eq("user_id", userId)
      .maybeSingle();

    if (!existing?.refresh_token) {
      throw new Error(
        "Google did not return a refresh_token. Re-link by revoking access for this app in Google Account → Security → Third-party access, then try again."
      );
    }

    await supabase()
      .from("drive_accounts")
      .update({
        scope: tokens.scope ?? null,
        token_type: tokens.token_type ?? null,
      })
      .eq("user_id", userId);

    return { userId, linked: true, refreshTokenStored: true, note: "refresh_token reused (not re-issued by Google)" };
  }

  await supabase()
    .from("drive_accounts")
    .upsert({
      user_id: userId,
      refresh_token: tokens.refresh_token,
      scope: tokens.scope ?? null,
      token_type: tokens.token_type ?? null,
      folder_id: null,
    });

  return { userId, linked: true, refreshTokenStored: true };
};

export const getDriveStatus = async (userId: string) => {
  const { data } = await supabase()
    .from("drive_accounts")
    .select("user_id, folder_id")
    .eq("user_id", userId)
    .maybeSingle();

  return { linked: !!data?.user_id, folderId: data?.folder_id ?? null };
};

const getAccountOrThrow = async (userId: string): Promise<DriveAccountRow> => {
  const { data, error } = await supabase()
    .from("drive_accounts")
    .select("user_id, refresh_token, folder_id")
    .eq("user_id", userId)
    .maybeSingle();

  if (error) throw new Error(`Supabase error: ${error.message}`);
  if (!data?.refresh_token) throw new Error("Drive not linked for this user");

  return data as DriveAccountRow;
};

export const ensureAppFolder = async (userId: string) => {
  const acc = await getAccountOrThrow(userId);
  if (acc.folder_id) return { folderId: acc.folder_id };

  const drive = makeDriveClient(acc.refresh_token);

  // Try find an existing folder named env.driveAppFolderName
  const q = [
    `mimeType='application/vnd.google-apps.folder'`,
    `name='${env.driveAppFolderName.replace(/'/g, "\\'")}'`,
    "trashed=false",
  ].join(" and ");

  const found = await drive.files.list({
    q,
    fields: "files(id,name)",
    pageSize: 5,
  });

  let folderId = found.data.files?.[0]?.id ?? null;

  if (!folderId) {
    const created = await drive.files.create({
      requestBody: {
        name: env.driveAppFolderName,
        mimeType: "application/vnd.google-apps.folder",
      },
      fields: "id,name",
    });
    folderId = created.data.id ?? null;
  }

  if (!folderId) throw new Error("Failed to create/find Drive app folder");

  await supabase()
    .from("drive_accounts")
    .update({ folder_id: folderId })
    .eq("user_id", userId);

  return { folderId };
};

export const uploadToDrive = async (userId: string, file: { buffer: Buffer; originalname: string; mimetype: string }) => {
  const acc = await getAccountOrThrow(userId);
  const { folderId } = await ensureAppFolder(userId);

  const drive = makeDriveClient(acc.refresh_token);

  const res = await drive.files.create({
    requestBody: {
      name: file.originalname,
      parents: [folderId],
    },
    media: {
      mimeType: file.mimetype,
      body: Readable.from(file.buffer),
    },
    fields: "id,name,mimeType,modifiedTime,md5Checksum",
  });

  const f = res.data;
  // track in supabase (pending until indexed)
  if (f.id) {
    await supabase()
      .from("drive_files")
      .upsert({
        user_id: userId,
        drive_file_id: f.id,
        name: f.name ?? null,
        mime_type: f.mimeType ?? null,
        md5_checksum: (f as any).md5Checksum ?? null,
        modified_time: f.modifiedTime ?? null,
        doc_id: `drive:${f.id}`,
        status: "pending",
      });
  }

  return f;
};

const listFolderFiles = async (drive: any, folderId: string) => {
  const out: any[] = [];
  let pageToken: string | undefined;

  do {
    const r = await drive.files.list({
      q: `'${folderId}' in parents and trashed=false`,
      fields: "nextPageToken, files(id,name,mimeType,modifiedTime,md5Checksum,size)",
      pageSize: 200,
      pageToken,
    });
    out.push(...(r.data.files ?? []));
    pageToken = r.data.nextPageToken ?? undefined;
  } while (pageToken);

  return out;
};

const exportGoogleDocToText = async (drive: any, fileId: string, mimeType: string) => {
  // Docs / Sheets / Slides exports
  if (mimeType === "application/vnd.google-apps.document") {
    const r = await drive.files.export({ fileId, mimeType: "text/plain" }, { responseType: "text" });
    return String(r.data ?? "");
  }
  if (mimeType === "application/vnd.google-apps.spreadsheet") {
    const r = await drive.files.export({ fileId, mimeType: "text/csv" }, { responseType: "text" });
    return String(r.data ?? "");
  }
  if (mimeType === "application/vnd.google-apps.presentation") {
    const r = await drive.files.export({ fileId, mimeType: "text/plain" }, { responseType: "text" });
    return String(r.data ?? "");
  }
  return "";
};

const downloadFileBytes = async (drive: any, fileId: string): Promise<Buffer> => {
  const r = await drive.files.get({ fileId, alt: "media" }, { responseType: "arraybuffer" });
  return Buffer.from(r.data as ArrayBuffer);
};

const extractPdfViaPython = async (pdfBytes: Buffer) => {
  const payload = { fileBase64: pdfBytes.toString("base64") };
  const r = await pythonClient.post("/internal/extract/pdf", payload);
  return r.data as { pages: { page_number: number; text: string }[]; total_pages: number };
};

export const syncDriveToIndex = async (userId: string) => {
  const acc = await getAccountOrThrow(userId);
  const { folderId } = await ensureAppFolder(userId);

  const drive = makeDriveClient(acc.refresh_token);
  const files = await listFolderFiles(drive, folderId);

  // Build a set for deletion detection
  const liveIds = new Set(files.map(f => f.id).filter(Boolean));

  // Mark deletions (and delete vectors)
  const existing = await supabase()
    .from("drive_files")
    .select("drive_file_id, doc_id, status")
    .eq("user_id", userId);

  for (const row of (existing.data ?? []) as any[]) {
    if (!liveIds.has(row.drive_file_id) && row.status !== "deleted") {
      const docId = row.doc_id || `drive:${row.drive_file_id}`;
      try {
        await aiService.deleteDocIndex(userId, docId);
      } catch {
        // don't block; still mark deleted
      }
      await supabase()
        .from("drive_files")
        .update({ status: "deleted" })
        .eq("user_id", userId)
        .eq("drive_file_id", row.drive_file_id);
    }
  }

  const results: any[] = [];
  let indexed = 0, skipped = 0, errored = 0;

  for (const f of files) {
    const fileId = f.id;
    if (!fileId) continue;

    const docId = `drive:${fileId}`;
    const modifiedTime = f.modifiedTime ? new Date(f.modifiedTime).toISOString() : null;

    const { data: st } = await supabase()
      .from("drive_files")
      .select("indexed_modified_time,status")
      .eq("user_id", userId)
      .eq("drive_file_id", fileId)
      .maybeSingle();

    // Skip if already indexed at same/newer modified_time
    if (st?.indexed_modified_time && modifiedTime && new Date(st.indexed_modified_time) >= new Date(modifiedTime)) {
      skipped++;
      results.push({ fileId, name: f.name, status: "skipped", reason: "already indexed" });
      continue;
    }

    try {
      const mime = f.mimeType || "";
      let pages: { page_number: number; text: string }[] = [];

      // Google native formats
      if (mime.startsWith("application/vnd.google-apps.")) {
        const text = await exportGoogleDocToText(drive, fileId, mime);
        pages = [{ page_number: 1, text }];
      }
      // Images -> OCR
      else if (mime.startsWith("image/")) {
        const bytes = await downloadFileBytes(drive, fileId);
        const ocr = await pythonClient.post("/internal/ocr", {
          jobId: `job_drive_${fileId}`,
          pageId: `drive_${fileId}`,
          imageBase64: bytes.toString("base64"),
          options: { languages: ["vi", "en"], returnLayout: false },
        });
        pages = [{ page_number: 1, text: String(ocr.data?.text ?? "") }];
      }
      // PDF -> extract text via Python
      else if (mime === "application/pdf") {
        const bytes = await downloadFileBytes(drive, fileId);
        const extracted = await extractPdfViaPython(bytes);
        pages = extracted.pages ?? [{ page_number: 1, text: "" }];
      }
      // text/plain fallback
      else if (mime === "text/plain") {
        const bytes = await downloadFileBytes(drive, fileId);
        pages = [{ page_number: 1, text: bytes.toString("utf-8") }];
      }
      else {
        // unsupported for now
        skipped++;
        await supabase().from("drive_files").upsert({
          user_id: userId,
          drive_file_id: fileId,
          name: f.name ?? null,
          mime_type: mime || null,
          md5_checksum: (f as any).md5Checksum ?? null,
          modified_time: modifiedTime,
          doc_id: docId,
          status: "skipped",
          last_error: `Unsupported mimeType: ${mime}`,
        });
        results.push({ fileId, name: f.name, status: "skipped", reason: `unsupported mimeType: ${mime}` });
        continue;
      }

      // Upsert to your existing RAG index
      await aiService.upsertOcrIndex(userId, {
        doc_id: docId,
        title: f.name ?? docId,
        replace: true,
        pages,
      });

      indexed++;
      await supabase().from("drive_files").upsert({
        user_id: userId,
        drive_file_id: fileId,
        name: f.name ?? null,
        mime_type: mime || null,
        md5_checksum: (f as any).md5Checksum ?? null,
        modified_time: modifiedTime,
        doc_id: docId,
        status: "indexed",
        last_error: null,
        indexed_at: new Date().toISOString(),
        indexed_modified_time: modifiedTime,
      });

      results.push({ fileId, name: f.name, status: "indexed", pages: pages.length });
    } catch (e: any) {
      errored++;
      await supabase().from("drive_files").upsert({
        user_id: userId,
        drive_file_id: fileId,
        name: f.name ?? null,
        mime_type: f.mimeType ?? null,
        md5_checksum: (f as any).md5Checksum ?? null,
        modified_time: modifiedTime,
        doc_id: docId,
        status: "error",
        last_error: String(e?.message ?? e),
      });

      results.push({ fileId, name: f.name, status: "error", error: String(e?.message ?? e) });
    }
  }

  return {
    folderId,
    counts: { total: files.length, indexed, skipped, errored },
    results,
  };
};
