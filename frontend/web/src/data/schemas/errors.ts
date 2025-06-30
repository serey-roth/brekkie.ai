import { z } from 'zod';

// TODO: Maybe get rid of this?
export const ApiErrorSchema = z.object({
    detail: z.object({
        message: z.string(),
    }),
});
export type ApiError = z.infer<typeof ApiErrorSchema>; 

export const ChatSessionErrorTypeSchema = z.enum([
    'access_token_not_found', 
    'access_token_expired', 
    'invalid_access_token', 
    'over_message_limit', 
    'thread_not_found', 
    'internal_server_error',
    'invalid_payload',
    'session_closed',
    'custom_error',
]);
export const ChatSessionErrorTypes = ChatSessionErrorTypeSchema.options;
export const ChatSessionErrorTypesThatDontRequireReconnect: readonly string[] = [
    'access_token_not_found',
    'access_token_expired',
    'invalid_access_token',
    'over_message_limit',
    'thread_not_found',
    'internal_server_error',
];

export const ChatSessionErrorSchema = z.object({
    code: z.number(),
    type: ChatSessionErrorTypeSchema,
    message: z.string(),
});
export type ChatSessionError = z.infer<typeof ChatSessionErrorSchema>;

export const AiAgentErrorSchema = z.object({
    error_message: z.string(),
});
export type AiAgentError = z.infer<typeof AiAgentErrorSchema>;

export const ChatLimitMessageSchema = z.object({
    type: z.enum(['warning', 'error']),
    message: z.string(),
});
export type ChatLimitMessage = z.infer<typeof ChatLimitMessageSchema>;