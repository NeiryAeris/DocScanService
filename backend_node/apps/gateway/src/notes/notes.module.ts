import { Module } from "@nestjs/common";
import { NoteController } from "./notes.controller";
import { NotesRepository } from "./notes.repository";
import { NotesService } from "./notes.service";

@Module({
    controllers: [NoteController],
    providers: [NotesRepository, NotesService]
})

export class NotesModule {}