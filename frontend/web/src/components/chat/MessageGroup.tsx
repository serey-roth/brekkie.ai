import { motion } from 'framer-motion';
import { DateTime } from 'luxon';
import { LuUser, LuBot, LuClock } from 'react-icons/lu';
import { RecipeMessageCard } from '@/components/recipes/RecipeMessageCard';
import { Markdown } from '@/components/ui/Markdown';
import type { AssistantMessage, RoleMessageGroup, UserMessage } from '@/data/schemas/messages';
import { isAssistantMessage, isAssistantRecipeMessage } from '@/utils/message-utils';

interface ChatMessageGroupProps {
    group: RoleMessageGroup;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}

function UserMessageBubble({ message }: { message: UserMessage }) {
    return (
        <div className="flex w-full items-end justify-end gap-3 sm:gap-2">
            <div className="flex max-w-10/12 min-w-8/12 flex-shrink-0 flex-col gap-1">
                <div className="bg-primary rounded-2xl px-4 py-3 text-sm leading-relaxed text-white sm:text-base">
                    <div className="mb-2 flex items-center justify-between text-white/90">
                        <div className="flex items-center gap-2">
                            <div className="flex-shrink-0">
                                <div className="flex h-6 w-6 items-center justify-center rounded-full bg-white/20 sm:h-8 sm:w-8">
                                    <LuUser size={18} className="text-white" />
                                </div>
                            </div>
                            <span className="text-base font-medium">You</span>
                        </div>

                        <div className="flex items-center gap-2 text-xs opacity-80 sm:text-sm">
                            <div className="flex items-center gap-1 text-white/90">
                                <LuClock size={12} />
                                <span>
                                    {DateTime.fromISO(message.created_at).toLocaleString(
                                        DateTime.DATETIME_SHORT,
                                    )}
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
        <div className="flex w-full items-start justify-start gap-3 sm:gap-2">
            <div className="flex w-full flex-shrink-0 flex-col">
                {messages.map((msg) => (
                    <UserMessageBubble key={msg.id} message={msg} />
                ))}
            </div>
        </div>
    );
}

function AssistantMessageContent({ message }: { message: AssistantMessage }) {
    // TODO: Future enhancement - Add typing effect with progressive markdown rendering
    // Consider implementing a custom typing animation that works well with markdown elements
    // like lists, headers, and code blocks without breaking the visual flow
    return (
        <div>
            <Markdown>{message.text_content ?? ''}</Markdown>
        </div>
    );
}

function AssistantMessageBubble({
    message,
    isFirst,
    isLast,
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe,
}: {
    message: AssistantMessage;
    isFirst: boolean;
    isLast: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}) {
    const bubbleClasses = `bg-white text-contrast-subtle 
        ${
            isFirst && isLast
                ? 'rounded-2xl'
                : isFirst
                  ? 'rounded-t-2xl'
                  : isLast
                    ? 'rounded-b-2xl'
                    : ''
        }
        ${isFirst && isLast ? 'py-3' : isFirst ? 'pt-3' : isLast ? 'pb-3' : 'py-3'}`;

    return (
        <div className={`px-4 text-sm leading-relaxed sm:text-base ${bubbleClasses}`}>
            {isFirst && (
                <div className="text-contrast-subtle mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="flex-shrink-0">
                            <div className="bg-primary/10 border-primary/20 flex h-6 w-6 items-center justify-center rounded-full border sm:h-8 sm:w-8">
                                <LuBot size={18} className="text-primary" />
                            </div>
                        </div>

                        <motion.div
                            key="assistant-name"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.15 }}
                        >
                            {isAssistantResponding ? (
                                <motion.div
                                    key="responding"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="flex items-center gap-1"
                                >
                                    <span className="text-primary/70 text-base font-medium">
                                        Milo is responding
                                    </span>
                                    <div className="mt-2 flex items-center gap-1">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                className="bg-primary/40 h-1 w-1 rounded-full"
                                                animate={{
                                                    y: [0, -4, 0],
                                                    opacity: [0.5, 1, 0.5],
                                                }}
                                                transition={{
                                                    duration: 0.6,
                                                    repeat: Infinity,
                                                    delay: i * 0.2,
                                                    ease: 'easeInOut',
                                                }}
                                            />
                                        ))}
                                    </div>
                                </motion.div>
                            ) : (
                                <motion.span
                                    key="finished"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ duration: 0.2 }}
                                    className="text-base font-medium"
                                >
                                    Milo
                                </motion.span>
                            )}
                        </motion.div>
                    </div>

                    <div className="flex items-center gap-2 text-xs opacity-80 sm:text-sm">
                        <div className="text-contrast-subtle/90 flex items-center gap-1">
                            <LuClock size={12} />
                            <span>
                                {DateTime.fromISO(message.created_at).toLocaleString(
                                    DateTime.DATETIME_SHORT,
                                )}
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

function AssistantMessageGroup({
    messages,
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe,
}: {
    messages: AssistantMessage[];
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}) {
    return (
        <div className="flex w-full items-start justify-start gap-3 sm:gap-2">
            <div className="flex w-full flex-shrink-0 flex-col">
                {messages.map((msg, i) => {
                    const isFirst = i === 0;
                    const isLast = i === messages.length - 1;

                    return (
                        <AssistantMessageBubble
                            key={msg.id}
                            message={msg}
                            isFirst={isFirst}
                            isLast={isLast}
                            isAssistantResponding={isLast && isAssistantResponding}
                            selectedRecipeId={selectedRecipeId}
                            onSelectRecipe={onSelectRecipe}
                        />
                    );
                })}
            </div>
        </div>
    );
}

export function AssistantThinkingMessageBubble() {
    return (
        <div className="flex w-full items-start justify-start gap-3 sm:gap-2">
            <div className="flex w-full flex-shrink-0 flex-col">
                <div className="text-contrast-subtle rounded-2xl bg-white px-4 py-3 text-sm leading-relaxed sm:text-base">
                    <div className="text-contrast-subtle mb-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="flex-shrink-0">
                                <div className="bg-primary/10 border-primary/20 flex h-6 w-6 items-center justify-center rounded-full border sm:h-8 sm:w-8">
                                    <LuBot size={18} className="text-primary" />
                                </div>
                            </div>
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.15 }}
                            >
                                <div className="flex items-center gap-1">
                                    <span className="text-primary/70 text-base font-medium">
                                        Milo is thinking
                                    </span>
                                    <div className="mt-2 flex items-center gap-1">
                                        {[0, 1, 2].map((i) => (
                                            <motion.div
                                                key={i}
                                                className="bg-primary/40 h-1 w-1 rounded-full"
                                                animate={{
                                                    y: [0, -4, 0],
                                                    opacity: [0.5, 1, 0.5],
                                                }}
                                                transition={{
                                                    duration: 0.6,
                                                    repeat: Infinity,
                                                    delay: i * 0.2,
                                                    ease: 'easeInOut',
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

export function ChatMessageGroup({
    group,
    selectedRecipeId,
    onSelectRecipe,
    isAssistantResponding = false,
}: ChatMessageGroupProps) {
    const { role, messages } = group;

    return (
        <div className="mb-3 flex w-full flex-col gap-3">
            {role === 'user' ? (
                <UserMessageGroup messages={messages} />
            ) : (
                <AssistantMessageGroup
                    messages={messages}
                    isAssistantResponding={isAssistantResponding}
                    selectedRecipeId={selectedRecipeId}
                    onSelectRecipe={onSelectRecipe}
                />
            )}
        </div>
    );
}
