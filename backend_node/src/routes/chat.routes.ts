import { Router } from "express";
import { firebaseAuthMiddleware } from "../middlewares/firebase_auth.middleware";
import * as chatController from "../controllers/chat.controller";

export const router = Router();

// Android Chat UI expects Firebase auth for /api/chat/*
router.use(firebaseAuthMiddleware);

// POST /api/chat/ask
router.post("/ask", chatController.ask);
