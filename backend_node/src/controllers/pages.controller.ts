import { Request, Response } from "express";
import * as processingService from "../services/processing.service";

interface AuthedRequest extends Request {
  user?: {id: string; email?: string};
  file?: Express.Multer.File;
}

export const ocrPage = async (req: AuthedRequest, res: Response) => {
  // @ts-expect-error
  const userId: string = req.user.id;
  const { pageId } = req.params;

  const file = req.file;
  const imageUrl = req.body.imageUrl; // optional fallback

  if (!file && !imageUrl) {
    return res.status(400).json({ error: "Must provide either file or imageUrl" });
  }

  // Prepare image payload for backend
  let imageBase64: string | undefined;

  if (file) {
    imageBase64 = file.buffer.toString("base64");
  }

  const result = await processingService.ocrPage({
    userId,
    pageId,
    imageBase64,
    imageUrl, // optional
  });

  res.json(result);
};
