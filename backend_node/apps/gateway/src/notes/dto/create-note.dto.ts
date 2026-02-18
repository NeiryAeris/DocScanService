import { IsOptional, IsString, MaxLength } from "class-validator";

export class CreateNodeDto {
    @IsString()
    @MaxLength(200)
    title!: string;

    @IsOptional()
    @IsString()
    content?: string;
}