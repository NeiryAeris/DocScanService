import { Router } from "express";
import * as documentsController from "../controllers/documents.controller";
import { firebaseAuthMiddleware } from "../middlewares/firebase_auth.middleware";
import { authMiddleware } from "../middlewares/auth.middleware";

export const router = Router();

router.use(firebaseAuthMiddleware);

router.post("/", documentsController.createDocument);
router.get("/", documentsController.getDocuments);
router.get("/:id", documentsController.getDocumentById);
// router.put("/:id", documentsController.updateDocument);
// router.delete("/:id", documentsController.deleteDocument);