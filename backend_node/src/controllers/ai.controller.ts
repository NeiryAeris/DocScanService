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
  if (!userId) return res.status(401).json({ response: null, error: "Unauthorized" });

  const body: any = req.body || {};

  // Android sends: { prompt, history: [{role,text}...] }
  // Python expects: { question, doc_ids?, top_k? }
  const question: string | undefined =
    body.question ??
    body.prompt ??
    (() => {
      const h = Array.isArray(body.history) ? body.history : [];
      for (let i = h.length - 1; i >= 0; i--) {
        const m = h[i];
        if (m?.role === "user" && typeof m?.text === "string" && m.text.trim()) return m.text.trim();
      }
      return undefined;
    })();

  if (!question) {
    return res.status(400).json({ response: null, error: "Missing question/prompt/history" });
  }

  const doc_ids = body.doc_ids ?? body.docIds ?? undefined;
  const top_k = body.top_k ?? body.topK ?? undefined;

  try {
    const py = await aiService.askChat(userId, { question, doc_ids, top_k } as any);

    // FastAPI returns { answer, citations, used_chunks }
    const answer: string | undefined = py?.answer ?? py?.response;

    if (!answer) {
      return res.status(502).json({ response: null, error: "Upstream returned no answer" });
    }

    // ✅ return shape Android expects
    return res.status(200).json({ response: answer, error: null });
  } catch (e: any) {
    return res.status(502).json({ response: null, error: e?.message || "Upstream error" });
  }
};
