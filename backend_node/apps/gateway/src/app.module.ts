import { Module } from "@nestjs/common";
import { LoggerModule } from "nestjs-pino";
import { randomUUID } from "crypto";

import { HealthModule } from "./health/health.module";
import { PrismaModule } from './prisma/prisma.module'
import { NotesModule } from './notes/notes.module'

@Module({
  imports: [
    LoggerModule.forRoot({
      pinoHttp: {
        level: process.env.LOG_LEVEL ?? "info",
        transport:
          process.env.NODE_ENV !== "production"
            ? {
                target: "pino-pretty",
                options: { singleLine: true, colorize: true },
              }
            : undefined,
        genReqId: (req, res) => {
          const incoming = req.headers["x-request-id"];
          const requestId = (Array.isArray(incoming) ? incoming[0] : incoming) ?? randomUUID();
          (req as any).id = requestId;
          res.setHeader("x-request-id", requestId);
          return requestId;
        },
      },
    }),
    HealthModule,
    PrismaModule,
    NotesModule
  ],
})
export class AppModule {}
