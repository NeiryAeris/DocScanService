import { Injectable, NotFoundException } from "@nestjs/common";
import { NotesRepository } from "./notes.repository";
import { CacheService } from "../cache/cache.service";
import { CacheKeys } from "../cache/cache.keys";

@Injectable()
export class NotesService {
    constructor(private readonly repo: NotesRepository, private readonly cache: CacheService) {}

    async create(input: {title: string; content?: string}) {
        const created = await this.repo.create(input)

        await this.cache.del(CacheKeys.notesList())
        return created
    }

    async list(){
        const key = CacheKeys.notesList()

        const cached = await this.cache.getJson<unknown[]>(key)
        if (cached) return cached

        const notes = await this.repo.findMany()
        await this.cache.setJson(key,notes, 30)

        return notes
    }

    async get(id: string) {
        const note = await this.repo.findById(id)
        if (!note) throw new NotFoundException("Note Not Found")
        return note
    }

    async update(id: string, input: {title?: string, content?: string}) {
        await this.get(id)
        const updated = this.repo.update(id, input)
        await this.cache.del(CacheKeys.notesList())

        return updated
    }

    async remove(id: string) {
        await this.get(id)
        const removed = this.repo.delete(id)
        await this.cache.del(CacheKeys.notesList())

        return removed
    }
}