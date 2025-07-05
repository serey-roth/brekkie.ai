import { useEffect, useState, useRef, useCallback } from "react";
import { useChatStateManager } from "@/context/chat-context";
import type { AssistantRecipeMessage, Message } from "@/data/schemas/messages";
import type { UserRecipe } from "@/data/schemas/recipes";
import type { Thread } from "@/data/schemas/threads";
import type { UserAccessData } from "@/data/schemas/user-access";
import { evolvingRecipeList } from "@/data/tests/recipes/evolving-recipe";

const userAccessData: UserAccessData = {
    access_token: "mock-access-token",
    is_authenticated: true,
    user_id: "1",
    email: null,
    name: null,
    user_message_count: 0,
}

const thread: Thread = {
    id: "1",
    user_id: "1",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    resumed_at: null,
    error_message: null,
    title: null, 
    summary: null,
    is_empty: true,
}

const chunks = {
    "user_message_1": ["I'm craving Mediterranean food tonight. Can you help me make a pasta dish with Mediterranean flavors? I have some garlic and olive oil on hand."],
    "ai_message_1": [
        "I'd be happy to ",
        "help you with a recipe for a ",
        "Mediterranean Pasta & Salad. ",
        "It's going to be a quick and flavorful dish ",
        "with the garlic and olive oil that you asked for."
    ],
    "user_message_2": ["That sounds perfect! Can you give me the recipe?"],
    "ai_message_2": [
        "Absolutely! ",
        "Let me create a delicious Mediterranean pasta recipe for you. ",
        "This will be a quick and flavorful dish ",
        "that's perfect for a weeknight dinner."
    ]
}

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export function useRecipeConversationSimulation() {
    const chatStateManager = useChatStateManager();
    const [isRunning, setIsRunning] = useState(false);
    const [isCompleted, setIsCompleted] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const startSimulation = useCallback(async () => {
        setIsRunning(true);
        setIsCompleted(false);
        
        // Create abort controller for cleanup
        abortControllerRef.current = new AbortController();
        const { signal } = abortControllerRef.current;

        try {
            // Start thread
            chatStateManager.handleChatEvent({
                event: "thread_started",
                data: {
                    user_access_data: userAccessData,
                    thread: thread,
                }
            });

            await delay(1000);

            // First user message
            const userMessage1 = chatStateManager.createUserMessage(chunks.user_message_1[0]);
            await delay(2000);

            // First AI response
            const updatedAt = new Date().toISOString();
            let updatedThread = {
                ...thread,
                is_empty: false,
                updated_at: updatedAt,
            } satisfies Thread;
            
            const messageId = crypto.randomUUID();
            const message = {
                id: messageId,
                thread_id: thread.id,
                role: "assistant" as const,
                content_type: "text" as const,
                text_content: "",
                created_at: updatedAt,
                updated_at: updatedAt,
                model_name: null,
                input_tokens: null,
                output_tokens: null,
                recipe_id: null,
                is_recipe_generation_started: false,
                is_recipe_generation_completed: false,
                tool_name: null,
                tool_input: null,
                tool_output: null,
                parent_id: userMessage1.id,
            } satisfies Message;

            chatStateManager.handleChatEvent({
                event: "text_message_started",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                    message: message,
                }
            });

            // Stream first AI message chunks
            let currentText = "";
            for (const chunk of chunks.ai_message_1) {
                if (signal.aborted) return;
                currentText += chunk;
                chatStateManager.handleChatEvent({
                    event: "text_message_chunk_generated",
                    data: {
                        user_access_data: userAccessData,
                        thread: updatedThread,
                        message: {
                            ...message,
                            text_content: currentText,
                        } satisfies Message,
                    }
                });
                await delay(1000);
            }

            chatStateManager.handleChatEvent({
                event: "text_message_completed",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                    message: {
                        ...message,
                        text_content: currentText,
                    } satisfies Message,
                }
            });

            await delay(1000);

            // Second user message
            const userMessage2 = chatStateManager.createUserMessage(chunks.user_message_2[0]);
            await delay(2000);

            // Second AI response
            const messageId2 = crypto.randomUUID();
            const message2 = {
                id: messageId2,
                thread_id: thread.id,
                role: "assistant" as const,
                content_type: "text" as const,
                text_content: "",
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
                model_name: null,
                input_tokens: null,
                output_tokens: null,
                recipe_id: null,
                is_recipe_generation_started: false,
                is_recipe_generation_completed: false,
                tool_name: null,
                tool_input: null,
                tool_output: null,
                parent_id: userMessage2.id,
            } satisfies Message;
            
            chatStateManager.handleChatEvent({
                event: "text_message_started",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                    message: message2,
                }
            });

            // Stream second AI message chunks
            currentText = "";
            for (const chunk of chunks.ai_message_2) {
                if (signal.aborted) return;
                currentText += chunk;
                chatStateManager.handleChatEvent({
                    event: "text_message_chunk_generated",
                    data: {
                        user_access_data: userAccessData,
                        thread: updatedThread,
                        message: {
                            ...message2,
                            text_content: currentText,
                        } satisfies Message,
                    }
                });
                await delay(1000);
            }

            chatStateManager.handleChatEvent({
                event: "text_message_completed",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                    message: {
                        ...message2,
                        text_content: currentText,
                    } satisfies Message,
                }
            });

            await delay(1000);
        
            updatedThread = {
                ...updatedThread,
                is_empty: false,
                updated_at: new Date().toISOString(),
                title: "Mediterranean Pasta & Salad",
            } satisfies Thread;

            // Update thread title
            chatStateManager.handleChatEvent({
                event: "thread_title_updated",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                }
            });

            await delay(1000);

            // Start recipe generation
            const recipeUpdatedAt = new Date().toISOString();
            const recipeMessageId = crypto.randomUUID();
            const recipeId = crypto.randomUUID();
            const recipeMessage = {
                id: recipeMessageId,
                thread_id: thread.id,
                role: "assistant" as const,
                content_type: "recipe" as const,
                recipe_id: recipeId,
                is_recipe_generation_started: true,
                is_recipe_generation_completed: false,
                tool_name: null,
                tool_input: null,
                tool_output: null,
                created_at: recipeUpdatedAt,
                updated_at: recipeUpdatedAt,
                model_name: null,
                input_tokens: null,
                output_tokens: null,
                text_content: null,
                parent_id: userMessage2.id,
            } satisfies AssistantRecipeMessage;

            const userRecipe = {
                id: recipeId,
                created_at: recipeUpdatedAt,
                updated_at: recipeUpdatedAt,
                thread_id: "1",
                user_id: "1",
                name: null,
                description: null,
                prep_time_minutes: null,
                cook_time_minutes: null,
                servings: null,
                ingredients: null,
                instructions: null,
                categories: null,
                substitutions: null,
                chef_notes: null,
                make_ahead_tips: null,
                equipment_alternatives: null,
                coordination_timeline: null,
                scaling_guidance: null,
                storage_notes: null,
                serving_suggestions: null,
            } satisfies UserRecipe;

            chatStateManager.handleChatEvent({
                event: "recipe_generation_started",
                data: {
                    user_access_data: userAccessData,
                    thread: {
                        ...thread,
                    } satisfies Thread,
                    message: recipeMessage,
                    recipe: userRecipe,
                }
            });

            // Stream recipe field updates
            for (let i = 0; i < evolvingRecipeList.length - 1; i++) {
                if (signal.aborted) return;
                chatStateManager.handleChatEvent({
                    event: "recipe_field_detected",
                    data: {
                        user_access_data: userAccessData,
                        thread: updatedThread,
                        message: recipeMessage,
                        recipe: {
                            ...userRecipe,
                            ...evolvingRecipeList[i],
                        } satisfies UserRecipe,
                    }
                });
                await delay(1000);
            }

            
            // Complete recipe generation
            chatStateManager.handleChatEvent({
                event: "recipe_generation_completed",
                data: {
                    user_access_data: userAccessData,
                    thread: updatedThread,
                    message: {
                        ...recipeMessage,
                        is_recipe_generation_started: false,
                        is_recipe_generation_completed: true,
                    } satisfies Message,
                    recipe: {
                        ...userRecipe,
                        ...evolvingRecipeList[evolvingRecipeList.length - 1],
                    } satisfies UserRecipe,
                }
            });

            await delay(1000);
            setIsCompleted(true);

        } catch (error) {
            if (!signal.aborted) {
                console.error('Simulation error:', error);
            }
        } finally {
            setIsRunning(false);
        }
    }, [chatStateManager]);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    return {
        startSimulation,
        isRunning,
        isCompleted,
    };
}