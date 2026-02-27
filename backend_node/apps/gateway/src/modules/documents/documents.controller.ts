import { Controller, Get } from "@nestjs/common";

@Controller('documents')
export class DocumentsController {
    @Get(':id')
    getById(@Param('id'), id: string) {
        return this.documentsService.getById(id)
    }
}