import { Router } from "express";
import multer from "multer";
import { supabaseAuth } from "../middlewares/auth.middleware";
import * as driveController from "../controllers/drive.controller";

export const router = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }, // 25MB (tune as needed)
});

// Auth-required endpoints
router.get("/status", supabaseAuth, driveController.status);
router.get("/oauth2/start", supabaseAuth, driveController.oauthStart);
router.post("/folder/init", supabaseAuth, driveController.initFolder);
router.post("/upload", supabaseAuth, upload.single("file"), driveController.upload);
router.post("/sync", supabaseAuth, driveController.sync);
// Public callback endpoint (browser redirect)
router.get("/oauth2/callback", driveController.oauthCallback);
