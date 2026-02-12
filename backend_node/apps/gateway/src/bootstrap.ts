import { INestApplication, ValidationPipe } from '@nestjs/common';
import { DocumentBuilder , SwaggerModule } from '@nestjs/swagger';
import { Logger } from 'nestjs-pino';
import type { Express, RequestHandler } from "express";

import { AllExceptionsFilter } from './common/filters/all-exceptions.filter'

// function loadLegacyMiddleware(): RequestHandler {
//   // Support multiple export styles from ./app.ts
//   // eslint-disable-next-line @typescript-eslint/no-var-requires
//   const mod = require("./app");

//   const candidate = mod?.default ?? mod?.app ?? mod;

//   if (typeof candidate !== "function") {
//     const keys =
//       mod && typeof mod === "object" && !Array.isArray(mod) ? Object.keys(mod) : [];
//     throw new Error(
//       `Legacy express app export is not a middleware function. ` +
//         `Expected src/app.ts to export: default OR named export { app }. ` +
//         `Got type="${typeof candidate}". Module keys=[${keys.join(", ")}]`
//     );
//   }

//   return candidate as RequestHandler;
// }

import legacyApp from './app'

export async function configureApp(app: INestApplication) {
    //Logger everywhere
    app.useLogger(app.get(Logger));

    //Global validation
    app.useGlobalPipes(
        new ValidationPipe({
            whitelist: true,
            forbidNonWhitelisted: true,
            transform: true,
        })
    );

    //Global error format
    app.useGlobalFilters(new AllExceptionsFilter());

    //Swagger only in dev
    if (process.env.NODE_ENV !== 'production') {
        const config = new DocumentBuilder()
        .setTitle('Gateway API')
        .setDescription('The Gateway API description')
        .setVersion('0.1.0')
        .build();

        const doc = SwaggerModule.createDocument(app, config);
        SwaggerModule.setup('docs', app, doc);
    }

    //Legacy express app
    const httpAdapter = app.getHttpAdapter();
    const expressInstance = httpAdapter.getInstance() as Express;
    
    // const legacy = loadLegacyMiddleware()
    expressInstance.use(legacyApp);

    return app
}