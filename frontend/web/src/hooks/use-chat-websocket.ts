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
    accessToken: string | null,
    threadId: string | null,
): string | null => {
    if (accessToken === null) {
        return null;
    }
    const timestamp = Date.now();
    return threadId
        ? `${baseWsUrl}/chat/${threadId}?access_token=${accessToken}&timestamp=${timestamp}`
        : `${baseWsUrl}/chat?access_token=${accessToken}&timestamp=${timestamp}`;
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
                if ('user_access_data' in result.data.data) {
                    const userAccessData = result.data.data.user_access_data;
                    userAccessManager.setUserAccessData(userAccessData);
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
            retryOnError: true, // This will used the reconnectAttempts too
        },
        !!websocketUrl,
    );

    const sendMessage = useCallback(
        (content: string) => {
            const message = chatStateManager.createUserMessage(content);
            userAccessManager.optimisticIncrementUserMessageCount();
            sendJsonMessage({
                id: message.id,
                content,
            } satisfies UserMessagePayload);
        },
        [chatStateManager, userAccessManager, sendJsonMessage],
    );

    return { sendMessage };
}

const useWebsocketUrl = (args: {
    userAccessManager: UserAccessManager;
    chatStateManager: ChatStateManager;
    connectionStateManager: ConnectionStateManager;
}) => {
    const { userAccessManager, chatStateManager, connectionStateManager } = args;

    const config = useAppConfig();

    const [websocketUrl, setWebsocketUrl] = useState<string | null>(
        getWebsocketUrl(
            config.wsBaseUrl,
            userAccessManager.getAccessToken(),
            chatStateManager.getCurrentThreadId(),
        ),
    );
    const hasTriedReconnectingToCurrentThreadRef = useRef(false);

    useEffect(() => {
        const accessEnsuredListener = () => {
            const accessToken = userAccessManager.getAccessToken();
            const threadId = chatStateManager.getCurrentThreadId();
            setWebsocketUrl(getWebsocketUrl(config.wsBaseUrl, accessToken, threadId));
        };

        const currentThreadChangedListener = (data: { thread_id: string } | null) => {
            const accessToken = userAccessManager.getAccessToken();
            setWebsocketUrl(
                getWebsocketUrl(config.wsBaseUrl, accessToken, data?.thread_id ?? null),
            );
            // Reset the reconnection flag when thread changes
            hasTriedReconnectingToCurrentThreadRef.current = false;
        };

        const reconnectingListener = () => {
            const accessToken = userAccessManager.getAccessToken();
            if (!accessToken) {
                return;
            }

            const currentThreadId = chatStateManager.getCurrentThreadId();
            if (!currentThreadId) {
                // If we don't have a thread id, there's no point in reconnecting
                return;
            }

            if (hasTriedReconnectingToCurrentThreadRef.current) {
                // First attempt to reconnect to the same thread failed due to thread not found/thread expired
                // Start a new thread instead
                setWebsocketUrl(getWebsocketUrl(config.wsBaseUrl, accessToken, null));
            } else {
                hasTriedReconnectingToCurrentThreadRef.current = true;
                setWebsocketUrl(getWebsocketUrl(config.wsBaseUrl, accessToken, currentThreadId));
            }
        };

        const connectionOpenedListener = () => {
            if (hasTriedReconnectingToCurrentThreadRef.current) {
                hasTriedReconnectingToCurrentThreadRef.current = false;
            }
        };

        const chatSessionErrorListener = (error: ChatSessionError) => {
            if (error.type === 'thread_not_found') {
                setWebsocketUrl(
                    getWebsocketUrl(config.wsBaseUrl, userAccessManager.getAccessToken(), null),
                );
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
    }, [chatStateManager, connectionStateManager, userAccessManager, config.wsBaseUrl]);

    return websocketUrl;
};
