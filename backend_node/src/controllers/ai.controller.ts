import { Request, Response } from "express";
import * as aiService from "../services/ai.service";

export const upsertOcrIndex = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const data = await aiService.upsertOcrIndex(userId, req.body);
  return res.status(200).json(data);
};

export const deleteDocIndex = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const { doc_id } = req.body || {};
  if (!doc_id) return res.status(400).json({ error: "Missing doc_id" });

  const data = await aiService.deleteDocIndex(userId, doc_id);
  return res.status(200).json(data);
};

export const askChat = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const body: any = req.body || {};

  // Accept both shapes:
  // - new/expected: { question, doc_ids, top_k }
  // - android-ui (current): { prompt, history, docIds, topK }
  const question =
    body.question ??
    body.prompt ??
    (() => {
      const h = Array.isArray(body.history) ? body.history : [];
      // take the last user message if present
      for (let i = h.length - 1; i >= 0; i--) {
        if (h[i]?.role === "user" && typeof h[i]?.text === "string") return h[i].text;
      }
      return undefined;
    })();

  if (!question || typeof question !== "string") {
    return res.status(400).json({ error: "Missing question (or prompt/history)" });
  }

  const doc_ids = body.doc_ids ?? body.docIds ?? undefined;
  const top_k = body.top_k ?? body.topK ?? undefined;

  const pythonBody = { question, doc_ids, top_k };

  const data = await aiService.askChat(userId, pythonBody);
  return res.status(200).json(data);
};
