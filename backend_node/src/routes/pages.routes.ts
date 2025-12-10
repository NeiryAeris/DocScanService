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

router.use(authMiddleware);

// router.post("/", pagesController.createPage);
// router.get("/", pagesController.getPages);
// router.get("/:id", pagesController.getPageById);
// router.put("/:id", pagesController.updatePage);
// router.delete("/:id", pagesController.deletePage);
// router.post("/:pageId/ocr", pagesController.ocrPage);

router.post(
  "/:pageId/ocr",
  upload.single("pageImage"),   // <- match Android field name
  pagesController.ocrPage
);