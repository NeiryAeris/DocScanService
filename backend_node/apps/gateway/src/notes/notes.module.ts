import { Module } from "@nestjs/common";
import { NoteController } from "./notes.controller";
import { NotesRepository } from "./notes.repository";
import { NotesService } from "./notes.service";
import { CacheModule } from "../cache/cache.module";

@Module({
    imports: [CacheModule],
    controllers: [NoteController],
    providers: [NotesRepository, NotesService]
})

export class NotesModule {}