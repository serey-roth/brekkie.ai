import type { Message } from '../../schemas/messages';

export const assistantRecipeMessage = {
    id: '1',
    thread_id: 'test-thread-1',
    role: 'assistant',
    content_type: 'recipe',
    text_content: null,
    recipe_id: 'test-recipe-1',
    parent_id: 'test-user-message-1',
    created_at: '2024-03-20T10:00:00Z',
    updated_at: '2024-03-20T10:00:00Z',
    model_name: 'gpt-4',
    input_tokens: 15,
    output_tokens: 15,
    is_recipe_generation_started: true,
    is_recipe_generation_completed: false,
    tool_name: 'create_recipe',
    tool_input: {
        idea: 'Mediterranean Pasta',
        context:
            'The user is looking for a quick and flavorful pasta dish with Mediterranean flavors.',
    },
    tool_output: {
        recipe_xml: `
        <recipe>
            <name>Mediterranean Pasta</name>
            <description>A quick and flavorful pasta dish with Mediterranean flavors</description>
            <prep_time_minutes>10</prep_time_minutes>
            <cook_time_minutes>20</cook_time_minutes>
            <servings>4</servings>
            <categories>
                <category><cat_name>pasta</cat_name></category>
                <category><cat_name>mediterranean</cat_name></category>
            </categories>
            <ingredients>
                <ingredient><ing_name>pasta</ing_name><ing_quantity>1 cup</ing_quantity><ing_unit>cup</ing_unit></ingredient>
                <ingredient><ing_name>tomatoes</ing_name><ing_quantity>2</ing_quantity><ing_unit>tomatoes</ing_unit></ingredient>
                <ingredient><ing_name>olives</ing_name><ing_quantity>1/2 cup</ing_quantity><ing_unit>cup</ing_unit></ingredient>
                <ingredient><ing_name>feta cheese</ing_name><ing_quantity>1/2 cup</ing_quantity><ing_unit>cup</ing_unit></ingredient>
            </ingredients>
            <instructions>
                <instruction><inst_title>Boil pasta</inst_title><inst_description>Boil pasta according to package instructions.</inst_description></instruction>
                <instruction><inst_title>Add tomatoes, olives, and feta cheese</inst_title><inst_description>Add tomatoes, olives, and feta cheese to the pasta.</inst_description></instruction>
                <instruction><inst_title>Serve</inst_title><inst_description>Serve the pasta with tomatoes, olives, and feta cheese.</inst_description></instruction>
            </instructions>
            <serving_suggestions>Serve with a side salad.</serving_suggestions>
            <storage_notes>Store in the fridge for up to 3 days.</storage_notes>
        </recipe>
        `,
    },
} satisfies Message;
