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

  const data = await aiService.askChat(userId, req.body);
  return res.status(200).json(data);
};
