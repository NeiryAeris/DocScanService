import {pythonClient} from "../integrations/python.client";

interface OcrPageInput {
    userId: string;
    pageId: string;
    imageUrl: string;
}

export const ocrPage = async (input: OcrPageInput): Promise<{ text: string }> => {
    const {pageId, imageUrl} = input;

    const payload = {
        jobId: 'job_' + pageId,
        pageId,
        imageUrl,
        options: {
            languages: ['vi', 'en'],
            returnLayout: true
        }
    }
    const response = await pythonClient.post('/internal/ocr', payload);
    
    // later: save to DB, update job status, etc.
    return response.data;
};
    