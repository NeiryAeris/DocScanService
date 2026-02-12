import {
    ArgumentsHost,
    Catch,
    ExceptionFilter,
    HttpException,
    HttpStatus
} from '@nestjs/common';
import { raw, request } from 'express';
import { timestamp } from 'rxjs';

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
    catch(exception: unknown, host: ArgumentsHost) {
        const ctx = host.switchToHttp();
        const req = ctx.getRequest<Request & { id?: string }>();
        const res = ctx.getResponse<any>();

        const requestId = 
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (req as any).id ??
        (req.headers as any)?.['x-request-id'] ?? undefined;

        const isHttp = exception instanceof HttpException;

        const statusCode = isHttp
            ? exception.getStatus()
            : HttpStatus.INTERNAL_SERVER_ERROR;

        const rawResponse = isHttp ? exception.getResponse() : undefined;

        const message = 
        typeof rawResponse === 'string'
            ? rawResponse
            : // Nest often puts validation messages in { message: [...] }
            (rawResponse as any)?.message ??
            (exception as any)?.message ?? 
            'internal server error';

        const details = 
        typeof rawResponse === 'object' && rawResponse !== null
            ? rawResponse
            : undefined;

        const payload = {
            requestId,
            timestamp: new Date().toISOString(),
            path: (req as any).url,
            method: (req as any).method,
            statusCode,
            error: {
                name: isHttp ? exception.name : 'InternalServerError',
                message,
                details
            }
        }
        res.status(statusCode).json(payload);
    }
}