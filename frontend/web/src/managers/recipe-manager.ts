import { produce } from "immer";
import type { UserRecipe } from "@/data/schemas/recipes";
import { EventManager } from "@/utils/event-manager";

type RecipeEvents = {
    recipeAdded: UserRecipe,
    recipesAdded: UserRecipe[],
    recipeUpdated: UserRecipe,
}

export class RecipeManager {
    private _recipes: UserRecipe[] = [];
    private _eventManager = new EventManager<RecipeEvents>();
    
    subscribe<K extends keyof RecipeEvents>(event: K, callback: (payload: RecipeEvents[K]) => void) {
        this._eventManager.subscribe(event, callback);
    }

    unsubscribe<K extends keyof RecipeEvents>(event: K, callback: (payload: RecipeEvents[K]) => void) {
        this._eventManager.unsubscribe(event, callback);
    }
    
    getRecipes() {
        return this._recipes;
    }

    getRecipe(id: string) {
        return this._recipes.find(recipe => recipe.id === id);
    }

    addRecipe(recipe: UserRecipe) {
        this._recipes.push(recipe);
        this._eventManager.publish('recipeAdded', recipe);
    }

    addRecipes(recipes: UserRecipe[]) {
        this._recipes = produce(this._recipes, draft => {
            recipes.forEach(recipe => {
                const existingRecipe = draft.find(r => r.id === recipe.id);
                if (!existingRecipe) {
                    draft.push(recipe);
                }
            });
        });
        this._eventManager.publish('recipesAdded', recipes);
    }

    updateRecipe(recipe: UserRecipe) {
        this._recipes = produce(this._recipes, draft => {
            const index = draft.findIndex(r => r.id === recipe.id);
            if (index !== -1) {
                draft[index] = recipe;
            }
        });
        this._eventManager.publish('recipeUpdated', recipe);
    }

    resetState() {
        this._recipes = [];
    }

    dispose() {
        this._eventManager.dispose();
    }
}