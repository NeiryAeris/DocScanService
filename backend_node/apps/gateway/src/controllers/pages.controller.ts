import { Request, Response } from "express";
import * as processingService from "../services/processing.service";

export const ocrPage = async (req: Request, res: Response) => {
  try {
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
      imageUrl,
    });
    return res.json(result);
  } catch (err: any) {
    const status = err?.response?.status || 500;
    return res.status(status).json({
      error: "OCR failed",
      detail: err?.response?.data || err?.message || String(err),
    });
  }
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
  try {
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

  //return raw image bytes if WPI returns a data URL
  const dataUrl = result.cleanImageUrl || "";
  if (
    result.status === "success" &&
    typeof dataUrl === "string" &&
    dataUrl.startsWith("data:image/") &&
    dataUrl.includes("base64,")
  ) {
    const [meta, b64] = dataUrl.split("base64,", 2);
    const mime = meta.split(";")[0].replace("data:", "") || "image/png";
    const buf = Buffer.from(b64, "base64");

    res.setHeader("Content-Type", mime);
    res.setHeader("Cache-Control", "no-store");
    res.setHeader("Content-Disposition", `inline; filename="clean_${pageId}.png"`);
    return res.status(200).send(buf);
  }

  // fallback: json
  return res.json(result);
  } catch (err: any) {
    const status = err?.response?.status || 500;
    return res.status(status).json({
      error: "Handwriting removal failed",
      detail: err?.response?.data || err?.message || String(err),
    });
  }
};
