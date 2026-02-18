import type { ThrottlerStorage } from "@nestjs/throttler";
import type Redis from "ioredis";

type StorageRecord = {
  totalHits: number;
  timeToExpire: number;
  isBlocked: boolean;
  timeToBlockExpire: number;
};

export class ThrottlerRedisStorage implements ThrottlerStorage {
  constructor(
    private readonly redis: Redis,
    private readonly prefix = "rl"
  ) {}

  private hitsKey(key: string, throttlerName: string) {
    return `${this.prefix}:${throttlerName}:${key}`;
  }

  private blockKey(key: string, throttlerName: string) {
    return `${this.prefix}:${throttlerName}:block:${key}`;
  }

  async increment(
    key: string,
    ttl: number,
    limit: number,
    blockDuration: number,
    throttlerName: string
  ): Promise<StorageRecord> {
    const hitsKey = this.hitsKey(key, throttlerName);
    const blockKey = this.blockKey(key, throttlerName);

    // 1) If blocked
    const blockTtl = await this.redis.ttl(blockKey);
    if (blockTtl > 0) {
      return {
        totalHits: limit,
        timeToExpire: 0,
        isBlocked: true,
        timeToBlockExpire: blockTtl
      };
    }

    // 2) Increment hits + ensure TTL
    const totalHits = await this.redis.incr(hitsKey);

    const currentTtl = await this.redis.ttl(hitsKey);
    if (currentTtl < 0) {
      await this.redis.expire(hitsKey, ttl);
    }

    const timeToExpire = Math.max(await this.redis.ttl(hitsKey), 0);

    // 3) Block if over limit
    if (totalHits > limit) {
      await this.redis.set(blockKey, "1", "EX", blockDuration);
      const timeToBlockExpire = Math.max(await this.redis.ttl(blockKey), 0);

      return {
        totalHits,
        timeToExpire,
        isBlocked: true,
        timeToBlockExpire
      };
    }

    return {
      totalHits,
      timeToExpire,
      isBlocked: false,
      timeToBlockExpire: 0
    };
  }
}