import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";

export const authMiddleware = (
    req: Request,
    res: Response,
    next: NextFunction
) => {
    const authHeader = req.headers.authorization; 
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
        return res.status(401).json({ error: "Missing or invalid Authorization header" });
    }

    const token = authHeader.slice("Bearer ".length).trim();

    try {
        const payload = jwt.verify(token, env.jwtSecret) as {
            sub: string;
            email?: string;
        }

        // attach user to req
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (req as any).user = {
            id: payload.sub,
            email: payload.email,
        };
        next();
    } catch (err) {
        return res.status(401).json({ error: "Invalid or expired token" });
    }
}