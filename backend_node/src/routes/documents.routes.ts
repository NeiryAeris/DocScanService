import { Router } from "express";
import * as documentsController from "../controllers/documents.controller";
import { authMiddleware } from "../middlewares/auth.middleware";

export const router = Router();

router.use(authMiddleware);

router.post("/", documentsController.createDocument);
router.get("/", documentsController.getDocuments);
router.get("/:id", documentsController.getDocumentById);
// router.put("/:id", documentsController.updateDocument);
// router.delete("/:id", documentsController.deleteDocument);