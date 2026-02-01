import axios from "axios";
import { env } from "../config/env";

export const pythonClient = axios.create({
  baseURL: env.pythonServiceUrl,
  // Chat/RAG can take time (vector search + LLM)
  // Increase to avoid gateway returning 502 while processing is still working.
  timeout: 120000
});

pythonClient.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-Internal-Token"] = env.pythonInternalToken;
  return config;
});
