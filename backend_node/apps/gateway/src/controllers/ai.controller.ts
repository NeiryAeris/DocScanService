import { Request, Response } from "express";
import axios from "axios";
import * as aiService from "../services/ai.service";

/**
 * Android chat history uses role = "model" for assistant messages.
 * Processing service expects role in {user, assistant, system}.
 * Normalize here so we never send invalid schema -> avoid 422.
 */
function normalizeHistory(
  raw: any
): { role: "user" | "assistant" | "system"; text: string }[] | undefined {
  if (!Array.isArray(raw)) return undefined;

  const out: { role: "user" | "assistant" | "system"; text: string }[] = [];
  for (const m of raw) {
    const roleRaw = String(m?.role ?? "user").toLowerCase();
    const text = String(m?.text ?? m?.content ?? "").trim();
    if (!text) continue;

    const role: "user" | "assistant" | "system" =
      roleRaw === "assistant" || roleRaw === "model"
        ? "assistant"
        : roleRaw === "system"
        ? "system"
        : "user";

    out.push({ role, text });
  }
  return out.length ? out : undefined;
}

export const upsertOcrIndex = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const data = await aiService.upsertOcrIndex(userId, req.body);
  return res.status(200).json(data);
};

export const upsertPdfIndex = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const file = (req as any).file as Express.Multer.File | undefined;
  if (!file?.buffer) return res.status(400).json({ error: "Missing PDF file (field name: file)" });

  const doc_id = (req.body?.doc_id || req.body?.docId) as string | undefined;
  if (!doc_id) return res.status(400).json({ error: "Missing doc_id" });

  const title = (req.body?.title as string | undefined) ?? file.originalname;
  const replace = String(req.body?.replace ?? "true") !== "false";

  // 1) Extract born-digital text
  const extracted = await aiService.extractPdf(userId, file.buffer.toString("base64"));
  const pages = (extracted?.pages || [])
    .filter((p: any) => (p?.text || "").trim().length > 0); // drop empty pages

  if (pages.length === 0) {
    return res.status(200).json({ indexed: false, chunks: 0, replaced: replace, reason: "No text extracted" });
  }

  // 2) Upsert using existing OCR index endpoint (it’s just pages of text)
  const data = await aiService.upsertOcrIndex(userId, {
    doc_id,
    title,
    replace,
    pages,
  } as any);

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

  // ✅ IMPORTANT:
  // - if doc_ids provided => default to "doc" (RAG)
  // - otherwise => default to "general" (pure chat, no vector search)
  const mode =
    body.mode ??
    ((Array.isArray(doc_ids) && doc_ids.length > 0) ? "doc" : "general");

  const history = normalizeHistory(body.history);
  const min_score = typeof body.min_score === "number" ? body.min_score : undefined;

  try {
    const py = await aiService.askChat(userId, { question, doc_ids, top_k, mode, history, min_score } as any);

    const answer: string | undefined = py?.answer ?? py?.response;
    if (!answer) {
      return res.status(502).json({ response: null, error: "Upstream returned no answer" });
    }

    // ✅ return richer shape (Android RemoteAiAskResponseDto supports these)
    return res.status(200).json({
      answer,                // optional
      response: answer,      // keep backward-compat
      error: null,
      citations: py?.citations ?? [],
      used_chunks: py?.used_chunks ?? 0
    });
  } catch (e: any) {
    // If upstream (FastAPI) rejects schema, expose it (don't mask as 502)
    if (axios.isAxiosError(e) && e.response) {
      return res.status(e.response.status).json({
        response: null,
        error: `Upstream HTTP ${e.response.status}`,
        detail: e.response.data,
      });
    }

    return res.status(502).json({ response: null, error: e?.message || "Upstream error" });
  }

};
