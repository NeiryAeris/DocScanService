import 'reflect-metadata';
import 'dotenv/config';

import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { configureApp } from './bootstrap';

async function main() {
    const app = await NestFactory.create(AppModule, { bufferLogs: true });

    await configureApp(app);

    const port = process.env.PORT ? Number(process.env.PORT) : 3000;
    await app.listen(port);
}

void main();