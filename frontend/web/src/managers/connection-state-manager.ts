import { produce } from 'immer';
import type { ConnectionState, ConnectionStatus } from '@/data/schemas/connection-state';
import { EventManager } from '@/utils/event-manager';

type ConnectionEvents = {
    stateChanged: Readonly<ConnectionState>;
    reconnecting: void;
    connecting: void;
    connected: void;
    disconnected: void;
    error: string | null;
};

export const MAX_RECONNECT_ATTEMPTS = 10;
export const INITIAL_RECONNECT_INTERVAL = 1000;
export const MAX_RECONNECT_INTERVAL = 30000;

function getInitialConnectionState(): ConnectionState {
    return {
        status: 'idle',
        errorMessage: null,
        isConnecting: false,
        isConnected: false,
        isReconnecting: false,
        reconnectAttempts: 0,
    };
}

export class ConnectionStateManager {
    private _state: ConnectionState;
    private _eventManager = new EventManager<ConnectionEvents>();

    constructor() {
        this._state = getInitialConnectionState();
    }

    getState(): Readonly<ConnectionState> {
        return Object.freeze(this._state);
    }

    getStatus(): Readonly<ConnectionStatus> {
        return Object.freeze(this._state.status);
    }

    getReconnectAttempts(): number {
        return this._state.reconnectAttempts;
    }

    subscribe<K extends keyof ConnectionEvents>(
        event: K,
        callback: (payload: ConnectionEvents[K]) => void,
    ) {
        this._eventManager.subscribe(event, callback);
    }

    unsubscribe<K extends keyof ConnectionEvents>(
        event: K,
        callback: (payload: ConnectionEvents[K]) => void,
    ) {
        this._eventManager.unsubscribe(event, callback);
    }

    updateState(updater: (draft: ConnectionState) => void) {
        this._state = produce(this._state, updater);
        this._eventManager.publish('stateChanged', Object.freeze(this._state));
    }

    shouldReconnect(): boolean {
        return this._state.reconnectAttempts < MAX_RECONNECT_ATTEMPTS;
    }

    onReconnecting() {
        this.updateState((draft) => {
            draft.status = 'reconnecting';
            draft.isReconnecting = true;
            draft.reconnectAttempts++;
        });
        this._eventManager.publish('reconnecting', undefined);
    }

    onConnectionOpened() {
        this.updateState((draft) => {
            draft.status = 'connected';
            draft.isConnected = true;
            draft.isConnecting = false;
            draft.isReconnecting = false;
            draft.errorMessage = null;
            draft.reconnectAttempts = 0;
        });
        this._eventManager.publish('connected', undefined);
    }

    onConnectionClosed() {
        this.updateState((draft) => {
            draft.status = 'disconnected';
            draft.isConnected = false;
            draft.isConnecting = false;
            draft.isReconnecting = false;
            draft.errorMessage = null;
            draft.reconnectAttempts++;
        });
        this._eventManager.publish('disconnected', undefined);
    }

    onConnectionError(errorMessage: string | null) {
        this.updateState((draft) => {
            draft.errorMessage = errorMessage;
        });
        this._eventManager.publish('error', errorMessage);
    }

    onReconnectStop(numAttempts: number) {
        this.updateState((draft) => {
            draft.status = 'disconnected';
            draft.isConnecting = false;
            draft.isConnected = false;
            draft.isReconnecting = false;
            draft.errorMessage = `Maximum number of reconnect attempts (${numAttempts}) reached. Please refresh the page.`;
            draft.reconnectAttempts = numAttempts;
        });
        this._eventManager.publish(
            'error',
            `Maximum number of reconnect attempts (${numAttempts}) reached. Please refresh the page.`,
        );
    }

    getReconnectInterval(): number {
        // Implement exponential backoff with jitter
        const baseDelay = Math.min(
            INITIAL_RECONNECT_INTERVAL * Math.pow(2, this._state.reconnectAttempts),
            MAX_RECONNECT_INTERVAL,
        );
        // Add jitter to prevent thundering herd problem
        const jitter = Math.random() * 1000;
        return baseDelay + jitter;
    }

    resetState() {
        this._state = getInitialConnectionState();
    }

    dispose() {
        this._eventManager.dispose();
    }
}
