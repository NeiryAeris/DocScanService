import { Global, Module } from "@nestjs/common";
import Redis from "ioredis";

export const REDIS = Symbol('REDIS')

@Global()
@Module({
    providers: [
        {provide: REDIS,
        useFactory: () => {
            const url = process.env.REDIS_URL
            if (!url) throw new Error('REDIS_URL is not defined')
            return new Redis(url, {maxRetriesPerRequest: 3})
        }}
    ],
    exports: [REDIS]
})

export class RedisModule {}