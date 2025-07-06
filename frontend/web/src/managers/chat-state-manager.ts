import { produce } from 'immer';
import { DateTime } from 'luxon';
import type { ChatEvent } from '@/data/schemas/chat-events';
import type { ChatState } from '@/data/schemas/chat-state';
import type { ChatSessionError } from '@/data/schemas/errors';
import { type Message, type UserMessage } from '@/data/schemas/messages';
import type { Thread } from '@/data/schemas/threads';
import { EventManager } from '@/utils/event-manager';
import { isAssistantMessage } from '@/utils/message-utils';
import { MessageManager } from './message-manager';
import { RecipeManager } from './recipe-manager';

type ChatStateEvents = {
    chatStateReady: ChatState;
    chatStateChanged: ChatState;
    threadStarted: Thread;
    firstMessageSent: UserMessage;
    currentThreadChanged: { thread_id: string } | null;
    threadResumed: Thread;
    threadTitleUpdated: Thread;
    assistantErrorOccurred: { error_message: string };
    chatSessionErrorOccurred: ChatSessionError;
};

const getInitialChatState = (): ChatState => {
    return {
        isReady: false,
        thread: null,
        threadState: null,
        hasMoreMessages: false,
        nextMessageTimestamp: null,
        isAssistantThinking: false,
        isAssistantResponding: false,
    } satisfies ChatState;
};

export class ChatStateManager {
    private _state: ChatState = getInitialChatState();
    private _eventManager = new EventManager<ChatStateEvents>();

    private _messageManager: MessageManager;
    private _recipeManager: RecipeManager;

    constructor(messageManager: MessageManager, recipeManager: RecipeManager) {
        this._messageManager = messageManager;
        this._recipeManager = recipeManager;
    }

    subscribe<K extends keyof ChatStateEvents>(
        event: K,
        callback: (payload: ChatStateEvents[K]) => void,
    ) {
        this._eventManager.subscribe(event, callback);
    }

    unsubscribe<K extends keyof ChatStateEvents>(
        event: K,
        callback: (payload: ChatStateEvents[K]) => void,
    ) {
        this._eventManager.unsubscribe(event, callback);
    }

    getState(): ChatState {
        return this._state;
    }

    getCurrentThreadId(): string | null {
        return this._state.thread?.id ?? null;
    }

    isStateReady(): boolean {
        return this._state?.isReady ?? false;
    }

    startNewThread() {
        this._state = getInitialChatState();
        this._eventManager.publish('currentThreadChanged', null);
        this._eventManager.publish('chatStateChanged', this._state);
    }

    resumePreviousThread(threadId: string) {
        this._state = getInitialChatState();
        this._eventManager.publish('currentThreadChanged', { thread_id: threadId });
        this._eventManager.publish('chatStateChanged', this._state);
    }

    hasThreadStarted(): boolean {
        return this._state?.threadState === 'started';
    }

    hasThreadResumed(): boolean {
        return this._state?.threadState === 'resumed';
    }

    updateState(updater: (draft: ChatState) => void) {
        this._state = produce(this._state, updater);
        this._eventManager.publish('chatStateChanged', this._state);
        this._eventManager.publish('chatStateReady', this._state);
    }

