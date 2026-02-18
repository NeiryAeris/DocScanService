import { Body, Controller, Delete, Get, Param, Patch, Post } from "@nestjs/common";
import { ApiTags } from "@nestjs/swagger";
import { CreateNodeDto } from "./dto/create-note.dto";
import { UpdateNoteDto } from "./dto/update-note.dto";
import { NotesService } from "./notes.service";

@ApiTags('notes')
@Controller('/notes')
export class NoteController {
    constructor(private readonly notes: NotesService) {}

    @Post()
    create(@Body() dto: CreateNodeDto) {
        return this.notes.create(dto)
    }

    @Get()
    list() {
        return this.notes.list()
    }

    @Get(':id')
    get(@Param('id') id: string) {
        return this.notes.get(id)
    }

    @Patch(':id')
    update(@Param('id') id: string, @Body() dto: UpdateNoteDto) {
        return this.notes.update(id, dto)
    }

    @Delete(':id')
    remove(@Param('id') id: string) {
        return this.notes.remove(id)
    }
}