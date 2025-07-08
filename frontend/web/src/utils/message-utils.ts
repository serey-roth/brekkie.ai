import type {
    AssistantMessage,
    AssistantRecipeMessage,
    AssistantTextMessage,
    Message,
    RoleMessageGroup,
    UserMessage,
} from '@/data/schemas/messages';

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

export function groupMessagesByRole(messages: Message[]): RoleMessageGroup[] {
    if (messages.length === 0) return [];

    const sortedMessages = [...messages].sort((a, b) => a.created_at.localeCompare(b.created_at));
    const groups: RoleMessageGroup[] = [];
    let currentGroup: RoleMessageGroup | null = null;

    for (const message of sortedMessages) {
        if (isUserMessage(message)) {
            if (currentGroup) {
                groups.push(currentGroup);
            }
            currentGroup = { role: 'user', messages: [message] };
        } else if (isAssistantMessage(message)) {
            if (currentGroup?.role === 'user') {
                groups.push(currentGroup);
                currentGroup = { role: 'assistant', messages: [message] };
            } else if (
                currentGroup?.role === 'assistant' &&
                currentGroup.messages[0].parent_id === message.parent_id
            ) {
                currentGroup.messages.push(message);
            } else {
                if (currentGroup) {
                    groups.push(currentGroup);
                }
                currentGroup = { role: 'assistant', messages: [message] };
            }
        }
    }

    if (currentGroup) {
        groups.push(currentGroup);
    }

    return groups;
}
