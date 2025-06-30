import type { Message } from "@/data/schemas/messages";

const message1: Message = {
    id: "1",
    thread_id: "1",
    role: "assistant",
    content_type: "text",
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
}

const message2: Message = {
    ...message1,
    text_content: message1.text_content + " I'd be happy to",
}

const message3: Message = {
    ...message2,
    text_content: message2.text_content + " help you with a recipe for a",
}

const message4: Message = {
    ...message3,
    text_content: message3.text_content + " Mediterranean Pasta &amp; Salad.",
}

const message5: Message = {
    ...message4,
    text_content: message4.text_content + " It's going to be a quick and flavorful with"
}

const message6: Message = {
    ...message5,
    text_content: message5.text_content + " the garlic and olive oil that you asked for.",
}

const message7: Message = {
    ...message6,
    text_content: "I'd be happy to help you with a recipe for a Mediterranean Pasta &amp; Salad. It's going to be a quick and flavorful with the garlic and olive oil that you asked for."
}

export const evolvingAssistantTextMessage = [message1, message2, message3, message4, message5, message6, message7];
