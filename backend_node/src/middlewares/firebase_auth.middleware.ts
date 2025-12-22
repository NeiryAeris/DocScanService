import { Request, Response, NextFunction } from "express";
import { getFirebaseAdmin } from "../integrations/firebase.admin";

export const firebaseAuthMiddleware = async (req: Request, res: Response, next: NextFunction) => {
  try {
    const auth = req.header("Authorization") || "";
    const m = auth.match(/^Bearer (.+)$/);
    if (!m) return res.status(401).json({ error: "Missing Bearer token" });

    const admin = getFirebaseAdmin();
    const decoded = await admin.auth().verifyIdToken(m[1]);

    // attach user
    (req as any).user = {
      id: decoded.uid,
      email: decoded.email,
    };

    next();
  } catch (e: any) {
    return res.status(401).json({ error: "Invalid Firebase token", detail: String(e?.message ?? e) });
  }
};
