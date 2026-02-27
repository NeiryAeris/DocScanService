import { ApiPropertyOptional, ApiProperty, ApiResponseProperty } from "@nestjs/swagger";
import { IsOptional, IsString, Max, MaxLength } from "class-validator";

export class CreateDocumentDto {
    @ApiProperty({example: 'Doc Title'})
    @IsString()
    @MaxLength(200)
    title!: string

    @ApiPropertyOptional({example: 'idk, some content'})
    @IsOptional()
    @IsString()
    content?: string
}

export class UpdateDocumentDto {
    @ApiPropertyOptional({example: 'updated title maybe'})
    @IsOptional()
    @IsString()
    @MaxLength(200)
    title?: string

    @ApiPropertyOptional({example: 'updated content (dummy content)'})
    @IsOptional()
    @IsString()
    content?: string 
}