import { Router } from "express";
import { supabaseAuth } from "../middlewares/auth.middleware";
import * as chatController from "../controllers/chat.controller";

export const router = Router();

// Android Chat UI expects Supabase auth for /api/chat/*
router.use(supabaseAuth);

// POST /api/chat/ask
router.post("/ask", chatController.ask);
