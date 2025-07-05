import { motion } from 'framer-motion';
import { DateTime } from 'luxon';
import { LuUser, LuBot, LuClock } from 'react-icons/lu';
import { RecipeMessageCard } from '@/components/recipes/RecipeMessageCard';
import { Markdown } from '@/components/ui/Markdown';
import type { AssistantMessage, RoleMessageGroup, UserMessage } from '@/data/schemas/messages';
import { isAssistantMessage, isAssistantRecipeMessage } from '@/utils/message-utils';

interface ChatMessageGroupProps {
    group: RoleMessageGroup;
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}

function AssistantMessageContent({ 
    message
}: { 
    message: AssistantMessage; 
}) {
    // TODO: Future enhancement - Add typing effect with progressive markdown rendering
    // Consider implementing a custom typing animation that works well with markdown elements
    // like lists, headers, and code blocks without breaking the visual flow
    
    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ 
                type: "tween",
                duration: 0.5, 
                ease: "easeInOut" 
            }}
        >
            <Markdown>{message.text_content ?? ''}</Markdown>
        </motion.div>
    );
}

function UserMessageBubble({ message }: { message: UserMessage }) {
    return (
        <div className="flex w-full gap-3 sm:gap-2 items-end justify-end">
            <div className="flex flex-col flex-shrink-0 gap-1 max-w-10/12 min-w-8/12">
                <div className="bg-primary text-white py-3 rounded-2xl px-4 text-sm leading-relaxed sm:text-base">
                    <div className="flex items-center justify-between mb-2 text-white/90">
                        <div className="flex items-center gap-2">
                            <div className="flex-shrink-0">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full sm:h-8 sm:w-8 bg-white/20">
                                    <LuUser size={18} className="text-white" />
                                </div>
                            </div>
                            <span className="text-base font-medium">
                                You
                            </span>
                        </div>
                        
                        <div className="flex items-center gap-2 text-xs sm:text-sm opacity-80">
                            <div className="flex items-center gap-1 text-white/90">
                                <LuClock size={12} />
                                <span>
                                    {DateTime.fromISO(message.created_at).toLocaleString(DateTime.DATETIME_SHORT)}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="prose prose-base dark:prose-invert max-w-none">
                        <p className="whitespace-pre-wrap">{message.text_content}</p>
                    </div>
                </div>
            </div>
        </div>
    );
}

function UserMessageGroup({ messages }: { messages: UserMessage[] }) {
    return (
        <div className="flex w-full gap-3 sm:gap-2 items-start justify-start">
            <div className="flex flex-col flex-shrink-0 w-full">
                {messages.map((msg) => <UserMessageBubble key={msg.id} message={msg} />)}
            </div>
        </div>
    );
}

function AssistantMessageBubble({ 
    message, 
    isFirst, 
    isLast, 
    isAssistantThinking, 
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe 
}: { 
    message: AssistantMessage;
    isFirst: boolean;
    isLast: boolean;
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}) {
    const bubbleClasses = `bg-white text-contrast-subtle 
        ${
            isFirst && isLast ? 'rounded-2xl' : isFirst ? 'rounded-t-2xl' : isLast ? 'rounded-b-2xl' : ''
        }
        ${
              isFirst && isLast ? 'py-3' : isFirst ? 'pt-3' : isLast ? 'pb-3' : 'py-3'
          }`;

    return (
        <div className={`px-4 text-sm leading-relaxed sm:text-base ${bubbleClasses}`}>
            {isFirst && (
                <div className="flex items-center justify-between mb-2 text-contrast-subtle">
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full sm:h-8 sm:w-8 bg-primary/10 border-primary/20 border">
                                <LuBot size={18} className="text-primary" />
                            </div>
                        </div>
                        
                        <motion.div
                            key={isAssistantThinking || isAssistantResponding ? 'active' : 'finished'}
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.15 }}
                        >
                            {isAssistantThinking || isAssistantResponding ? (
                                <div className="flex items-center gap-1">
                                    <span className="text-base font-medium text-primary/70">
                                        Milo is {isAssistantThinking ? 'thinking' : 'typing'} 
                                    </span>
                                    <div className="flex items-center gap-1 mt-2">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                className="bg-primary/40 h-1 w-1 rounded-full"
                                                animate={{
                                                    y: [0, -4, 0],
                                                    opacity: [0.5, 1, 0.5]
                                                }}
                                                transition={{
                                                    duration: 0.6,
                                                    repeat: Infinity,
                                                    delay: i * 0.2,
                                                    ease: "easeInOut"
                                                }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <span className="text-base font-medium">
                                    Milo
                                </span>
                            )}
                        </motion.div>
                    </div>
                    
                    <div className="flex items-center gap-2 text-xs sm:text-sm opacity-80">
                        <div className="flex items-center gap-1 text-contrast-subtle/90">
                            <LuClock size={12} />
                            <span>
                                {DateTime.fromISO(message.created_at).toLocaleString(DateTime.DATETIME_SHORT)}
                            </span>
                        </div>
                    </div>
                </div>
            )}

            <div className="prose prose-base dark:prose-invert max-w-none">
                {isAssistantMessage(message) ? (
                    isAssistantRecipeMessage(message) ? (
                        <RecipeMessageCard
                            recipeId={message.recipe_id}
                            isGenerating={message.is_recipe_generation_started ?? false}
                            onSelectRecipe={onSelectRecipe}
                            selectedRecipeId={selectedRecipeId}
                        />
                    ) : message.text_content ? (
                        <AssistantMessageContent message={message} />
                    ) : null
                ) : null}
            </div>
        </div>
    );
}

