import { AnimatePresence, motion } from 'framer-motion';
import { CircleAlert, Loader } from 'lucide-react';
import { ChatMessageGroup, AssistantThinkingMessageBubble } from '@/components/chat/MessageGroup';
import type { RoleMessageGroup } from '@/data/schemas/messages';

interface MessageListProps {
    messageGroups: RoleMessageGroup[];
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
    isLoadingMoreMessages: boolean;
    loadingMessage: string | null;
    errorLoadingMoreMessages: string | null;
}

export function MessageList({
    messageGroups,
    isAssistantThinking,
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe,
    isLoadingMoreMessages,
    loadingMessage,
    errorLoadingMoreMessages,
}: MessageListProps) {
    return (
        <AnimatePresence mode="popLayout">
            <motion.div
                initial={false}
                animate={{ height: isLoadingMoreMessages || errorLoadingMoreMessages ? 48 : 0 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
            >
                {isLoadingMoreMessages && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="text-contrast-subtle flex h-12 items-center justify-center gap-2 text-sm"
                    >
                        <Loader className="h-4 w-4 animate-spin" />
                        <span>{loadingMessage}</span>
                    </motion.div>
                )}
                {errorLoadingMoreMessages && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="text-contrast-subtle flex h-12 items-center justify-center gap-2 text-sm"
                    >
                        <CircleAlert className="h-4 w-4 text-red-500" />
                        <span>{errorLoadingMoreMessages}</span>
                    </motion.div>
                )}
            </motion.div>
            {messageGroups.map((group, idx) => (
                <ChatMessageGroup
                    key={idx}
                    group={group}
                    isAssistantResponding={
                        idx === messageGroups.length - 1 && isAssistantResponding
                    }
                    selectedRecipeId={selectedRecipeId}
                    onSelectRecipe={onSelectRecipe}
                />
            ))}
            {isAssistantThinking && <AssistantThinkingMessageBubble />}
        </AnimatePresence>
    );
}
