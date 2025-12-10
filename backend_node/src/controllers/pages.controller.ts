import { Request, Response } from "express";
import * as processingService from "../services/processing.service";

export const ocrPage = async (req: Request, res: Response) => {
  // @ts-expect-error
  const userId: string = req.user.id;
  const { pageId } = req.params;

  // later we’ll load page from DB; for now assume we have imageUrl from body
  const { imageUrl } = req.body;

  if (!imageUrl) {
    return res.status(400).json({ error: "imageUrl is required for now" });
  }

  const result = await processingService.ocrPage({
    userId,
    pageId,
    imageUrl,
  });

  res.json(result);
};
