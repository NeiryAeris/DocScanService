import { Router } from "express";
import * as authController from "../controllers/auth.controller";
import { supabaseAuth } from "../middlewares/auth.middleware";

export const router = Router();

router.post("/login", authController.login);
router.get("/me", authController.me);

// ✅ Supabase token test
router.get("/supabase/me", supabaseAuth, (req, res) => {
  // @ts-expect-error attached by middleware
  res.json({ user: req.user });
});