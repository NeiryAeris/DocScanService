import axios from "axios";

const baseURL = process.env.PYTHON_BASE_URL;
const internalToken = process.env.PYTHON_INTERNAL_TOKEN;

if (!baseURL) throw new Error("Missing PYTHON_BASE_URL");
if (!internalToken) throw new Error("Missing PYTHON_INTERNAL_TOKEN");

export const python = axios.create({
  baseURL,
  timeout: 60_000,
});

export function pythonHeaders(userId: string) {
  return {
    "X-Internal-Token": internalToken!,
    "X-User-Id": userId,
  };
}