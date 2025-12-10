import axios from "axios";
import { env } from "../config/env";

export const pythonClient = axios.create({
  baseURL: env.pythonServiceUrl,
  timeout: 30000
});

pythonClient.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-Internal-Token"] = env.pythonInternalToken;
  return config;
});
