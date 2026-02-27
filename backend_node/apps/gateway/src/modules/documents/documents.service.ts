import { Injectable, NotFoundException } from "@nestjs/common";
import { CreateDocumentDto, UpdateDocumentDto } from "./document.dto";
import { filter } from "rxjs";
import { Doc } from "zod/v4/core";

export type DocumentEntity = {
  id: string;
  title: string;
  content?: string;
  createdAt: string;
  updatedAt: string;
};

@Injectable()
export class DocumentsService {
  // replace this with prisma later
  private readonly store = new Map<string, DocumentEntity>();

  async list(params: { q?: string; limit?: number; offset?: number }) {
    const { q, limit = 50, offset = 0 } = params;

    const all = Array.from(this.store.values());

    const filtered = q
      ? all.filter((d) => {
          const hay = `${d.title} ${d.content ?? ""}`.toLowerCase();
          return hay.includes(q.toLowerCase());
        })
      : all;

    const items = filtered.slice(offset, offset + limit);

    return {
      items,
      total: filtered.length,
      limit,
      offset,
    };
  }

  async getById(id: string) {
    const found = this.store.get(id)
    if (!found) {
        throw new NotFoundException(`Document not found: ${id}`)
    }
    return found
  }

  async create(dto: DocumentEntity) {
    const now = new Date().toISOString()
    const id = cryptoRandomId()

    const doc: DocumentEntity = {
        id,
        title: dto.title,
        content: dto.content ?? 'null',
        createdAt: now,
        updatedAt: now
    }

    this.store.set(id, doc)
    return doc
  }

  async update(id: string, dto: UpdateDocumentDto) {
    const found  = this.store.get(id)
    if(!found) {
        throw new NotFoundException(`Document not found: ${id}`)
    }

    const updated: DocumentEntity = {
        ...found,
        title: dto.title ?? found.title,
        content: dto.content !== undefined ? dto.content: found.content,
        updatedAt: new Date().toISOString()
    }
    
    this.store.set(id, updated)
    return updated
  }


  async remove(id: string) {
    const found = this.store.get(id)
    if (!found) {
        throw new NotFoundException(`Document not found: ${id}`)
    }
        this.store.delete(id)
        return {
            ok: true, id
        }
    }

    
  }

  function cryptoRandomId(): string {
    const c: any = globalThis.crypto
    if(c?.getRandomValue) {
      const bytes = new Uint8Array(16)
      return Array.from(bytes)
        .map((b) => {b.toString(16).padStart(2,'0')})
        .join('')
    }
    return Math.random().toString(16).slice(2) + Date.now().toString(16)
  }
