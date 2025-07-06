import type { UserRecipe } from '@/data/schemas/recipes';

export const mockRecipes: UserRecipe[] = [
    {
        id: 'recipe-1',
        user_id: 'user-1',
        thread_id: 'thread-1',
        name: 'Spicy Thai Basil Chicken',
        description:
            'A quick and flavorful stir-fry with tender chicken, fresh basil, and aromatic Thai spices.',
        prep_time_minutes: 15,
        cook_time_minutes: 20,
        servings: '4',
        ingredients: [
            { name: 'Chicken breast', quantity: '1', unit: 'lb' },
            { name: 'Thai basil', quantity: '2', unit: 'cups' },
            { name: 'Garlic', quantity: '4', unit: 'cloves' },
            { name: 'Fish sauce', quantity: '2', unit: 'tbsp' },
            { name: 'Soy sauce', quantity: '1', unit: 'tbsp' },
        ],
        instructions: [
            {
                title: 'Prep chicken',
                description: 'Cut chicken into bite-sized pieces and season with salt and pepper.',
            },
            {
                title: 'Stir-fry',
                description:
                    'Heat oil in wok over high heat. Add chicken and cook until golden brown.',
            },
            {
                title: 'Add aromatics',
                description: 'Add garlic and chili, stir-fry for 30 seconds until fragrant.',
            },
            {
                title: 'Finish',
                description:
                    'Add basil leaves and sauces, toss until basil wilts. Serve hot with rice.',
            },
        ],
        categories: [{ name: 'Thai' }, { name: 'Stir-fry' }, { name: 'Quick & Easy' }],
        substitutions:
            'Can use pork or tofu instead of chicken. Thai holy basil can be substituted with regular basil.',
        chef_notes: 'The key is to cook over very high heat for that authentic wok hei flavor.',
        make_ahead_tips:
            'Chicken can be marinated up to 2 hours ahead. Basil should be added fresh.',
        equipment_alternatives: "If you don't have a wok, use a large cast iron skillet.",
        coordination_timeline:
            'Start rice 20 minutes before cooking. Prep all ingredients before starting to cook.',
        scaling_guidance:
            'Recipe doubles easily. For larger batches, cook in multiple batches to maintain high heat.',
        storage_notes:
            'Leftovers keep for 3 days in refrigerator. Reheat gently to avoid overcooking chicken.',
        serving_suggestions:
            'Serve with jasmine rice, cucumber slices, and extra chili sauce on the side.',
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T10:30:00Z',
    },
    {
        id: 'recipe-2',
        user_id: 'user-1',
        thread_id: 'thread-2',
        name: 'Creamy Mushroom Risotto',
        description:
            'Rich and creamy risotto with wild mushrooms, finished with parmesan and fresh herbs.',
        prep_time_minutes: 10,
        cook_time_minutes: 30,
        servings: '4',
        ingredients: [
            { name: 'Arborio rice', quantity: '1.5', unit: 'cups' },
            { name: 'Mixed mushrooms', quantity: '1', unit: 'lb' },
            { name: 'Vegetable stock', quantity: '6', unit: 'cups' },
            { name: 'Parmesan cheese', quantity: '1', unit: 'cup' },
            { name: 'White wine', quantity: '1/2', unit: 'cup' },
        ],
        instructions: [
            { title: 'Prepare stock', description: 'Keep vegetable stock warm in a separate pot.' },
            {
                title: 'Sauté mushrooms',
                description: 'Cook mushrooms until golden brown, remove from pan.',
            },
            {
                title: 'Toast rice',
                description: 'Add rice to pan and toast until translucent around edges.',
            },
            { title: 'Add wine', description: 'Pour in wine and stir until absorbed.' },
            {
                title: 'Gradual addition',
                description: 'Add stock one ladle at a time, stirring constantly.',
            },
            {
                title: 'Finish',
                description:
                    'Stir in parmesan, mushrooms, and herbs. Let rest 2 minutes before serving.',
            },
        ],
        categories: [{ name: 'Italian' }, { name: 'Vegetarian' }, { name: 'Comfort Food' }],
        substitutions:
            'Can use any type of mushrooms. Vegetable stock can be replaced with chicken stock for non-vegetarian version.',
        chef_notes:
            'The key to perfect risotto is patience - add stock slowly and stir constantly.',
        make_ahead_tips:
            'Risotto is best served immediately, but you can prep mushrooms and stock ahead.',
        equipment_alternatives: "A heavy-bottomed pan works well if you don't have a risotto pan.",
        coordination_timeline:
            'Start stock heating 10 minutes before cooking. Prep all ingredients before starting.',
        scaling_guidance:
            'Recipe scales well. For larger batches, use multiple pans to maintain proper heat control.',
        storage_notes:
            "Risotto doesn't keep well - it's best eaten fresh. Leftovers can be made into arancini.",
        serving_suggestions:
            'Serve with a crisp green salad and crusty bread. Garnish with extra parmesan and herbs.',
        created_at: '2024-01-10T14:20:00Z',
        updated_at: '2024-01-10T14:20:00Z',
    },
    {
        id: 'recipe-3',
        user_id: 'user-1',
        thread_id: 'thread-3',
        name: 'Chocolate Chip Cookies',
        description: 'Classic chewy chocolate chip cookies with crispy edges and soft centers.',
        prep_time_minutes: 15,
        cook_time_minutes: 12,
        servings: '24 cookies',
        ingredients: [
            { name: 'All-purpose flour', quantity: '2.25', unit: 'cups' },
            { name: 'Butter', quantity: '1', unit: 'cup' },
            { name: 'Brown sugar', quantity: '3/4', unit: 'cup' },
            { name: 'White sugar', quantity: '3/4', unit: 'cup' },
            { name: 'Chocolate chips', quantity: '2', unit: 'cups' },
            { name: 'Eggs', quantity: '2', unit: 'large' },
        ],
        instructions: [
            {
                title: 'Cream butter and sugars',
                description: 'Beat butter and sugars until light and fluffy.',
            },
            {
                title: 'Add eggs',
                description: 'Add eggs one at a time, beating well after each addition.',
            },
            {
                title: 'Mix dry ingredients',
                description: 'Whisk together flour, baking soda, and salt.',
            },
            {
                title: 'Combine',
                description:
                    'Gradually add dry ingredients to wet ingredients, mixing until just combined.',
            },
            { title: 'Add chocolate', description: 'Fold in chocolate chips.' },
            {
                title: 'Bake',
                description:
                    'Drop rounded tablespoons onto baking sheet and bake at 375°F for 10-12 minutes.',
            },
        ],
        categories: [{ name: 'Dessert' }, { name: 'Baking' }, { name: 'Kid-Friendly' }],
        substitutions:
            'Can use dark chocolate chips, white chocolate chips, or a mix. Butter can be replaced with coconut oil for dairy-free version.',
        chef_notes:
            "Don't overmix the dough - this will make the cookies tough. Let them cool on the baking sheet for 5 minutes before transferring.",
        make_ahead_tips:
            'Dough can be refrigerated for up to 3 days or frozen for up to 3 months. Let come to room temperature before baking.',
        equipment_alternatives:
            'A stand mixer works best, but a hand mixer or even a wooden spoon will work.',
        coordination_timeline:
            'Preheat oven while mixing dough. Line baking sheets with parchment paper before starting.',
        scaling_guidance:
            'Recipe doubles easily. For larger batches, bake in multiple sheets, rotating halfway through.',
        storage_notes:
            'Store in an airtight container at room temperature for up to 1 week. Can be frozen for up to 3 months.',
        serving_suggestions:
            'Serve warm with a glass of cold milk. Great for parties, potlucks, or as a sweet treat.',
        created_at: '2024-01-05T16:45:00Z',
        updated_at: '2024-01-05T16:45:00Z',
    },
];
