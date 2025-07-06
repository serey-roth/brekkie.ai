import { z } from 'zod';

export const ThreadSchema = z.object({
    id: z.string(),
    user_id: z.string(),
    created_at: z.string(),
    updated_at: z.string(),
    resumed_at: z.string().nullable(),
    error_message: z.string().nullable(),
    title: z.string().nullable(),
    summary: z.string().nullable(),
    is_empty: z.boolean(),
});
export type Thread = z.infer<typeof ThreadSchema>;

export const PaginatedThreadsSchema = z.object({
    threads: z.array(ThreadSchema),
    total_count: z.number(),
    has_more: z.boolean(),
    next_timestamp: z.string().nullable(),
});
export type PaginatedThreads = z.infer<typeof PaginatedThreadsSchema>;

export const GetUserThreadsPayloadSchema = z.object({
    limit: z.number().min(1).max(100).optional().default(10),
    sort_by: z.enum(['created_at', 'updated_at']).optional().default('updated_at'),
    sort_order: z.enum(['asc', 'desc']).optional().default('desc'),
    from_timestamp: z.string().nullable().optional(),
    exclude_empty: z.boolean().optional().default(true),
});
export type GetUserThreadsPayload = z.infer<typeof GetUserThreadsPayloadSchema>;
