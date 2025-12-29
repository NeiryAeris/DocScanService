import { Request, Response } from "express";
import * as processingService from "../services/processing.service";

export const ocrPage = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
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

function parseStrength(body: any): "low" | "medium" | "high" {
  // multer puts fields into req.body as strings
  const direct = (body?.strength || body?.hwStrength || "").toString().trim().toLowerCase();

  // allow options JSON string: options='{"strength":"high"}'
  let fromOptions = "";
  if (typeof body?.options === "string") {
    try {
      const obj = JSON.parse(body.options);
      fromOptions = (obj?.strength || "").toString().trim().toLowerCase();
    } catch {}
  }

  const s = (direct || fromOptions || "medium").toLowerCase();
  if (s === "low" || s === "high") return s;
  return "medium";
}

export const removeHandwritingPage = async (req: Request, res: Response) => {
  const userId = (req as any).user?.id as string | undefined;
  const { pageId } = req.params;

  const file = req.file;
  const imageUrl = req.body.imageUrl;

  if (!file && !imageUrl) {
    return res.status(400).json({ error: "Must provide either pageImage file or imageUrl" });
  }

  let imageBase64: string | undefined;
  if (file) {
    imageBase64 = file.buffer.toString("base64");
  }

  const strength = parseStrength(req.body);

  const result = await processingService.removeHandwritingPage({
    userId,
    pageId,
    imageBase64,
    imageUrl,
    strength,
  });

  res.json(result);
};