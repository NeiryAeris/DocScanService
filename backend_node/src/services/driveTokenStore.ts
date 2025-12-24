import fs from "node:fs/promises";
import path from "node:path";

export type DriveTokens = {
  access_token?: string;
  refresh_token?: string;
  scope?: string;
  token_type?: string;
  expiry_date?: number;
};

export type DriveUserState = {
  userId: string;
  tokens: DriveTokens;
  folderId?: string;
  lastSyncIso?: string;
};

export interface DriveTokenStore {
  get(userId: string): Promise<DriveUserState | null>;
  upsert(state: DriveUserState): Promise<void>;
}

/**
 * Dev-only token store.
 * - Works locally
 * - NOT suitable for serverless (Vercel) or production (no persistence / no encryption)
 */
export class FileDriveTokenStore implements DriveTokenStore {
  private filePath: string;

  constructor(filePath?: string) {
    // In serverless, only /tmp is writable. In local dev, keep it in repo.
    const baseDir = process.env.DRIVE_TOKEN_DIR || path.join(process.cwd(), ".data");
    this.filePath = filePath || path.join(baseDir, "drive_tokens.json");
  }

  private async ensureFile(): Promise<void> {
    const dir = path.dirname(this.filePath);
    await fs.mkdir(dir, { recursive: true });
    try {
      await fs.access(this.filePath);
    } catch {
      await fs.writeFile(this.filePath, JSON.stringify({}, null, 2), "utf-8");
    }
  }

  private async readAll(): Promise<Record<string, DriveUserState>> {
    await this.ensureFile();
    const raw = await fs.readFile(this.filePath, "utf-8");
    try {
      return JSON.parse(raw) as Record<string, DriveUserState>;
    } catch {
      return {};
    }
  }

  private async writeAll(data: Record<string, DriveUserState>): Promise<void> {
    await this.ensureFile();
    await fs.writeFile(this.filePath, JSON.stringify(data, null, 2), "utf-8");
  }

  async get(userId: string): Promise<DriveUserState | null> {
    const all = await this.readAll();
    return all[userId] || null;
  }

  async upsert(state: DriveUserState): Promise<void> {
    const all = await this.readAll();
    all[state.userId] = state;
    await this.writeAll(all);
  }
}
