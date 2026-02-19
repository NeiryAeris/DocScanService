import { CanActivate, ExecutionContext, Injectable, UnauthorizedException } from "@nestjs/common";
import jwt from "jsonwebtoken";

type SupabaseJwtPayload = {
  sub: string;
  email?: string;
  role?: string;
  aud?: string;
  exp?: number;
  iat?: number;
  [k: string]: unknown;
};

@Injectable()
export class SupabaseJwtGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean {
    const req = context.switchToHttp().getRequest<any>();
    const authHeader = req.headers?.authorization;

    if (!authHeader || typeof authHeader !== "string") {
      throw new UnauthorizedException("Missing Authorization header");
    }

    const [type, token] = authHeader.split(" ");
    if (type !== "Bearer" || !token) {
      throw new UnauthorizedException("Invalid Authorization header");
    }

    const secret = process.env.SUPABASE_JWT_SECRET;
    if (!secret) throw new Error("SUPABASE_JWT_SECRET is not defined");

    try {
      const payload = jwt.verify(token, secret) as SupabaseJwtPayload;

      // attach user to request for handlers
      req.user = {
        id: payload.sub,
        email: payload.email,
        role: payload.role
      };

      return true;
    } catch {
      throw new UnauthorizedException("Invalid or expired token");
    }
  }
}