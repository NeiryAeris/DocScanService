import express, {Application} from 'express';
import cor from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import {router as apiRouter} from './routes';
import { errorHandler } from './middlewares/error.middleware';

export const createApp = (): Application => {
    const app = express();

    // Middlewares
    app.use(helmet());
    app.use(cor());
    app.use(express.json({limit : "10mb"}));
    app.use(express.urlencoded({ extended: true }));
    app.use(morgan('dev'));

    //routes
    app.use('/api', apiRouter);

    // heath root
    app.get("/", (req, res) => {
        res.status(200).send("DocScan Service is running...");
        res.json({ status: "OK", message: "DocScan Service Gateway is running" });
    })

    // error handler
    app.use(errorHandler);

    return app;
}