import { Router } from "express"
import { router as heatlthRouter } from "./health.routes";
import { router as authRouter } from "./auth.routes";
// import { router as userRouter } from "./user.routes";
import { router as documentRouter } from "./documents.routes";
import { router as pageRouter } from "./pages.routes";

export const router = Router()

router.use('/health', heatlthRouter);
router.use('/auth', authRouter);
// router.use('/users', userRouter);
router.use('/documents', documentRouter);
router.use('/pages', pageRouter);