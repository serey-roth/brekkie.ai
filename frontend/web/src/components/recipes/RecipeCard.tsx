import { Clock, Users } from 'lucide-react';
import Markdown from 'react-markdown';
import type { UserRecipe } from '@/data/schemas/recipes';
import { formatRecipeCategory, formatRecipeTime } from '@/utils/recipe-utils';

type RecipeCardProps = {
    recipe: UserRecipe;
    selectedRecipeId: string | null;
    onSelectRecipe: (recipeId: string) => void;
    className?: string;
};

export const RecipeCard = ({
    recipe,
    selectedRecipeId,
    onSelectRecipe,
    className,
}: RecipeCardProps) => {
    return (
        <div
            className={`bg-contrast-subtle border-border/10 w-full cursor-pointer rounded-lg border p-4 shadow-sm transition-all duration-300 ease-out ${selectedRecipeId === recipe.id ? 'border-accent border-2 shadow-md' : 'hover:border-border/40'} ${className}`}
            onClick={() => onSelectRecipe(recipe.id)}
        >
            <h3 className="text-background mb-2 text-lg font-medium">
                <Markdown>{recipe.name ?? ''}</Markdown>
            </h3>

            <div className="text-background-light mb-2 flex flex-wrap items-center gap-x-4 gap-y-2">
                {(recipe.prep_time_minutes || recipe.cook_time_minutes) && (
                    <div className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        <span className="text-sm">
                            Total:{' '}
                            {formatRecipeTime(
                                (recipe.prep_time_minutes ?? 0) + (recipe.cook_time_minutes ?? 0),
                            )}
                        </span>
                    </div>
                )}
                {recipe.servings && (
                    <div className="flex items-center gap-1">
                        <Users className="h-4 w-4" />
                        <span className="text-sm">{recipe.servings} servings</span>
                    </div>
                )}
            </div>

            {recipe.categories && recipe.categories.length > 0 && (
                <div className="flex flex-wrap gap-1">
                    {recipe.categories.map((category) => (
                        <div
                            key={category.name}
                            className="bg-accent-dark text-accent-light rounded-full px-2 py-0.5 text-xs"
                        >
                            <Markdown>{formatRecipeCategory(category.name)}</Markdown>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};
