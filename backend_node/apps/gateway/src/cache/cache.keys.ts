export const CACHE_PREFIX = 'docscan'

export type  CacheScope = 'gateway'

export function cacheKey(parts: Array<string | number>) {
    return [CACHE_PREFIX, 'gateway', ...parts].join(':')
}

export const CacheKeys = {
    notesList: () => cacheKey(['notes', 'list']),
    noteById: (id: string) => cacheKey(['notes', 'by-id', id])
}