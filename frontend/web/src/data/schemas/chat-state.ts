import { z } from 'zod';
import { ThreadSchema } from './threads';

export const ChatStateSchema = z.object({
    isReady: z.boolean(),
    thread: ThreadSchema.nullable(),
    threadState: z.enum(['started', 'resumed']).nullable(),
    hasMoreMessages: z.boolean(),
    nextMessageTimestamp: z.string().nullable(), // TODO: Better name?
    isAssistantThinking: z.boolean(),
    isAssistantResponding: z.boolean(),
});
export type ChatState = z.infer<typeof ChatStateSchema>;
