import { Router } from "express";
import multer from "multer";
import { firebaseAuthMiddleware } from "../middlewares/firebase_auth.middleware";
import * as driveController from "../controllers/drive.controller";

export const router = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 25 * 1024 * 1024 }, // 25MB (tune as needed)
});

// Auth-required endpoints
router.get("/status", firebaseAuthMiddleware, driveController.status);
router.get("/oauth2/start", firebaseAuthMiddleware, driveController.oauthStart);
router.post("/folder/init", firebaseAuthMiddleware, driveController.initFolder);
router.post("/upload", firebaseAuthMiddleware, upload.single("file"), driveController.upload);
router.post("/sync", firebaseAuthMiddleware, driveController.sync);

// Public callback endpoint (browser redirect)
router.get("/oauth2/callback", driveController.oauthCallback);
