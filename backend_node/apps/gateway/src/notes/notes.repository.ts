import { Injectable } from "@nestjs/common";
import { PrismaService } from "../prisma/prisma.service";

@Injectable()
export class NotesRepository {
  constructor(private readonly prisma: PrismaService) {}

  create(data: { title: string; content?: string }) {
    return this.prisma.note.create({ data });
  }

  findMany() {
    return this.prisma.note.findMany({ orderBy: { createdAt: "desc" } });
  }

  findById(id: string) {
    return this.prisma.note.findUnique({ where: { id } });
  }

  update(id: string, data: { title?: string; content?: string }) {
    return this.prisma.note.update({ where: { id }, data });
  }

  delete(id: string) {
    return this.prisma.note.delete({ where: { id } });
  }
}