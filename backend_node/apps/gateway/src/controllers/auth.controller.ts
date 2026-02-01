import { Request, Response } from "express";
import jwt from "jsonwebtoken";
import { env } from "../config/env";

// Mock user data for demonstration purposes

const fakeUser = {
  id: "user_1",
  email: "demo@example.com",
};

export const login = (req: Request, res: Response) => {
  // For now, accept any email/password and return fake user
  const { email } = req.body;

  const token = jwt.sign({ sub: fakeUser.id, email: email || fakeUser.email }, env.jwtSecret, { expiresIn: "7d" });

  res.json({
    user: { id: fakeUser.id, email: email || fakeUser.email },
    accessToken: token,
  });
};

export const me = (req: Request, res: Response) => {
  // authMiddleware will attach user to req
  // @ts-expect-error added in middleware
  const user = req.user;
  res.json({ user });
};