import { pythonClient } from "../integrations/python.client";

export type UpsertOcrBody = {
  doc_id: string;
  title?: string;
  replace?: boolean;
  pages: { page_number: number; text: string }[];
};

export type ChatHistoryItem = {
  role: "user" | "assistant" | "system";
  text: string;
};

export type AskBody = {
  question: string;
  doc_ids?: string[];
  top_k?: number;
  mode?: "auto" | "doc" | "general";
  history?: ChatHistoryItem[];
  min_score?: number;
};

export const upsertOcrIndex = async (userId: string, body: UpsertOcrBody) => {
  const r = await pythonClient.post("/internal/index/upsert_ocr", body, {
    headers: { "X-User-Id": userId },
  });
  return r.data;
};

export const deleteDocIndex = async (userId: string, doc_id: string) => {
  const r = await pythonClient.post("/internal/index/delete_doc", { doc_id }, {
    headers: { "X-User-Id": userId },
  });
  return r.data;
};

export const askChat = async (userId: string, body: AskBody) => {
  const r = await pythonClient.post("/internal/chat/ask", body, {
    headers: { "X-User-Id": userId },
  });
  return r.data;
};
