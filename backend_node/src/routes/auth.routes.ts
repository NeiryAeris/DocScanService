import { Router } from "express";
import * as authController from "../controllers/auth.controller";
import { firebaseAuthMiddleware } from "../middlewares/firebase_auth.middleware";

export const router = Router();

router.post("/login", authController.login);
router.get("/me", authController.me);

// ✅ Firebase token test
router.get("/firebase/me", firebaseAuthMiddleware, (req, res) => {
  // @ts-expect-error attached by middleware
  res.json({ user: req.user });
});