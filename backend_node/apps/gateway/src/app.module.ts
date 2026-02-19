import { Module } from "@nestjs/common";
import { LoggerModule } from "nestjs-pino";
import { randomUUID } from "crypto";
import { ThrottlerModule } from "@nestjs/throttler";

import { HealthModule } from "./health/health.module";
import { PrismaModule } from "./prisma/prisma.module";
import { NotesModule } from "./notes/notes.module";
import { RedisModule, REDIS } from "./redis/redis.module";
import { ThrottlerRedisStorage } from "./security/throttler-redis.storage";
import type Redis from "ioredis";
import { CacheModule } from "./cache/cache.module";

@Module({
  imports: [
    LoggerModule.forRoot({
      pinoHttp: {
        level: process.env.LOG_LEVEL ?? "info",
        transport:
          process.env.NODE_ENV !== "production"
            ? { target: "pino-pretty", options: { singleLine: true } }
            : undefined,
        genReqId: (req, res) => {
          const incoming = req.headers["x-request-id"];
          const id =
            (Array.isArray(incoming) ? incoming[0] : incoming) ?? randomUUID();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          (req as any).id = id;
          res.setHeader("x-request-id", id);
          return id;
        }
      }
    }),
    RedisModule,
    ThrottlerModule.forRootAsync({
      inject: [REDIS],
      useFactory: (redis: Redis) => ({
        throttlers: [
          // default global limit (tweak later)
          { ttl: 60, limit: 120 }
        ],
        storage: new ThrottlerRedisStorage(redis)
      })
    }),
    PrismaModule,
    HealthModule,
    RedisModule,
    CacheModule,
    NotesModule
  ]
})
export class AppModule {}