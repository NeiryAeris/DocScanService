import 'reflect-metadata';
import 'dotenv/config';

import helmet from 'helmet';
import cors from 'cors'
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { configureApp } from './bootstrap';

function parseCorsOrigin(value?: string) {
    return (value ?? '')
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean)
}

async function main() {
    const app = await NestFactory.create(AppModule, { bufferLogs: true });

    app.use(helmet())

    const allowlist = parseCorsOrigin(process.env.CORS_ORIGINS) 
    app.use(
        cors({
            origin: (origin, cb) => {
                if (!origin) return cb(null,true)
                if (allowlist.includes(origin)) return cb(null,true)
                return cb(new Error(`CORS blocked origin: ${origin}`))
            },
            credentials: true
        })
    )

    await configureApp(app);

    const port = process.env.PORT ? Number(process.env.PORT) : 3000;
    await app.listen(port);
}

void main(); 