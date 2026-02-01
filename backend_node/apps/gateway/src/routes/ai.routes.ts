import { Router } from "express";
import multer from "multer";
import * as aiController from "../controllers/ai.controller";
import { supabaseAuth } from "../middlewares/auth.middleware";

export const router = Router();

router.use(supabaseAuth);

// 25MB (tùy bạn)
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 },
});

router.post("/index/upsert-ocr", aiController.upsertOcrIndex);
router.post("/index/upsert-pdf", upload.single("file"), aiController.upsertPdfIndex);
router.post("/index/delete", aiController.deleteDocIndex);
router.post("/chat/ask", aiController.askChat);
