import { z } from 'zod';

export const RecipeIngredientSchema = z.object({
    name: z.string(),
    quantity: z.string(),
    unit: z.string().nullable(),
});
export type RecipeIngredient = z.infer<typeof RecipeIngredientSchema>;

export const RecipeInstructionSchema = z.object({
    title: z.string(),
    description: z.string(),
});
export type RecipeInstruction = z.infer<typeof RecipeInstructionSchema>;

export const RecipeCategorySchema = z.object({
    name: z.string(),
});
export type RecipeCategory = z.infer<typeof RecipeCategorySchema>;

export const RecipeSchema = z.object({
    name: z.string().nullable(),
    description: z.string().nullable(),
    prep_time_minutes: z.number().nullable(),
    cook_time_minutes: z.number().nullable(),
    servings: z.string().nullable(),
    ingredients: z.array(RecipeIngredientSchema).nullable(),
    instructions: z.array(RecipeInstructionSchema).nullable(),
    categories: z.array(RecipeCategorySchema).nullable(),
    substitutions: z.string().nullable(),
    chef_notes: z.string().nullable(),
    make_ahead_tips: z.string().nullable(),
    equipment_alternatives: z.string().nullable(),
    coordination_timeline: z.string().nullable(),
    scaling_guidance: z.string().nullable(),
    storage_notes: z.string().nullable(),
    serving_suggestions: z.string().nullable(),
});
export type Recipe = z.infer<typeof RecipeSchema>;

export const UserRecipeSchema = z
    .object({
        id: z.string(),
        user_id: z.string(),
        thread_id: z.string(),
        created_at: z.string(),
        updated_at: z.string(),
    })
    .extend(RecipeSchema.shape);
export type UserRecipe = z.infer<typeof UserRecipeSchema>;
