import { Router } from "express"
import { router as heatlthRouter } from "./health.routes";
import { router as authRouter } from "./auth.routes";
import { router as pyHealthRouter } from "./py-health.routes";
import { router as documentRouter } from "./documents.routes";
import { router as pageRouter } from "./pages.routes";
import { router as aiRouter } from "./ai.routes";


export const router = Router()

router.use('/health', heatlthRouter);
router.use('/py-health', pyHealthRouter);
router.use('/auth', authRouter);
// router.use('/users', userRouter);
router.use('/documents', documentRouter);
router.use('/pages', pageRouter);
router.use("/ai", aiRouter);