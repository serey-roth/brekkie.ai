import type { Recipe } from '../../schemas/recipes';

// Step 1: Add name
const recipe1: Recipe = {
    name: 'Mediterranean Pasta &amp; Salad',
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
};

// Step 2: Add description
const recipe2: Recipe = {
    ...recipe1,
    description: 'A quick and flavorful pasta dish with Mediterranean flavors',
};

// Step 3: Add prep_time
const recipe3: Recipe = { ...recipe2, prep_time_minutes: 10 };

// Step 4: Add cook_time
const recipe4: Recipe = { ...recipe3, cook_time_minutes: 15 };

// Step 5: Add servings
const recipe5: Recipe = { ...recipe4, servings: '2-3' };

// Step 6: Add categories
const recipe6: Recipe = { ...recipe5, categories: [{ name: 'pasta' }, { name: 'mediterranean' }] };

// Step 6: Add categories
const recipe7: Recipe = {
    ...recipe6,
    categories: [{ name: 'pasta' }, { name: 'mediterranean' }, { name: 'quick-meals' }],
};

// Step 7: Add first ingredient
const recipe8: Recipe = {
    ...recipe7,
    ingredients: [{ name: 'penne pasta', quantity: '8', unit: 'oz' }],
};

// Step 7: Add second ingredient
const recipe9: Recipe = {
    ...recipe8,
    ingredients: [
        ...(recipe8.ingredients ?? []),
        { name: 'olive oil', quantity: '2', unit: 'tbsp' },
    ],
};

// Step 8: Add third ingredient
const recipe10: Recipe = {
    ...recipe9,
    ingredients: [
        ...(recipe9.ingredients ?? []),
        { name: 'garlic', quantity: '3', unit: 'cloves' },
    ],
};

// Step 9: Add fourth ingredient
const recipe11: Recipe = {
    ...recipe10,
    ingredients: [
        ...(recipe10.ingredients ?? []),
        { name: 'cherry tomatoes', quantity: '1', unit: 'cup' },
    ],
};

// Step 10: Add first instruction
const recipe12: Recipe = {
    ...recipe11,
    instructions: [
        {
            title: 'Cook pasta',
            description:
                'Bring a large pot of salted water to boil and cook pasta according to package instructions.',
        },
    ],
};

// Step 11: Add second instruction
const recipe13: Recipe = {
    ...recipe12,
    instructions: [
        ...(recipe12.instructions ?? []),
        {
            title: 'Heat oil',
            description: 'While pasta cooks, heat olive oil in a large skillet over medium heat.',
        },
    ],
};

// Step 12: Add third instruction
const recipe14: Recipe = {
    ...recipe13,
    instructions: [
        ...(recipe13.instructions ?? []),
        {
            title: 'Add garlic',
            description: 'Add garlic and cook until fragrant, about 30 seconds.',
        },
    ],
};

// Step 16: Add substitutions
const recipe15: Recipe = {
    ...recipe14,
    substitutions: 'You can substitute regular olives for kalamata olives if needed.',
};

// Step 17: Add chef_notes
const recipe16: Recipe = {
    ...recipe15,
    chef_notes: 'The key to this dish is not overcooking the garlic and tomatoes.',
};

// Step 18: Add make_ahead_tips
const recipe17: Recipe = {
    ...recipe16,
    make_ahead_tips: 'You can prep the ingredients up to 2 hours ahead.',
};

// Step 19: Add equipment_alternatives
const recipe18: Recipe = {
    ...recipe17,
    equipment_alternatives: "If you don't have a large skillet, a wok or large saucepan",
};

// Step 20: Add coordination_timeline
const recipe19: Recipe = {
    ...recipe18,
    coordination_timeline:
        'Start heating the water first, then prep ingredients while waiting for it to boil.',
};

// Step 21: Add scaling_guidance
const recipe20: Recipe = {
    ...recipe19,
    scaling_guidance: 'This recipe can be easily doubled or tripled.',
};

// Step 22: Add storage_notes
const recipe21: Recipe = {
    ...recipe20,
    storage_notes: 'Best served immediately, but leftovers can be refrigerated for up to 2 days.',
};

// Step 23: Add serving_suggestions
const recipe22: Recipe = {
    ...recipe21,
    serving_suggestions: 'Serve with a crisp green salad and crusty bread.',
};

// Step 24: Add substitutions
const recipe23: Recipe = {
    ...recipe22,
    substitutions: 'You can substitute regular olives for kalamata olives if needed.',
};

export const evolvingRecipeList = [
    recipe1,
    recipe2,
    recipe3,
    recipe4,
    recipe5,
    recipe6,
    recipe7,
    recipe8,
    recipe9,
    recipe10,
    recipe11,
    recipe12,
    recipe13,
    recipe14,
    recipe15,
    recipe16,
    recipe17,
    recipe18,
    recipe19,
    recipe20,
    recipe21,
    recipe22,
    recipe23,
];
