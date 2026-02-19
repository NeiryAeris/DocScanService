import { Injectable, Inject } from "@nestjs/common";
import { PinoLogger } from "nestjs-pino";
import Redis from "ioredis";
import { REDIS } from "../redis/redis.module";
import { privateca } from "googleapis/build/src/apis/privateca";

type JsonValue = unknown

@Injectable()
export class CacheService {
    constructor(
        @Inject(REDIS) private readonly redis: Redis,
        private readonly logger: PinoLogger
    ) {
        this.logger.setContext(CacheService.name)
    }

    async getJson<T = JsonValue>(key: string): Promise<T | null> {
       try {
        const raw = await this.redis.get(key)
        if(!raw) {
            this.logger.debug({key}, 'cache.miss')
            return null
        }
        this.logger.debug({key}, 'cache.hit');
        return JSON.parse(raw) as T
       } catch (err) {
            this.logger.warn({key, err}, 'cache.get.failed')
            return null
       }
    }

    async setJson(key: string, value: JsonValue, ttlSeconds: number): Promise<void> {
        try {
            const payload = JSON.stringify(value)
            await this.redis.set(key, payload, 'EX', ttlSeconds)
            this.logger.debug({key, ttlSeconds}, 'cache.set')
        } catch (err) {
            this.logger.warn({key, err}, 'cache.set.failed')
        }
    }

    async del(key: string): Promise<void> {
        try{
            await this.redis.del(key)
            this.logger.debug({ key}, 'cache.del')
        } catch (err) {
            this.logger.warn({key, err}, 'cache.del.failed')
        }
    }
}