function ThinkingMessageBubble({ 
    isAssistantThinking, 
    isAssistantResponding
}: { 
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
}) {
    return (
        <div className="flex w-full gap-3 sm:gap-2 items-start justify-start">
            <div className="flex flex-col flex-shrink-0 w-full">
                <div className="bg-white text-contrast-subtle py-3 rounded-2xl px-4 text-sm leading-relaxed sm:text-base">
                    <div className="flex items-center justify-between mb-2 text-contrast-subtle">
                        <div className="flex items-center gap-2">
                            <div className="flex-shrink-0">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full sm:h-8 sm:w-8 bg-primary/10 border-primary/20 border">
                                    <LuBot size={18} className="text-primary" />
                                </div>
                            </div>
                            
                            <motion.div
                                key={isAssistantThinking || isAssistantResponding ? 'active' : 'finished'}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.15 }}
                            >
                                <div className="flex items-center gap-1">
                                    <span className="text-base font-medium text-primary/70">
                                        Milo is {isAssistantThinking ? 'thinking' : 'typing'} 
                                    </span>
                                    <div className="flex items-center gap-1 mt-2">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                className="bg-primary/40 h-1 w-1 rounded-full"
                                                animate={{
                                                    y: [0, -4, 0],
                                                    opacity: [0.5, 1, 0.5]
                                                }}
                                                transition={{
                                                    duration: 0.6,
                                                    repeat: Infinity,
                                                    delay: i * 0.2,
                                                    ease: "easeInOut"
                                                }}
                                            />
                                        ))}
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function AssistantMessageGroup({ 
    messages, 
    isAssistantThinking, 
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe 
}: { 
    messages: AssistantMessage[];
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}) {
    const isActive = isAssistantThinking || isAssistantResponding;
    const hasMessages = messages.length > 0;

    // Don't render anything if no messages and not active
    if (!hasMessages && !isActive) return null;

    return (
        <div className="flex w-full gap-3 sm:gap-2 items-start justify-start">
            <div className="flex flex-col flex-shrink-0 w-full">
                {hasMessages ? (
                    // Render actual messages
                    messages.map((msg, i) => {
                        const isFirst = i === 0;
                        const isLast = i === messages.length - 1;

                        return (
                            <AssistantMessageBubble
                                key={msg.id}
                                message={msg}
                                isFirst={isFirst}
                                isLast={isLast}
                                isAssistantThinking={isAssistantThinking}
                                isAssistantResponding={isAssistantResponding}
                                selectedRecipeId={selectedRecipeId}
                                onSelectRecipe={onSelectRecipe}
                            />
                        );
                    })
                ) : (
                    // Render thinking bubble
                    <ThinkingMessageBubble 
                        isAssistantThinking={isAssistantThinking}
                        isAssistantResponding={isAssistantResponding}
                    />
                )}
            </div>
        </div>
    );
}

export function ChatMessageGroup({ group, selectedRecipeId, onSelectRecipe, isAssistantThinking, isAssistantResponding = false }: ChatMessageGroupProps) {
    const { role, messages } = group;

    return (
        <div className="mb-3 flex w-full flex-col gap-3">
            {role === 'user' && <UserMessageGroup messages={messages} />}
            {role === 'assistant' && <AssistantMessageGroup 
                messages={messages}
                isAssistantThinking={isAssistantThinking}
                isAssistantResponding={isAssistantResponding}
                selectedRecipeId={selectedRecipeId}
                onSelectRecipe={onSelectRecipe}
            />}
        </div>
    );
}
