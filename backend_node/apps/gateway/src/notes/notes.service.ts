import { Injectable, NotFoundException } from "@nestjs/common";
import { NotesRepository } from "./notes.repository";

@Injectable()
export class NotesService {
    constructor(private readonly repo: NotesRepository) {}

    async create(input: {title: string; content?: string}) {
        return this.repo.create(input)
    }

    async list(){
        return this.repo.findMany()
    }

    async get(id: string) {
        const note = await this.repo.findById(id)
        if (!note) throw new NotFoundException("Note Not Found")
        return note
    }

    async update(id: string, input: {title?: string, content?: string}) {
        await this.get(id)
        return this.repo.update(id, input)
    }

    async remove(id: string) {
        await this.get(id)
        return this.repo.delete(id)
    }
}