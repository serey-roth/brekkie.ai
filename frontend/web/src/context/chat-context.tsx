import { createContext, useContext } from 'react';
import { ChatStateManager } from '@/managers/chat-state-manager';
import { ConnectionStateManager } from '@/managers/connection-state-manager';
import { MessageManager } from '@/managers/message-manager';
import { RecipeManager } from '@/managers/recipe-manager';

export type ChatContextType = {
    connectionStateManager: ConnectionStateManager;
    chatStateManager: ChatStateManager;
    recipeManager: RecipeManager; // TODO: Should we expose this through the chat state manager?
    messageManager: MessageManager;
    sendMessage: (content: string) => void;
};

export const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChatContext = () => {
    const ctx = useContext(ChatContext);
    if (!ctx) throw new Error('useChat must be used within a ChatProvider');
    return ctx;
};

export const useChatStateManager = () => {
    const ctx = useChatContext();
    return ctx.chatStateManager;
};

export const useConnectionStateManager = () => {
    const ctx = useChatContext();
    return ctx.connectionStateManager;
};

export const useRecipeManager = () => {
    const ctx = useChatContext();
    return ctx.recipeManager;
};

export const useMessageManager = () => {
    const ctx = useChatContext();
    return ctx.messageManager;
};
