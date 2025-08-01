import { motion } from 'framer-motion';
import { Bot, Info } from 'lucide-react';
import { DateTime } from 'luxon';
import { RecipeMessageCard } from '@/components/recipes/RecipeMessageCard';
import { Avatar } from '@/components/ui/Avatar';
import { Markdown } from '@/components/ui/Markdown';
import type { AssistantMessage, RoleMessageGroup, UserMessage } from '@/data/schemas/messages';
import type { UserMetadata } from '@/supabase-client';
import { isAssistantMessage, isAssistantRecipeMessage } from '@/utils/message-utils';

interface ChatMessageGroupProps {
    group: RoleMessageGroup;
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    currentUser: UserMetadata | null;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}

function UserMessageBubble({
    message,
    currentUser,
}: {
    message: UserMessage;
    currentUser: UserMetadata | null;
}) {
    return (
        <div className="flex w-full items-end justify-end gap-3 sm:gap-2">
            <div className="flex max-w-10/12 min-w-8/12 flex-shrink-0 flex-col gap-1">
                <div className="bg-primary rounded-2xl px-4 py-3 text-sm leading-relaxed text-white sm:text-base">
                    <div className="mb-2 flex items-center justify-between text-white/90">
                        <div className="flex items-center gap-2">
                            <div className="flex-shrink-0">
                                <Avatar
                                    name={currentUser?.name ?? null}
                                    avatarUrl={currentUser?.avatar_url}
                                    size="sm"
                                />
                            </div>
                            <span className="text-base font-medium">
                                {currentUser?.name ?? 'You'}
                            </span>
                        </div>

                        <div className="flex items-center gap-2 self-start text-xs opacity-80 sm:text-sm">
                            <div className="group relative flex items-center gap-1 text-white/90">
                                <Info size={12} className="cursor-help" />
                                <div className="absolute right-0 bottom-full mb-2 hidden whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs text-white group-hover:block">
                                    {DateTime.fromISO(message.created_at).toLocaleString(
                                        DateTime.DATETIME_SHORT,
                                    )}
                                </div>
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

function UserMessageGroup({
    messages,
    currentUser,
}: {
    messages: UserMessage[];
    currentUser: UserMetadata | null;
}) {
    return (
        <div className="flex w-full items-start justify-start gap-3 sm:gap-2">
            <div className="flex w-full flex-shrink-0 flex-col">
                {messages.map((msg) => (
                    <UserMessageBubble key={msg.id} message={msg} currentUser={currentUser} />
                ))}
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
    onSelectRecipe,
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
                                <Bot size={18} className="text-primary" />
                            </div>
                        </div>

                        <motion.div
                            key="assistant-name"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.15 }}
                        >
                            {isAssistantThinking || isAssistantResponding ? (
                                <motion.div
                                    key="responding"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="flex items-center gap-1"
                                >
                                    <span className="text-primary/70 text-base font-medium">
                                        Milo is {isAssistantThinking ? 'thinking' : 'responding'}
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

                    <div className="flex items-center gap-2 self-start text-xs opacity-80 sm:text-sm">
                        <div className="group text-contrast-subtle/90 relative flex items-center gap-1">
                            <Info size={14} className="cursor-help" />
                            <div className="absolute right-0 bottom-full mb-2 hidden whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs text-white group-hover:block">
                                {DateTime.fromISO(message.created_at).toLocaleString(
                                    DateTime.DATETIME_SHORT,
                                )}
                            </div>
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
                        <div className="prose prose-base dark:prose-invert max-w-none">
                            <Markdown>{message.text_content ?? ''}</Markdown>
                        </div>
                    ) : null
                ) : null}
            </div>
        </div>
    );
}

function AssistantMessageGroup({
    messages,
    isAssistantThinking,
    isAssistantResponding,
    selectedRecipeId,
    onSelectRecipe,
}: {
    messages: AssistantMessage[];
    isAssistantThinking: boolean;
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
                            isAssistantThinking={isLast && isAssistantThinking}
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

export function ChatMessageGroup({
    group,
    currentUser,
    selectedRecipeId,
    onSelectRecipe,
    isAssistantThinking = false,
    isAssistantResponding = false,
}: ChatMessageGroupProps) {
    const { role, messages } = group;

    return (
        <div className="mb-3 flex w-full flex-col gap-3">
            {role === 'user' ? (
                <UserMessageGroup messages={messages} currentUser={currentUser} />
            ) : (
                <AssistantMessageGroup
                    messages={messages}
                    isAssistantThinking={isAssistantThinking}
                    isAssistantResponding={isAssistantResponding}
                    selectedRecipeId={selectedRecipeId}
                    onSelectRecipe={onSelectRecipe}
                />
            )}
        </div>
    );
}
