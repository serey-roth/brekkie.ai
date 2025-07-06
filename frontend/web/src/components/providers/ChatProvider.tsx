import { useCallback, useRef } from 'react';
import { useUserAccessManager } from '@/context/app-context';
import { ChatContext } from '@/context/chat-context';
import { useChatWebSocket } from '@/hooks/use-chat-websocket';
import { ChatStateManager } from '@/managers/chat-state-manager';
import { ConnectionStateManager } from '@/managers/connection-state-manager';
import { MessageManager } from '@/managers/message-manager';
import { RecipeManager } from '@/managers/recipe-manager';

export function ChatProvider({ children }: { children: React.ReactNode }) {
    const userAccessManager = useUserAccessManager();
    const messageManager = useRef(new MessageManager());
    const recipeManagerRef = useRef(new RecipeManager());
    const connectionStateManager = useRef(new ConnectionStateManager());
    const chatStateManagerRef = useRef(
        new ChatStateManager(messageManager.current, recipeManagerRef.current),
    );

    const { sendMessage: sendMessageToAssistant } = useChatWebSocket({
        userAccessManager,
        chatStateManager: chatStateManagerRef.current,
        connectionStateManager: connectionStateManager.current,
    });

    const sendMessage = useCallback(
        (content: string) => {
            const cleanedContent = content.trim();
            if (cleanedContent.length === 0) {
                return;
            }
            sendMessageToAssistant(cleanedContent);
        },
        [sendMessageToAssistant],
    );

    return (
        <ChatContext.Provider
            value={{
                chatStateManager: chatStateManagerRef.current,
                connectionStateManager: connectionStateManager.current,
                messageManager: messageManager.current,
                recipeManager: recipeManagerRef.current,
                sendMessage,
            }}
        >
            {children}
        </ChatContext.Provider>
    );
}
