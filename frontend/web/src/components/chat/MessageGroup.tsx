import { motion } from 'framer-motion';
import { DateTime } from 'luxon';
import { LuUser, LuBot, LuClock } from 'react-icons/lu';
import { RecipeMessageCard } from '@/components/recipes/RecipeMessageCard';
import { Markdown } from '@/components/ui/Markdown';
import type { AssistantMessage, Message, MessageGroup } from '@/data/schemas/messages';
import { isAssistantRecipeMessage, isUserMessage } from '@/utils/message-utils';

interface ChatMessageGroupProps {
    group: MessageGroup;
    isAssistantThinking: boolean;
    isAssistantResponding: boolean;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string | null) => void;
}

function isAssistantMessage(message: Message): message is AssistantMessage {
    return message.role === 'assistant';
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

export function ChatMessageGroup({ isAssistantThinking, isAssistantResponding = false, group, selectedRecipeId, onSelectRecipe }: ChatMessageGroupProps) {
    const role = group.role;
    const messages = group.messages;

    return (
        <div
            className={`mb-6 flex w-full gap-3 sm:gap-2 ${role === 'user' ? 'items-end justify-end' : 'items-start justify-start'} `}
        >
            <div
                className={`flex flex-col flex-shrink-0 ${role === 'user' ? 'gap-1 max-w-10/12 min-w-8/12' : 'w-full'}`}
            >
                {messages.map((msg, i) => {
                    const isFirst = i === 0;
                    const isLast = i === messages.length - 1;

                    const bubbleClasses =
                        role === 'user'
                            ? `bg-primary text-white py-3 rounded-2xl`
                            : `bg-white text-contrast-subtle 
                            ${
                                isFirst && isLast ? 'rounded-2xl' : isFirst ? 'rounded-t-2xl' : isLast ? 'rounded-b-2xl' : ''
                            }
                            ${
                                  isFirst && isLast ? 'py-3' : isFirst ? 'pt-3' : isLast ? 'pb-3' : 'py-3'
                              }`;

                    return (
                        <div
                            key={msg.id}
                            className={`px-4 text-sm leading-relaxed sm:text-base ${bubbleClasses}`}
                        >
                            {isFirst && (
                                <div className={`flex items-center justify-between mb-2 ${isUserMessage(msg) ? 'text-white/90' : 'text-contrast-subtle'}`}>
                                    <div className="flex items-center gap-2">
                                        <div className="flex-shrink-0">
                                            <div className={`flex h-6 w-6 items-center justify-center rounded-full sm:h-8 sm:w-8 ${
                                                isUserMessage(msg) 
                                                    ? 'bg-white/20' 
                                                    : 'bg-primary/10 border-primary/20 border'
                                            }`}>
                                                {isUserMessage(msg) ? (
                                                    <LuUser size={18} className="text-white" />
                                                ) : (
                                                    <LuBot size={18} className="text-primary" />
                                                )}
                                            </div>
                                        </div>
                                        
                                        {isUserMessage(msg) ? (
                                            <span className="text-base font-medium">
                                                You
                                            </span>
                                        ) : (
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
                                        )}
                                    </div>
                                    
                                    <div className="flex items-center gap-2 text-xs sm:text-sm opacity-80">
                                        <div className={`flex items-center gap-1 ${isUserMessage(msg) ? 'text-white/90' : 'text-contrast-subtle/90'}`}>
                                            <LuClock size={12} />
                                            <span>
                                                {DateTime.fromISO(msg.created_at).toLocaleString(DateTime.DATETIME_SHORT)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div className="prose prose-base dark:prose-invert max-w-none">
                                {isAssistantMessage(msg) ? (
                                    isAssistantRecipeMessage(msg) ? (
                                        <RecipeMessageCard
                                            recipeId={msg.recipe_id}
                                            isGenerating={msg.is_recipe_generation_started ?? false}
                                            onSelectRecipe={onSelectRecipe}
                                            selectedRecipeId={selectedRecipeId}
                                        />
                                    ) : msg.text_content ? (
                                        <AssistantMessageContent message={msg} />
                                    ) : null
                                ) : msg.text_content ? (
                                    <p className="whitespace-pre-wrap">{msg.text_content}</p>
                                ) : null}
                            </div>

                        </div>
                    );
                })}
            </div>
        </div>
    );
}
