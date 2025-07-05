import { useEffect, useState } from "react";
import { LuLoader } from "react-icons/lu";
import { useRecipeManager } from "@/context/chat-context";
import type { UserRecipe } from "@/data/schemas/recipes";
import { RecipeCard } from "./RecipeCard";

type RecipeCardProps = {
    recipeId: string;
    isGenerating: boolean;
    onSelectRecipe: (recipeId: string) => void;
    selectedRecipeId: string | null;
}

const getGenerationProgress = (recipe: UserRecipe | null) => {
    if (!recipe) return { message: 'Searching for the perfect recipe...' };
    if (!recipe.name) return { message: 'Writing recipe name...' };
    if (!recipe.description) return { message: 'Writing recipe description...' };
    if (!recipe.prep_time_minutes || !recipe.cook_time_minutes || !recipe.servings) return { message: 'Calculating recipe time and servings...' };
    if (!recipe.categories?.length) return { message: 'Adding recipe categories...' };

    if (recipe.instructions?.length) return { message: 'Adding final touches...' };
    if (recipe.ingredients?.length) return { message: 'Writing step-by-step instructions...' };
    return { message: 'Writing ingredients...' };
};

export function RecipeMessageCard({ recipeId, isGenerating, onSelectRecipe, selectedRecipeId }: RecipeCardProps) {
    const recipeManager = useRecipeManager();   
    const [recipe, setRecipe] = useState<UserRecipe | null>(recipeManager.getRecipe(recipeId) ?? null);

    const handleSelectRecipe = () => {
        onSelectRecipe(recipeId);
    };

    useEffect(() => {
        const recipeUpdatedListener = (recipe: UserRecipe) => {
            if (recipe.id === recipeId) {
                setRecipe(recipe);
            }
        };
        recipeManager.subscribe('recipeUpdated', recipeUpdatedListener);
        return () => {
            recipeManager.unsubscribe('recipeUpdated', recipeUpdatedListener);
        };
    }, [recipeId, recipeManager]);


    useEffect(() => {
        setRecipe(recipeManager.getRecipe(recipeId) ?? null);
    }, [recipeId, recipeManager]);

    if (isGenerating) {
        const { message } = getGenerationProgress(recipe);

        return (
            <div
                className={`bg-contrast-subtle border-border/50 w-full cursor-pointer rounded-lg border p-4 shadow-sm transition-all duration-200 ease-in-out hover:shadow-md hover:border-border ${selectedRecipeId === recipeId ? 'border-accent border-2 shadow-md scale-[1.02]' : ''} ${isGenerating && !recipe?.name ? 'pointer-events-none cursor-not-allowed opacity-60' : ''}`}
                onClick={handleSelectRecipe}
            >
                <div className="flex flex-col gap-3">
                    <div className="flex items-center gap-3">
                        <LuLoader className="h-5 w-5 text-background-light animate-spin" />
                        <p className="text-background-light text-sm">{message}</p>
                    </div>
                </div>
            </div>
        );
    }

    if (!recipe) return null;

    return (
        <RecipeCard
            recipe={recipe}
            selectedRecipeId={selectedRecipeId}
            onSelectRecipe={handleSelectRecipe}
        />
    );
}