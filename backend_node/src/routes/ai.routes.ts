import { Router } from "express";
import { firebaseAuthMiddleware } from "../middlewares/firebase_auth.middleware";
import * as aiController from "../controllers/ai.controller";

export const router = Router();

router.use(firebaseAuthMiddleware);

router.post("/index/upsert-ocr", aiController.upsertOcrIndex);
router.post("/index/delete", aiController.deleteDocIndex);
router.post("/chat/ask", aiController.askChat);
