import { pythonClient } from "../integrations/python.client";

interface OcrPageInput {
  userId?: string;
  pageId: string;
  imageBase64?: string;
  imageUrl?: string;
}

export const ocrPage = async (input: OcrPageInput): Promise<{ text: string }> => {
  const { pageId, imageBase64, imageUrl } = input;

  const payload = {
    jobId: "job_" + pageId,
    pageId,
    imageUrl,     // optional for future
    imageBase64,  // actual raw image for now
    options: {
      languages: ["vi", "en"],
      returnLayout: true,
    },
  };

  const response = await pythonClient.post("/internal/ocr", payload);
  return response.data;
};

interface HandwritingPageInput {
  userId?: string;
  pageId: string;
  imageBase64?: string;
  imageUrl?: string;
  strength?: "low" | "medium" | "high";
}

export const removeHandwritingPage = async (
  input: HandwritingPageInput
): Promise<{ jobId: string; status: string; cleanImageUrl?: string; error?: string }> => {
  const { pageId, imageBase64, imageUrl, strength } = input;

  const payload = {
    jobId: "hw_" + pageId,
    pageId,
    imageUrl,
    imageBase64,
    options: {
      strength: strength || "medium",
    },
  };

  // WPI can be slow → override timeout for this call
  const response = await pythonClient.post("/internal/remove-handwriting", payload, {
    timeout: 300_000, // 5 minutes
  });

  return response.data;
};
