import { Request, Response } from "express";
import * as processingService from "../services/processing.service";

export const ocrPage = async (req: Request, res: Response) => {
  // @ts-expect-error user added by middleware
  const userId: string = req.user.id;
  const { pageId } = req.params;

  const file = req.file;
  const imageUrl = req.body.imageUrl; // optional future use

  if (!file && !imageUrl) {
    return res.status(400).json({ error: "Must provide either pageImage file or imageUrl" });
  }

  let imageBase64: string | undefined;
  if (file) {
    imageBase64 = file.buffer.toString("base64");
  }

  const result = await processingService.ocrPage({
    userId,
    pageId,
    imageBase64,
    imageUrl
  });

  res.json(result);
};