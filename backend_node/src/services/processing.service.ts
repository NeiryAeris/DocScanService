import {pythonClient} from "../integrations/python.client";

interface OcrPageInput {
  userId: string;
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
        languages: ["vie", "eng"],
        returnLayout: true
    }
  };
    const response = await pythonClient.post('/internal/ocr', payload);
    
    // later: save to DB, update job status, etc.
    return response.data;
};
    