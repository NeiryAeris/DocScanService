import { Request, Response } from "express";
import * as aiService from "../services/ai.service";

/**
 * Compatibility controller for the Android Chat UI.
 *
 * Android posts to: POST /api/chat/ask
 * body: { prompt: string, history: [{ role, text }, ...] }
 *
 * The backend RAG endpoint is: POST /api/ai/chat/ask
 * body: { question: string, doc_ids?: string[], top_k?: number }
 */
export const ask = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  if (!userId) return res.status(401).json({ error: "Unauthorized" });

  const { prompt } = (req.body || {}) as { prompt?: string };
  if (!prompt || !String(prompt).trim()) {
    return res.status(400).json({ error: "Missing prompt" });
  }

  // We currently ignore history here; RAG is single-turn.
  const data = await aiService.askChat(userId, { question: String(prompt) });

  // Return a shape that matches the Android DTO (response/error)
  return res.status(200).json({
    response: data?.answer ?? "",
    error: null,
    citations: data?.citations ?? [],
    used_chunks: data?.used_chunks ?? 0,
  });
};
