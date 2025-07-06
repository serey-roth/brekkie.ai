import { z } from 'zod';

export const ConnectionStatusSchema = z.enum([
    'connecting',
    'connected',
    'reconnecting',
    'disconnecting',
    'disconnected',
    'idle',
    'error',
]);
export type ConnectionStatus = z.infer<typeof ConnectionStatusSchema>;

export const ConnectionStateSchema = z.object({
    isConnecting: z.boolean(),
    isConnected: z.boolean(),
    isReconnecting: z.boolean(),
    errorMessage: z.string().nullable(),
    status: ConnectionStatusSchema,
    reconnectAttempts: z.number().default(0),
});

export type ConnectionState = z.infer<typeof ConnectionStateSchema>;
