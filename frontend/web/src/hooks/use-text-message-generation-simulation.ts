import { useEffect, useRef, useState } from 'react';
import { useChatStateManager } from '@/context/chat-context';
import { type ChatEvent } from '@/data/schemas/chat-events';
import { type Thread } from '@/data/schemas/threads';
import { type UserAccessData } from '@/data/schemas/user-access';
import { evolvingAssistantTextMessage } from '@/data/tests/messages/evolving-assistant-text-message';

const userAccessData: UserAccessData = {
    access_token: 'mock-access-token',
    is_authenticated: true,
    user_id: '1',
    email: null,
    name: null,
    user_message_count: 0,
};

export function useTextMessageGenerationSimulation() {
    const chatStateManager = useChatStateManager();
    const [isRunning, setIsRunning] = useState(false);
    const [isCompleted, setIsCompleted] = useState(false);

    const currentMessageIndex = useRef(0);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    useEffect(() => {
        const thread = {
            id: '1',
            user_id: '1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            resumed_at: null,
            error_message: null,
            title: 'Test Assistant Message Thread',
            summary: null,
            is_empty: false,
        } satisfies Thread;

        setIsRunning(true);

        chatStateManager.handleChatEvent({
            event: 'text_message_started',
            data: {
                user_access_data: userAccessData,
                thread: thread,
                message: evolvingAssistantTextMessage[0],
            },
        } satisfies ChatEvent);

        // Add a delay before starting chunk generation
        timeoutRef.current = setTimeout(() => {
            intervalRef.current = setInterval(() => {
                if (currentMessageIndex.current === evolvingAssistantTextMessage.length - 1) {
                    const message = evolvingAssistantTextMessage[currentMessageIndex.current];
                    chatStateManager.handleChatEvent({
                        event: 'text_message_completed',
                        data: {
                            user_access_data: userAccessData,
                            thread: thread,
                            message: message,
                        },
                    } satisfies ChatEvent);
                    setIsCompleted(true);
                    if (intervalRef.current) {
                        clearInterval(intervalRef.current);
                    }
                    return;
                }

                chatStateManager.handleChatEvent({
                    event: 'text_message_chunk_generated',
                    data: {
                        user_access_data: userAccessData,
                        thread: thread,
                        message: evolvingAssistantTextMessage[currentMessageIndex.current],
                    },
                } satisfies ChatEvent);

                currentMessageIndex.current++;
            }, 1000);
        }, 2000);

        return () => {
            setIsRunning(false);
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
            }
        };
    }, [chatStateManager]);

    return { isRunning, isCompleted };
}
