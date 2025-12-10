import { Router } from "express";
import * as authController from "../controllers/auth.controller";

export const router = Router();

router.post("/login", authController.login);
// router.post("/register", authController.register);
// router.post("/logout", authController.logout);
// router.post("/refresh-token", authController.refreshToken);
// router.post("/forgot-password", authController.forgotPassword);
// router.post("/reset-password", authController.resetPassword);
// router.get("/verify-email", authController.verifyEmail);
router.get("/me", authController.me);