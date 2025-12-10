import { Request, Response } from "express";
import * as documentService from "../services/document.service";

export const getDocuments = async (req: Request, res: Response) => {
  // @ts-expect-error added in middleware
  const userId: string = req.user.id;

  const docs = await documentService.getDocuments(userId);
  res.json({ documents: docs });
};

export const createDocument = async (req: Request, res: Response) => {
    // @ts-expect-error added in middleware
    const userId: string = req.user.id;
    const {title} = req.body;

    const doc = await documentService.createDocument(userId, title);
    res.status(201).json({ document: doc });
}

export const getDocumentById = async (req: Request, res: Response) => {
    // @ts-expect-error added in middleware
    const userId: string = req.user.id;
    const { id } = req.params;

    const doc = await documentService.getDocumentById(userId,id);
    if (!doc) {
        return res.status(404).json({ message: "Document not found" });
    }
};