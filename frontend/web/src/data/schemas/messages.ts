import { z } from 'zod';
import { UserRecipeSchema } from './recipes';

export const MessageRoleSchema = z.enum(['user', 'assistant']);
export type MessageRole = z.infer<typeof MessageRoleSchema>;

export const MessageContentTypeSchema = z.enum(['text', 'recipe', 'tool']);
export type MessageContentType = z.infer<typeof MessageContentTypeSchema>;

export const MessageSchema = z.object({
    id: z.string(),
    thread_id: z.string(),
    role: MessageRoleSchema,
    content_type: MessageContentTypeSchema,
    created_at: z.string(),
    updated_at: z.string(),
    parent_id: z.string().nullable(),
    text_content: z.string().nullable(),
    recipe_id: z.string().nullable(),
    model_name: z.string().nullable(),
    input_tokens: z.number().nullable(),
    output_tokens: z.number().nullable(),
    tool_name: z.string().nullable(),
    tool_input: z.record(z.string(), z.unknown()).nullable(),
    tool_output: z.record(z.string(), z.unknown()).nullable(),
    is_recipe_generation_started: z.boolean().nullable(),
    is_recipe_generation_completed: z.boolean().nullable(),
});
export type Message = z.infer<typeof MessageSchema>;

export type UserMessage = Message & { role: 'user'; text_content: string; content_type: 'text' };

export type AssistantMessage = Message & { role: 'assistant'; parent_id: string };
export type AssistantTextMessage = AssistantMessage & {
    content_type: 'text';
    text_content: string;
};
export type AssistantRecipeMessage = AssistantMessage & {
    content_type: 'recipe';
    recipe_id: string;
    is_recipe_generation_started: boolean;
    is_recipe_generation_completed: boolean;
};
export type AssistantToolMessage = AssistantMessage & {
    content_type: 'tool';
    tool_name: string;
    tool_input: Record<string, unknown>;
    tool_output: Record<string, unknown>;
};

export type RoleMessageGroup =
    | {
          role: 'user';
          messages: UserMessage[];
      }
    | {
          role: 'assistant';
          messages: AssistantMessage[];
      };

export const UserMessagePayloadSchema = z.object({
    id: z.string(),
    content: z.string(),
});
export type UserMessagePayload = z.infer<typeof UserMessagePayloadSchema>;

export const PaginatedMessagesSchema = z.object({
    messages: z.array(MessageSchema),
    total_count: z.number(),
    has_more: z.boolean(),
    next_timestamp: z.string().nullable(),
});
export type PaginatedMessages = z.infer<typeof PaginatedMessagesSchema>;

export const GetThreadMessagesPayloadSchema = z.object({
    thread_id: z.string(),
    limit: z.number().min(1).max(100).optional().default(10),
    sort_by: z.enum(['created_at', 'updated_at']).optional().default('created_at'),
    sort_order: z.enum(['asc', 'desc']).optional().default('desc'),
    from_timestamp: z.string().nullable().optional(),
});
export type GetThreadMessagesPayload = z.infer<typeof GetThreadMessagesPayloadSchema>;
export const GetThreadMessagesResponseSchema = z.object({
    paginated_messages: PaginatedMessagesSchema,
    recipes: z.array(UserRecipeSchema),
});
export type GetThreadMessagesResponse = z.infer<typeof GetThreadMessagesResponseSchema>;
