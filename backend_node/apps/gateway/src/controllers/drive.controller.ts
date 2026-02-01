import { Request, Response } from "express";
import * as driveService from "../services/drive.service";

export const status = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string;
  const r = await driveService.getDriveStatus(userId);
  res.json(r);
};

export const oauthStart = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string;
  const r = driveService.makeOauthStartUrl(userId);
  res.json(r);
};

// NOTE: callback is visited by browser (no Firebase header). state JWT maps to uid.
export const oauthCallback = async (req: Request, res: Response) => {
  try {
    const code = String(req.query.code ?? "");
    const state = String(req.query.state ?? "");
    if (!code || !state) return res.status(400).send("Missing code/state");

    await driveService.handleOauthCallback(code, state);

    res
      .status(200)
      .send(`
        <html>
          <body style="font-family: sans-serif;">
            <h2>✅ Google Drive linked</h2>
            <p>You can close this tab and return to the app.</p>
          </body>
        </html>
      `);
  } catch (e: any) {
    res.status(500).send(`Drive link failed: ${String(e?.message ?? e)}`);
  }
};

export const initFolder = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string;
  const r = await driveService.ensureAppFolder(userId);
  res.json(r);
};

export const upload = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string;
  const file = (req as any).file as Express.Multer.File | undefined;

  if (!file) return res.status(400).json({ error: "Missing multipart file field: file" });

  const r = await driveService.uploadToDrive(userId, {
    buffer: file.buffer,
    originalname: file.originalname,
    mimetype: file.mimetype,
  });
  res.json(r);
};

export const sync = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string;
  const r = await driveService.syncDriveToIndex(userId);
  res.json(r);
};
