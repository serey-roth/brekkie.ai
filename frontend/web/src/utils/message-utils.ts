import type { AssistantMessage, AssistantRecipeMessage, AssistantTextMessage, Message, MessageGroup, UserMessage, } from "@/data/schemas/messages";

export function isUserMessage(message: Message): message is UserMessage {
    return message.role === 'user';
}

export function isAssistantMessage(message: Message): message is AssistantMessage {
    return message.role === 'assistant';
}

export function isAssistantTextMessage(message: Message): message is AssistantTextMessage {
    return message.role === 'assistant' && message.content_type === 'text';
}   

export function isAssistantRecipeMessage(message: Message): message is AssistantRecipeMessage {
    return message.role === 'assistant' && message.content_type === 'recipe' && !!message.recipe_id;
}

export function groupChatMessages(messages: Message[]): MessageGroup[] {
    if (messages.length === 0) return [];

    const sortedMessages = [...messages].sort((a, b) => a.created_at.localeCompare(b.created_at));

    const firstMessage = sortedMessages[0];
    const groups: MessageGroup[] = [];
    let currentGroup: Message[] = [firstMessage];

    for (let i = 1; i < sortedMessages.length; i++) {
        const curr = sortedMessages[i];
        const prev = sortedMessages[i - 1];

        if (curr.role === prev.role) {
            currentGroup.push(curr);
        } else {
            if (isUserMessage(prev)) {
                groups.push({
                    role: 'user',
                    messages: currentGroup as UserMessage[],
                });
            } else {
                groups.push({
                    role: 'assistant',
                    messages: currentGroup as AssistantMessage[],
                });
            }
            currentGroup = [curr];
        }
    }

    if (currentGroup.length > 0) {
        groups.push(
            isUserMessage(currentGroup[0])
                ? { role: 'user', messages: currentGroup as UserMessage[] }
                : { role: 'assistant', messages: currentGroup as AssistantMessage[] }
        );
    }

    return groups;
}
