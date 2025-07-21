import { useEffect, useRef, useState } from 'react';
import { useChatStateManager } from '@/context/chat-context';
import { type ChatEvent } from '@/data/schemas/chat-events';
import { type Message } from '@/data/schemas/messages';
import { type UserRecipe } from '@/data/schemas/recipes';
import { type Thread } from '@/data/schemas/threads';
import { type UserAccess } from '@/data/schemas/user-access';
import { evolvingRecipeList } from '@/data/tests/recipes/evolving-recipe';

const userAccess: UserAccess = {
    access_token: '123',
    is_authenticated: true,
    user_id: '1',
    user_message_count: 5,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
};

export function useRecipeGenerationSimulation() {
    const chatStateManager = useChatStateManager();
    const [isRunning, setIsRunning] = useState(false);

    const currentRecipeIndex = useRef(0);
    useEffect(() => {
        const recipes = evolvingRecipeList;
        const thread = {
            id: '1',
            user_id: '1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            resumed_at: null,
            error_message: null,
            title: 'Test Recipe Generation Thread',
            summary: null,
            is_empty: false,
        } satisfies Thread;

        const recipeMessage = {
            id: '1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            thread_id: '1',
            role: 'assistant',
            content_type: 'recipe',
            text_content: null,
            parent_id: 'test-user-message-1',
            recipe_id: 'recipe_1',
            model_name: null,
            input_tokens: null,
            output_tokens: null,
            is_recipe_generation_started: true,
            is_recipe_generation_completed: false,
            tool_name: null,
            tool_input: null,
            tool_output: null,
        } satisfies Message;

        const userRecipe = {
            id: 'recipe_1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            thread_id: '1',
            user_id: '1',
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

        setIsRunning(true);

        chatStateManager.handleChatEvent({
            event: 'recipe_generation_started',
            data: {
                user_access: userAccess,
                thread: thread,
                message: recipeMessage,
                recipe: userRecipe,
            },
        } satisfies ChatEvent);

        const interval = setInterval(() => {
            if (currentRecipeIndex.current === recipes.length - 1) {
                const recipe = recipes[currentRecipeIndex.current];
                const newUserRecipe = {
                    ...userRecipe,
                    ...recipe,
                } satisfies UserRecipe;
                const newMessage = {
                    ...recipeMessage,
                    recipe_id: userRecipe.id,
                    is_recipe_generation_completed: true,
                    is_recipe_generation_started: false,
                } satisfies Message;
                chatStateManager.handleChatEvent({
                    event: 'recipe_generation_completed',
                    data: {
                        user_access: userAccess,
                        thread: thread,
                        message: newMessage,
                        recipe: newUserRecipe,
                    },
                } satisfies ChatEvent);
                clearInterval(interval);
                return;
            }

            const newMessage = {
                ...recipeMessage,
                recipe_id: userRecipe.id,
                is_recipe_generation_started: true,
                is_recipe_generation_completed: false,
            } satisfies Message;
            const newUserRecipe = {
                ...userRecipe,
                ...recipes[currentRecipeIndex.current],
            } satisfies UserRecipe;
            chatStateManager.handleChatEvent({
                event: 'recipe_field_detected',
                data: {
                    user_access: userAccess,
                    thread: thread,
                    message: newMessage,
                    recipe: newUserRecipe,
                },
            } satisfies ChatEvent);

            currentRecipeIndex.current++;
        }, 1000);

        return () => {
            setIsRunning(false);
            clearInterval(interval);
        };
    }, [chatStateManager]);

    return { isRunning };
}
