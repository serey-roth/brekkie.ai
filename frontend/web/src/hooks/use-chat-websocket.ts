import { useCallback, useEffect, useRef, useState } from 'react';
import useWebSocket from 'react-use-websocket';
import { useAppConfig } from '@/context/app-context';
import { ChatEventSchema } from '@/data/schemas/chat-events';
import {
    type ChatSessionError,
    ChatSessionErrorTypesThatDontRequireReconnect,
} from '@/data/schemas/errors';
import { type UserMessagePayload } from '@/data/schemas/messages';
import { ChatStateManager } from '@/managers/chat-state-manager';
import {
    ConnectionStateManager,
    MAX_RECONNECT_ATTEMPTS,
} from '@/managers/connection-state-manager';
import { UserAccessManager } from '@/managers/user-access-manager';

type ChatWebSocketArgs = {
    userAccessManager: UserAccessManager;
    chatStateManager: ChatStateManager;
    connectionStateManager: ConnectionStateManager;
};

const getWebsocketUrl = (
    baseWsUrl: string,
    threadId: string | null,
    token: string,
): string => {
    const url = new URL(threadId ? `${baseWsUrl}/chat/${threadId}` : `${baseWsUrl}/chat`);
    url.searchParams.set('token', token);
    url.searchParams.set('timestamp', Date.now().toString());
    return url.toString();
};

const CLOSE_CODES_TO_NOT_RECONNECT = [
    1000, // Normal closure
    1001, // Going away
    1008, // Policy violation
    1009, // Message size too big
    1011, // Internal server error
];

export function useChatWebSocket(args: ChatWebSocketArgs) {
    const { userAccessManager, chatStateManager, connectionStateManager } = args;
    const websocketUrl = useWebsocketUrl({
        userAccessManager,
        chatStateManager,
        connectionStateManager,
    });
    const unmountedRef = useRef(false);

    useEffect(() => {
        unmountedRef.current = false;
        return () => {
            unmountedRef.current = true;
        };
    }, []);

    const { sendJsonMessage } = useWebSocket(
        websocketUrl,
        {
            shouldReconnect: (closeEvent) => {
                if (unmountedRef.current) {
                    return false;
                }

                const code = closeEvent.code;
                if (CLOSE_CODES_TO_NOT_RECONNECT.includes(code)) {
                    return false;
                }

                const reason = closeEvent.reason;
                if (reason && ChatSessionErrorTypesThatDontRequireReconnect.includes(reason)) {
                    return false;
                }

                const shouldReconnect = connectionStateManager.shouldReconnect();
                if (shouldReconnect) {
                    connectionStateManager.onReconnecting();
                } else {
                    connectionStateManager.onReconnectStop(MAX_RECONNECT_ATTEMPTS);
                }
                return shouldReconnect;
            },
            reconnectAttempts: MAX_RECONNECT_ATTEMPTS,
            onOpen: () => {
                connectionStateManager.onConnectionOpened();
            },
            onClose: () => {
                connectionStateManager.onConnectionClosed();
            },
            onMessage: (event) => {
                const parsed = JSON.parse(event.data);
                const result = ChatEventSchema.safeParse(parsed);
                if (!result.success) {
                    console.error('Invalid event', result.error);
                    return;
                }
                chatStateManager.handleChatEvent(result.data);
            },
            onError: () => {
                connectionStateManager.onConnectionError(
                    'Failed to connect. Please refresh the page.',
                );
            },
            onReconnectStop(numAttempts) {
                connectionStateManager.onReconnectStop(numAttempts);
            },
            reconnectInterval() {
                return connectionStateManager.getReconnectInterval();
            },
            retryOnError: true,
        },
        websocketUrl !== null,
    );

    const sendMessage = useCallback(
        (content: string) => {
            const message = chatStateManager.createUserMessage(content);
            sendJsonMessage({
                id: message.id,
                content,
            } satisfies UserMessagePayload);
        },
        [chatStateManager, sendJsonMessage],
    );

    return { sendMessage };
}

const useWebsocketUrl = (args: {
    userAccessManager: UserAccessManager;
    chatStateManager: ChatStateManager;
    connectionStateManager: ConnectionStateManager;
}) => {
    const { userAccessManager, chatStateManager, connectionStateManager } = args;
    const { wsBaseUrl } = useAppConfig();

    const token = userAccessManager.getJwt();
    const [websocketUrl, setWebsocketUrl] = useState<string | null>(
        token ? getWebsocketUrl(wsBaseUrl, chatStateManager.getCurrentThreadId(), token) : null,
    );
    const hasTriedReconnectingToCurrentThreadRef = useRef(false);

    useEffect(() => {
        const accessEnsuredListener = () => {
            const jwt = userAccessManager.getJwt();
            const threadId = chatStateManager.getCurrentThreadId();
            if (jwt) {
                setWebsocketUrl(getWebsocketUrl(wsBaseUrl, threadId, jwt));
            } else {
                setWebsocketUrl(null);
            }
        };

        const currentThreadChangedListener = (data: { thread_id: string } | null) => {
            const jwt = userAccessManager.getJwt();
            if (jwt) {
                setWebsocketUrl(getWebsocketUrl(wsBaseUrl, data?.thread_id ?? null, jwt));
            } else {
                setWebsocketUrl(null);
            }
            hasTriedReconnectingToCurrentThreadRef.current = false;
        };

        const reconnectingListener = () => {
            const jwt = userAccessManager.getJwt();
            if (!jwt) return;

            const currentThreadId = chatStateManager.getCurrentThreadId();
            if (!currentThreadId) return;

            if (hasTriedReconnectingToCurrentThreadRef.current) {
                setWebsocketUrl(getWebsocketUrl(wsBaseUrl, null, jwt));
            } else {
                hasTriedReconnectingToCurrentThreadRef.current = true;
                setWebsocketUrl(getWebsocketUrl(wsBaseUrl, currentThreadId, jwt));
            }
        };

        const connectionOpenedListener = () => {
            if (hasTriedReconnectingToCurrentThreadRef.current) {
                hasTriedReconnectingToCurrentThreadRef.current = false;
            }
        };

        const chatSessionErrorListener = (error: ChatSessionError) => {
            const jwt = userAccessManager.getJwt();
            if (error.type === 'thread_not_found' && jwt) {
                setWebsocketUrl(getWebsocketUrl(wsBaseUrl, null, jwt));
            }
        };

        userAccessManager.subscribe('accessEnsured', accessEnsuredListener);
        connectionStateManager.subscribe('reconnecting', reconnectingListener);
        connectionStateManager.subscribe('connected', connectionOpenedListener);
        chatStateManager.subscribe('currentThreadChanged', currentThreadChangedListener);
        chatStateManager.subscribe('chatSessionErrorOccurred', chatSessionErrorListener);
        return () => {
            userAccessManager.unsubscribe('accessEnsured', accessEnsuredListener);
            connectionStateManager.unsubscribe('reconnecting', reconnectingListener);
            connectionStateManager.unsubscribe('connected', connectionOpenedListener);
            chatStateManager.unsubscribe('currentThreadChanged', currentThreadChangedListener);
            chatStateManager.unsubscribe('chatSessionErrorOccurred', chatSessionErrorListener);
        };
    }, [chatStateManager, connectionStateManager, userAccessManager, wsBaseUrl]);

    return websocketUrl;
};
