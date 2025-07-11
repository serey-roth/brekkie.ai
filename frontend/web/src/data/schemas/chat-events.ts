import { z } from 'zod';
import { AiAgentErrorSchema, ChatSessionErrorSchema } from './errors';
import { MessageSchema, PaginatedMessagesSchema } from './messages';
import { UserRecipeSchema } from './recipes';
import { ThreadSchema } from './threads';
import { UserAccessDataSchema } from './user-access';

export const ChatEventSchema = z.discriminatedUnion('event', [
    z.object({
        event: z.literal('thread_started'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
        }),
    }),
    z.object({
        event: z.literal('thread_resumed'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            paginated_messages: PaginatedMessagesSchema,
            recipes: z.array(UserRecipeSchema),
        }),
    }),
    z.object({
        event: z.literal('text_message_started'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
    z.object({
        event: z.literal('text_message_chunk_generated'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
    z.object({
        event: z.literal('text_message_completed'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
    z.object({
        event: z.literal('recipe_generation_started'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
            recipe: UserRecipeSchema,
        }),
    }),
    z.object({
        event: z.literal('recipe_field_detected'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
            recipe: UserRecipeSchema,
        }),
    }),
    z.object({
        event: z.literal('recipe_generation_completed'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
            recipe: UserRecipeSchema,
        }),
    }),
    z.object({
        event: z.literal('search_started'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
    z.object({
        event: z.literal('search_completed'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
    z.object({
        event: z.literal('summary_updated'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
        }),
    }),
    z.object({
        event: z.literal('thread_title_updated'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
        }),
    }),
    z.object({
        event: z.literal('ai_agent_error'),
        data: z
            .object({
                user_access_data: UserAccessDataSchema,
                thread: ThreadSchema,
            })
            .extend(AiAgentErrorSchema.shape),
    }),
    z.object({
        event: z.literal('chat_session_error'),
        data: ChatSessionErrorSchema,
    }),
    z.object({
        event: z.literal('user_message_rejected'),
        data: z.object({
            user_access_data: UserAccessDataSchema,
            thread: ThreadSchema,
            message: MessageSchema,
        }),
    }),
]);
export type ChatEvent = z.infer<typeof ChatEventSchema>;
