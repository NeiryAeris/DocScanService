import { Router } from "express";
import * as pagesController from "../controllers/pages.controller";
import { authMiddleware } from "../middlewares/auth.middleware";
import multer from "multer";

export const router = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  fileFilter: (_req, file, cb) => {
    // Only accept image/* mimetypes
    if (file.mimetype.startsWith("image/")) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed"));
    }
  }
});

router.post(
  "/:pageId/ocr",
  upload.single("pageImage"),   // <- match Android field name
  pagesController.ocrPage
);

router.post(
  "/:pageId/remove-handwriting",
  upload.single("pageImage"), // same Android field name
  pagesController.removeHandwritingPage
);