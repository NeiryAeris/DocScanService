import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";

type SupabasePayload = {
  sub: string;
  email?: string;
  role?: string;
  aud?: string;
  exp?: number;
  iat?: number;
};

declare global {
  namespace Express {
    interface Request {
      user?: { id: string; email?: string };
    }
  }
}

export const authMiddleware = (req: Request, res: Response, next: NextFunction) => {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return res.status(401).json({ error: "Missing or invalid Authorization header" });
  }

  const token = authHeader.slice("Bearer ".length).trim();

  try {
    const payload = jwt.verify(token, env.jwtSecret) as {
      sub: string;
      email?: string;
    };

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
};

export const supabaseAuth = (req: Request, res: Response, next: NextFunction) => {
    try {
        const authHeader  = req.headers.authorization
        if (!authHeader?.startsWith('Bearer ')) {
            return res.status(401).json({error: 'Missing Authorization Bearer token'})
        }

        const token = authHeader.slice('Bearer '.length).trim()
        const secret = process.env.SUPABASE_JWT_TOKEN

        if (!secret) {
            return res.status(500).json({error: 'SUPABASE_JWT_TOKEN is not set'})
        }

        const decoded = jwt.verify(token, secret) as SupabasePayload;

        if (!decoded?.sub) {
            return res.status(401).json({error: 'Invalid token playload'})
        }

        req.user = {id: decoded.sub, email: decoded.email}
        next();
    } catch (err: any) {
        return res.status(401).json({error: 'Invalid or expired token'})
    }
};