    handleChatEvent(event: ChatEvent) {
        this.updateState((draft) => {
            switch (event.event) {
                case 'thread_started': {
                    draft.isReady = false;
                    draft.thread = event.data.thread;
                    draft.threadState = 'started';

                    this._messageManager.resetState();
                    this._recipeManager.resetState();

                    this._eventManager.publish('threadStarted', event.data.thread);

                    break;
                }

                case 'thread_resumed': {
                    draft.isReady = true;
                    draft.thread = event.data.thread;
                    draft.threadState = 'resumed';

                    this._messageManager.resetState();
                    this._recipeManager.resetState();

                    const paginatedMessages = event.data.paginated_messages;
                    draft.hasMoreMessages = paginatedMessages.has_more;
                    draft.nextMessageTimestamp = paginatedMessages.next_timestamp;

                    this._messageManager.addMessages(paginatedMessages.messages);
                    this._recipeManager.addRecipes(event.data.recipes);

                    this._eventManager.publish('threadResumed', event.data.thread);
                    break;
                }

                case 'text_message_started': {
                    draft.isAssistantThinking = true; //TODO: Add real thinking, not a simulation
                    draft.thread = event.data.thread;

                    this._messageManager.addMessage(event.data.message);
                    break;
                }

                case 'text_message_chunk_generated': {
                    draft.isAssistantThinking = false;
                    draft.isAssistantResponding = true;
                    draft.thread = event.data.thread;

                    const updatedMessage = event.data.message;
                    if (!isAssistantMessage(updatedMessage)) {
                        return;
                    }
                    this._messageManager.updateAssistantMessage(updatedMessage.id, updatedMessage);

                    break;
                }

                case 'text_message_completed': {
                    draft.isAssistantThinking = false;
                    draft.isAssistantResponding = false;
                    draft.thread = event.data.thread;

                    const updatedMessage = event.data.message;
                    if (!isAssistantMessage(updatedMessage)) {
                        return;
                    }

                    this._messageManager.updateAssistantMessage(updatedMessage.id, updatedMessage);
                    break;
                }

                case 'recipe_generation_started': {
                    draft.thread = event.data.thread;

                    this._messageManager.addMessage(event.data.message);
                    this._recipeManager.addRecipe(event.data.recipe);

                    break;
                }

                case 'recipe_field_detected': {
                    draft.thread = event.data.thread;

                    const updatedMessage = event.data.message;
                    if (isAssistantMessage(updatedMessage)) {
                        this._messageManager.updateAssistantMessage(
                            updatedMessage.id,
                            updatedMessage,
                        );
                    }

                    this._recipeManager.updateRecipe(event.data.recipe);

                    break;
                }

                case 'recipe_generation_completed': {
                    draft.thread = event.data.thread;

                    const updatedMessage = event.data.message;
                    if (isAssistantMessage(updatedMessage)) {
                        this._messageManager.updateAssistantMessage(
                            updatedMessage.id,
                            updatedMessage,
                        );
                    }

                    this._recipeManager.updateRecipe(event.data.recipe);
                    break;
                }

                case 'thread_title_updated': {
                    draft.thread = event.data.thread;
                    this._eventManager.publish('threadTitleUpdated', event.data.thread);
                    break;
                }

                case 'summary_updated': {
                    draft.isReady = true;
                    draft.thread = event.data.thread;
                    break;
                }

                case 'ai_agent_error': {
                    draft.isAssistantThinking = false;
                    draft.isAssistantResponding = false;
                    draft.thread = event.data.thread;

                    this._eventManager.publish('assistantErrorOccurred', {
                        error_message: event.data.error_message,
                    });
                    break;
                }

                case 'chat_session_error': {
                    this._eventManager.publish('chatSessionErrorOccurred', event.data);
                    break;
                }
            }
        });
    }

    createUserMessage(text: string): Message {
        const message: UserMessage = {
            id: crypto.randomUUID(),
            thread_id: this._state.thread?.id ?? '__NEW_THREAD__',
            role: 'user',
            content_type: 'text',
            text_content: text,
            created_at: DateTime.now().toUTC().toISO(),
            updated_at: DateTime.now().toUTC().toISO(),
            recipe_id: null,
            model_name: null,
            input_tokens: null,
            output_tokens: null,
            tool_name: null,
            tool_input: null,
            tool_output: null,
            is_recipe_generation_started: null,
            is_recipe_generation_completed: null,
            parent_id: null,
        };

        this._messageManager.addMessage(message);

        if (this._state.threadState === 'started' && this._state.thread?.is_empty) {
            this._eventManager.publish('firstMessageSent', message);
        }

        this.updateState((draft) => {
            draft.isAssistantThinking = true;
        });

        return message;
    }

    getNextMessageTimestamp(): string | null {
        return this._state.nextMessageTimestamp;
    }

    hasMoreMessages(): boolean {
        return this._state.hasMoreMessages;
    }

    resetState() {
        this._state = getInitialChatState();
        this._messageManager.resetState();
        this._recipeManager.resetState();
        this._eventManager.publish('currentThreadChanged', null);
        this._eventManager.publish('chatStateChanged', this._state);
    }
}
