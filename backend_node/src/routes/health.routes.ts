import { Router } from "express";

export const router = Router();

router.get("/", (req, res) => {
    res.status(200).json({ status: "OK", message: "Health check passed" });
});