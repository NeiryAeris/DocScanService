import { Router } from "express";

export const router = Router();

router.get("/", async (_req, res) => {
  const base = process.env.PYTHON_SERVICE_URL;

  if (!base) {
    return res.status(500).json({
      ok: false,
      error: "Missing PYTHON_SERVICE_URL",
    });
  }

  try {
    const response = await fetch(`${base}/health`);
    const data = await response.json();

    return res.json({
      ok: true,
      python: data,
    });
  } catch (err) {
    return res.status(502).json({
      ok: false,
      error: "Failed to reach python service",
      details: String(err),
    });
  }
});
