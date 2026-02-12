import 'reflect-metadata';
import 'dotenv/config';

import express from 'express';
import { NestFactory } from '@nestjs/core';
import { ExpressAdapter } from '@nestjs/platform-express';  

import { AppModule } from './app.module';
import { configureApp } from './bootstrap';

let cacheHandler: ((req: any, res: any) => any) | null = null;
let bootPromise: Promise<(req: any, res: any) => any> | null = null;

async function bootstrapVercelHandler() {
    const expressInstance  = express();
    const adapter = new ExpressAdapter(expressInstance);

    const nestApp = await NestFactory.create(AppModule, adapter, { bufferLogs: true }); 
    
    await configureApp(nestApp);
    await nestApp.init();

    return ((req: any, res: any) =>  expressInstance(req, res));
}

export default async function handler(req: any, res: any) {
    if (cacheHandler) return cacheHandler(req, res);

    if (!bootPromise) bootPromise = bootstrapVercelHandler();
    cacheHandler = await bootPromise;

    return cacheHandler(req, res);
}