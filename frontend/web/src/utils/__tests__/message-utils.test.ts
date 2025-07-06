import { describe, it, expect } from 'vitest';
import type { Message } from '@/data/schemas/messages';
import { groupMessagesByRole } from '@/utils/message-utils';

const createMessage = (
    id: string,
    role: 'user' | 'assistant',
    content_type: 'text' | 'recipe' | 'tool',
    text_content: string | null,
    created_at: string,
    parent_id?: string | null,
): Message => ({
    id,
    role,
    created_at,
    thread_id: '1',
    content_type,
    text_content,
    updated_at: created_at,
    parent_id: parent_id || null,
    recipe_id: null,
    tool_name: null,
    tool_input: null,
    tool_output: null,
    is_recipe_generation_started: false,
    is_recipe_generation_completed: false,
    model_name: 'gpt-4o',
    input_tokens: 0,
    output_tokens: 0,
});

describe('groupMessagesByRole   ', () => {
    it('should return an empty array if there are no messages', () => {
        const messages: Message[] = [];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([]);
    });

    it('should create an individual group for each user message', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage('2', 'user', 'text', 'User message 2', '2021-01-01T00:00:01Z'),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'user', messages: [messages[1]] },
        ]);
    });

    it('should group assistant messages with the same parent_id', () => {
        const messages = [
            createMessage(
                '2',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:01Z',
                '1',
            ),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:02Z',
                '1',
            ),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([{ role: 'assistant', messages: [messages[0], messages[1]] }]);
    });

    it('should create a new group for assistant messages following a user message', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage(
                '2',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:01Z',
                '1',
            ),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:02Z',
                '1',
            ),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'assistant', messages: [messages[1], messages[2]] },
        ]);
    });

    it('should create different groups for assistant messages with different parent_id', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage(
                '2',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:01Z',
                '1',
            ),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:02Z',
                '2',
            ),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'assistant', messages: [messages[1]] },
            { role: 'assistant', messages: [messages[2]] },
        ]);
    });

    it('should create a new group for assistant messages with no parent_id', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage(
                '2',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:01Z',
                '1',
            ),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:02Z',
                null,
            ),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'assistant', messages: [messages[1]] },
            { role: 'assistant', messages: [messages[2]] },
        ]);
    });

    it('should maintain chronological order of messages within each group', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage(
                '2',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:01Z',
                '1',
            ),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:02Z',
                '1',
            ),
            createMessage(
                '4',
                'assistant',
                'text',
                'Assistant message 3',
                '2021-01-01T00:00:03Z',
                '1',
            ),
            createMessage('5', 'user', 'text', 'User message 2', '2021-01-01T00:00:04Z'),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'assistant', messages: [messages[1], messages[2], messages[3]] },
            { role: 'user', messages: [messages[4]] },
        ]);
    });

    it('should handle consecutive user messages', () => {
        const messages = [
            createMessage('1', 'user', 'text', 'User message 1', '2021-01-01T00:00:00Z'),
            createMessage('2', 'user', 'text', 'User message 2', '2021-01-01T00:00:01Z'),
            createMessage(
                '3',
                'assistant',
                'text',
                'Assistant message 1',
                '2021-01-01T00:00:02Z',
                '1',
            ),
            createMessage(
                '4',
                'assistant',
                'text',
                'Assistant message 2',
                '2021-01-01T00:00:03Z',
                '2',
            ),
            createMessage('5', 'user', 'text', 'User message 3', '2021-01-01T00:00:04Z'),
            createMessage(
                '6',
                'assistant',
                'text',
                'Assistant message 3',
                '2021-01-01T00:00:05Z',
                '5',
            ),
        ];
        const groups = groupMessagesByRole(messages);
        expect(groups).toEqual([
            { role: 'user', messages: [messages[0]] },
            { role: 'user', messages: [messages[1]] },
            { role: 'assistant', messages: [messages[2]] },
            { role: 'assistant', messages: [messages[3]] },
            { role: 'user', messages: [messages[4]] },
            { role: 'assistant', messages: [messages[5]] },
        ]);
    });
});
