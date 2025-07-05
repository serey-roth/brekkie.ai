import { AnimatePresence, motion } from 'framer-motion';
import { FaCircleExclamation } from 'react-icons/fa6';
import { LuLoader } from 'react-icons/lu';
import { ChatMessageGroup } from '@/components/chat/MessageGroup';
import type { RoleMessageGroup } from '@/data/schemas/messages';

interface MessageTurnListProps {
    messageGroups: RoleMessageGroup[];
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
    isLoadingMoreMessages: boolean;
    loadingMessage: string | null;
    errorLoadingMoreMessages: string | null;
}

export function MessageTurnList({
    messageGroups,
    isAssistantThinking,
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe,
    isLoadingMoreMessages,
    loadingMessage,
    errorLoadingMoreMessages,
}: MessageTurnListProps) {
    return (
        <AnimatePresence mode="popLayout">
            <motion.div
                initial={false}
                animate={{ height: isLoadingMoreMessages || errorLoadingMoreMessages ? 48 : 0 }}
                transition={{ duration: 0.2, ease: "easeOut" }}
            >
                {isLoadingMoreMessages && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="flex h-12 items-center justify-center gap-2 text-sm text-contrast-subtle"
                    >
                        <LuLoader className="w-4 h-4 animate-spin" />
                        <span>{loadingMessage}</span>
                    </motion.div>
                )}
                {errorLoadingMoreMessages && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.15 }}
                        className="flex h-12 items-center justify-center gap-2 text-sm text-contrast-subtle"
                    >
                        <FaCircleExclamation className="w-4 h-4 text-red-500" />
                        <span>{errorLoadingMoreMessages}</span>
                    </motion.div>
                )}
            </motion.div>
            {messageGroups.map((group, idx) => (
                <ChatMessageGroup
                    key={idx}
                    group={group}
                    isAssistantThinking={isAssistantThinking}
                    isAssistantResponding={isAssistantResponding}
                    selectedRecipeId={selectedRecipeId}
                    onSelectRecipe={onSelectRecipe}
                />
            ))}
        </AnimatePresence>
    );
} 