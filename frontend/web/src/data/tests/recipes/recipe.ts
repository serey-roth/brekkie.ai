import type { Recipe } from '../../schemas/recipes';

export const testRecipe: Recipe = {
    name: "Classic Chocolate Chip Cookies",
    description: "A timeless recipe for soft and chewy chocolate chip cookies with a perfect balance of sweetness and chocolate.",
    prep_time_minutes: 15,
    cook_time_minutes: 10,
    servings: "24 cookies",
    ingredients: [
        {
            name: 'All-purpose flour',
            quantity: "2 1/4",
            unit: "cups",
        },
        {
            name: 'Butter',
            quantity: "1",
            unit: "cup",
        },
        {
            name: 'Brown sugar',
            quantity: "3/4",
            unit: "cup",
        },
        {
            name: 'White sugar',
            quantity: "3/4",
            unit: "cup",
        },
        {
            name: 'Eggs',
            quantity: "2",
            unit: "large",
        },
        {
            name: 'Vanilla extract',
            quantity: "2",
            unit: "teaspoons",
        },
        {
            name: 'Baking soda',
            quantity: "1",
            unit: "teaspoon",
        },
        {
            name: 'Salt',
            quantity: "1",
            unit: "teaspoon",
        },
        {
            name: 'Chocolate chips',
            quantity: "2",
            unit: "cups",
        },
    ],
    instructions: [
        {
            title: "Preheat and Prepare",
            description: "Preheat oven to 375°F (190°C). Line baking sheets with parchment paper.",
        },
        {
            title: "Cream Butter and Sugars",
            description: "In a large bowl, cream together the butter, brown sugar, and white sugar until light and fluffy.",
        },
        {
            title: "Add Wet Ingredients",
            description: "Beat in the eggs one at a time, then stir in the vanilla extract.",
        },
        {
            title: "Combine Dry Ingredients",
            description: "In a separate bowl, whisk together the flour, baking soda, and salt.",
        },
        {
            title: "Mix and Add Chocolate",
            description: "Gradually add the dry ingredients to the wet ingredients, mixing until just combined. Fold in the chocolate chips.",
        },
        {
            title: "Bake",
            description: "Drop rounded tablespoons of dough onto the prepared baking sheets. Bake for 10-12 minutes or until golden brown.",
        },
    ],
    categories: [{ name: "Dessert" }, { name: "Baking" }, { name: "Cookies" }],
    substitutions: "Replace butter with margarine for a dairy-free version, Use gluten-free flour blend instead of all-purpose flour",
    chef_notes: "For extra chewy cookies, slightly underbake them. The cookies will continue to cook from residual heat after being removed from the oven.",
    make_ahead_tips: "The cookie dough can be made ahead and stored in the refrigerator for up to 3 days or frozen for up to 3 months.",
    equipment_alternatives: "If you don't have a stand mixer, a hand mixer or even a wooden spoon will work for mixing the dough.",
    coordination_timeline: "Total time: 25-27 minutes (15 minutes prep, 10-12 minutes baking)",
    scaling_guidance: "This recipe can be easily doubled or halved. For larger batches, bake in multiple sheets, rotating them halfway through baking.",
    storage_notes: "Store cookies in an airtight container at room temperature for up to 1 week. They can also be frozen for up to 3 months.",
    serving_suggestions: "Serve warm with a glass of cold milk or as an ice cream sandwich filling. Can be served with coffee or tea for a delightful afternoon treat.",
};
