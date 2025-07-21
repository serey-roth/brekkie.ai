import { useEffect } from 'react';
import { useUserAccessManager } from '@/context/app-context';
import { useChatStateManager } from '@/context/chat-context';
import type { ChatEvent } from '@/data/schemas/chat-events';
import type { UserAccess } from '@/data/schemas/user-access';
import { useTextMessageGenerationSimulation } from './use-text-message-generation-simulation';

export function useOverMessageLimitSimulation() {
    const userAccessManager = useUserAccessManager();
    const chatStateManager = useChatStateManager();

    const { isCompleted } = useTextMessageGenerationSimulation();

    useEffect(() => {
        if (!isCompleted) return;

        userAccessManager.setUserAccess({
            access_token: '123',
            user_id: '1',
            is_authenticated: false,
            user_message_count: 11,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
        } satisfies UserAccess);

        chatStateManager.handleChatEvent({
            event: 'chat_session_error',
            data: {
                code: 429,
                message: "You've reached the message limit",
                type: 'over_message_limit',
            },
        } satisfies ChatEvent);
    }, [chatStateManager, userAccessManager, isCompleted]);
}
