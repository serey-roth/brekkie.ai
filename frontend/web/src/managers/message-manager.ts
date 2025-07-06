import { produce } from 'immer';
import { type AssistantMessage, type Message, type UserMessage } from '@/data/schemas/messages';
import { EventManager } from '@/utils/event-manager';
import { isAssistantMessage, isUserMessage } from '@/utils/message-utils';

type MessageEvents = {
    messageAdded: Message;
    messageUpdated: Message;
    messagesUpdated: Message[];
};

export class MessageManager {
    private _messages: Message[] = [];
    private _eventManager = new EventManager<MessageEvents>();

    subscribe<K extends keyof MessageEvents>(
        event: K,
        callback: (payload: MessageEvents[K]) => void,
    ) {
        this._eventManager.subscribe(event, callback);
    }

    unsubscribe<K extends keyof MessageEvents>(
        event: K,
        callback: (payload: MessageEvents[K]) => void,
    ) {
        this._eventManager.unsubscribe(event, callback);
    }

    addMessage(message: Message) {
        this._messages.push(message);
        this._eventManager.publish('messageAdded', message);
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    addMessages(messages: Message[]) {
        this._messages = produce(this._messages, (draft) => {
            messages.forEach((message) => {
                draft.push(message);
            });
        });
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    prependMessages(messages: Message[]) {
        this._messages = produce(this._messages, (draft) => {
            messages.forEach((message) => {
                draft.unshift(message);
            });
        });
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    updateLastMessage(updater: (draft: Message) => void) {
        this._messages = produce(this._messages, (draft) => {
            const lastMessage = draft[draft.length - 1];
            if (lastMessage) {
                updater(lastMessage);
            }
        });
        this._eventManager.publish('messageUpdated', this._messages[this._messages.length - 1]);
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    updateAssistantMessage(id: string, newMessage: AssistantMessage) {
        const index = this._messages.findIndex((m) => m.id === id);
        if (index === -1) {
            return;
        }

        if (!isAssistantMessage(this._messages[index])) {
            return;
        }

        this._messages = produce(this._messages, (draft) => {
            draft[index] = newMessage;
        });
        this._eventManager.publish('messageUpdated', newMessage);
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    getMessages(): Message[] {
        return this._messages;
    }

    getAssistantMessages(): AssistantMessage[] {
        return this._messages.filter(isAssistantMessage);
    }

    getUserMessages(): UserMessage[] {
        return this._messages.filter(isUserMessage);
    }

    resetState() {
        this._messages = [];
        this._eventManager.publish('messagesUpdated', this._messages);
    }

    dispose() {
        this._eventManager.dispose();
    }
}
