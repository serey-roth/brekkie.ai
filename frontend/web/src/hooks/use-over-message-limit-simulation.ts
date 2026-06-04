import { useEffect } from 'react';
import { useChatStateManager } from '@/context/chat-context';
import type { ChatEvent } from '@/data/schemas/chat-events';
import { useTextMessageGenerationSimulation } from './use-text-message-generation-simulation';

export function useOverMessageLimitSimulation() {
    const chatStateManager = useChatStateManager();

    const { isCompleted } = useTextMessageGenerationSimulation();

    useEffect(() => {
        if (!isCompleted) return;

        chatStateManager.handleChatEvent({
            event: 'chat_session_error',
            data: {
                code: 429,
                message: "You've reached the message limit",
                type: 'over_message_limit',
            },
        } satisfies ChatEvent);
    }, [chatStateManager, isCompleted]);
}
