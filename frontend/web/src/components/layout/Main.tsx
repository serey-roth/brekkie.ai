import { useCallback, useEffect, useRef, useState } from 'react';
import { AuthScreen } from '@/components/auth/AuthScreen';
import { MessageTurnList } from '@/components/chat/MessageList';
import { ChatLayout } from '@/components/layout/ChatLayout';
import { WelcomeScreen } from '@/components/layout/WelcomeScreen';
import { RecipePanel } from '@/components/recipes/RecipePanel';
import { useThreadsApiClient, useUserAccessManager } from '@/context/app-context';
import { useAuth, useAuthModal } from '@/context/auth-context';
import { useChatContext, useChatStateManager, useConnectionStateManager, useMessageManager, useRecipeManager } from '@/context/chat-context';
import type { ChatState } from '@/data/schemas/chat-state';
import type { ConnectionState } from '@/data/schemas/connection-state';
import type { ChatLimitMessage, ChatSessionError } from '@/data/schemas/errors';
import type { Message, RoleMessageGroup } from '@/data/schemas/messages';
import type { Thread } from '@/data/schemas/threads';
import type { UserAccessData } from '@/data/schemas/user-access';
import { groupMessagesByRole } from '@/utils/message-utils';
import { RecipeListView } from './RecipeListView';
import { Sidebar } from './Sidebar';

export function Main() {
    const [selectedRecipeId, setSelectedRecipeId] = useState<string | null>(null);
    const [showRecipeListView, setShowRecipeListView] = useState(false);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);
    const [scrollToBottomMessage, setScrollToBottomMessage] = useState<string | null>(null);

    const userAccessManager = useUserAccessManager();
    const { isAuthModalOpen, openAuthModal, closeAuthModal } = useAuthModal();
    const { signin, signup } = useAuth();
    
    const connectionState = useConnectionState();
    
    const { sendMessage } = useChatContext();
    const { isLoadingMoreMessages, errorLoadingMoreMessages, loadingMessage, loadMorePreviousMessages } = useLoadChatPreviousMessages();

    const scrollRef = useRef<HTMLDivElement | null>(null);

    const scrollToBottom = useCallback(() => {
        const container = scrollRef.current
        if (!container) return;
        requestAnimationFrame(() => {
            container.scrollTo({
                top: container.scrollHeight,
                behavior: 'smooth',
            });
        });
    }, []);


    // TODO: Auto scroll to bottom should happens once at the beginning and message change when no manual scroll happens
    const { currentChatState, chatSessionErrorMessage, threadTitle, resetChatState } = useChatState({ onThreadResumed: scrollToBottom });
    const { chatLimitMessage } = useChatLimit();

    useScrollHandler({
        scrollRef,
        onLoadMore: useCallback(() => {
            loadMorePreviousMessages();
        }, [loadMorePreviousMessages]),
        onDistanceFromBottomChange: useCallback((distance: number) => {
            if (distance > 250) {
                setScrollToBottomMessage('Scroll to bottom'); // TODO: Would be nice to calculate the actual distance from the last message
            } else {
                setScrollToBottomMessage(null);
            }
        }, [])
    });

    const { messageGroups } = useChatMessageGroups({ onMessageChange: useCallback(() => {
        const container = scrollRef.current;
        if (!container) return;
        const distanceFromBottom =
            container.scrollHeight - container.scrollTop - container.clientHeight;

        if (distanceFromBottom <= 250) {
            scrollToBottom();
        } else {
            setScrollToBottomMessage("New message");
        }
    }, [scrollRef, scrollToBottom]) });
        
    return (
        <div className="bg-background min-h-screen px-safe pb-safe pt-safe">
            <Sidebar 
                isOpen={isSidebarOpen} 
                openSidebar={() => setIsSidebarOpen(true)} 
                closeSidebar={() => setIsSidebarOpen(false)} 
                showRecipeListView={() => setShowRecipeListView(true)} 
                hideRecipeListView={() => setShowRecipeListView(false)} 
            />
            
            <div
                className={`bg-background grid min-h-screen overflow-hidden transition-all duration-300 ${
                    selectedRecipeId ? 'lg:grid-cols-2' : 'lg:grid-cols-1'
                } ${isSidebarOpen ? 'md:ml-16 lg:ml-[20rem]' : 'md:ml-16'}`}
            >
                {showRecipeListView ? (
                    <RecipeListView
                        selectedRecipeId={selectedRecipeId}
                        isRecipePanelOpen={selectedRecipeId !== null}
                        onSelectRecipe={setSelectedRecipeId}
                    />
                ) : (
                <ChatLayout
                    scrollRef={scrollRef}
                    selectedRecipeId={selectedRecipeId}
                    scrollToBottomMessage={scrollToBottomMessage}
                    onScrollToBottom={scrollToBottom}
                    onSendMessage={sendMessage}
                    connectionState={connectionState}
                    isAuthenticated={userAccessManager.isAuthenticated() ?? false}
                    chatLimitMessage={chatLimitMessage ?? undefined}
                    chatSessionErrorMessage={chatSessionErrorMessage ?? undefined}
                    disableSendButton={!currentChatState || isLoadingMoreMessages || !connectionState.isConnected}
                    onSignIn={openAuthModal}
                    threadTitle={threadTitle}
                >
                    {messageGroups.length > 0 ? (
                        <MessageTurnList
                            messageGroups={messageGroups}
                            isLoadingMoreMessages={isLoadingMoreMessages}
                            isAssistantThinking={currentChatState?.isAssistantThinking ?? false}
                            isAssistantResponding={currentChatState?.isAssistantResponding ?? false}
                            selectedRecipeId={selectedRecipeId}
                            onSelectRecipe={setSelectedRecipeId}
                            errorLoadingMoreMessages={errorLoadingMoreMessages}
                            loadingMessage={loadingMessage}
                        />
                    ) : (
                        <WelcomeScreen onSendMessage={sendMessage} disabled={connectionState.status !== 'connected'} />
                    )}
                    </ChatLayout>
                )}
                <RecipePanel
                    selectedRecipeId={selectedRecipeId}
                    isSidebarOpen={isSidebarOpen}
                    onClose={() => setSelectedRecipeId(null)}
                />
            </div>

            <AuthScreen
                isOpen={isAuthModalOpen}
                onClose={closeAuthModal}
                onSignIn={async (payload) => {
                    await signin(payload);
                    resetChatState();
                }}
                onSignUp={async (payload) => {
                    await signup(payload);
                    resetChatState();
                }}
            />
        </div>
    );
}

// TODO: Fix this. Distinguish user scroll and programmatic scroll with onWheel deltas.
function useScrollHandler({ scrollRef, onLoadMore, onDistanceFromBottomChange }: {
    scrollRef: React.RefObject<HTMLDivElement | null>;
    onDistanceFromBottomChange: (distance: number) => void;
    onLoadMore?: () => void;
}) {
    useEffect(() => {
        const container = scrollRef.current;
        if (!container) return;

        let loadMoreTimeout: NodeJS.Timeout;

        const handleScroll = () => {
            const distanceFromBottom =
                container.scrollHeight - container.scrollTop - container.clientHeight;

            onDistanceFromBottomChange(distanceFromBottom);

            if (container.scrollTop === 0 && onLoadMore) {
                clearTimeout(loadMoreTimeout);  
                loadMoreTimeout = setTimeout(() => {
                    onLoadMore();
                }, 1000);
            }
        };

        container.addEventListener('scroll', handleScroll);
        return () => {
            clearTimeout(loadMoreTimeout);      
            container.removeEventListener('scroll', handleScroll);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [onLoadMore, onDistanceFromBottomChange]);
}

function useChatState({ onThreadResumed }: {
    onThreadResumed: () => void;
}) {
    const chatStateManager = useChatStateManager();

    const [currentChatState, setCurrentChatState] = useState(chatStateManager.getState());
    const [chatSessionErrorMessage, setChatSessionErrorMessage] = useState<string | null>(null);
    const [threadTitle, setThreadTitle] = useState<string | null>(chatStateManager.getState().thread?.title ?? (chatStateManager.getState().thread?.is_empty === false ? 'New chat' : null));

    useEffect(() => {
        const chatStateReadyListener = (state: ChatState) => {
            setCurrentChatState(state);
            setThreadTitle(state.thread?.title ?? (state.thread?.is_empty === false ? 'New chat' : null));
        };
        const chatStateChangedListener = (state: ChatState) => {
            setCurrentChatState(state);
            setThreadTitle(state.thread?.title ?? (state.thread?.is_empty === false ? 'New chat' : null));
        };
        const threadResumedListener = () => {
            onThreadResumed();
        }
        const chatSessionErrorOccurredListener = (error: ChatSessionError) => {
            if (error.type === 'over_message_limit') {
                // We handle this in the useMessageLimit hook
                setChatSessionErrorMessage(null); 
            } else {
                setChatSessionErrorMessage(error.message);
            }
        }
        const threadTitleUpdatedListener = (thread: Thread) => setThreadTitle(thread.title ?? (thread.is_empty === false ? 'New chat' : null));

        chatStateManager.subscribe('chatStateReady', chatStateReadyListener);
        chatStateManager.subscribe('chatStateChanged', chatStateChangedListener);
        chatStateManager.subscribe('threadResumed', threadResumedListener);
        chatStateManager.subscribe('threadTitleUpdated', threadTitleUpdatedListener);
        chatStateManager.subscribe('chatSessionErrorOccurred', chatSessionErrorOccurredListener);
        return () => {
            chatStateManager.unsubscribe('chatStateReady', chatStateReadyListener);
            chatStateManager.unsubscribe('chatStateChanged', chatStateChangedListener);
            chatStateManager.unsubscribe('threadResumed', threadResumedListener);
            chatStateManager.unsubscribe('threadTitleUpdated', threadTitleUpdatedListener);
            chatStateManager.unsubscribe('chatSessionErrorOccurred', chatSessionErrorOccurredListener);
        };
    }, [chatStateManager, onThreadResumed]);

    const resetChatState = useCallback(() => {
        chatStateManager.resetState();
    }, [chatStateManager]);

    return { currentChatState, chatSessionErrorMessage, threadTitle, resetChatState };
}   

function useChatMessageGroups({ onMessageChange }: {
    onMessageChange: () => void;
}) {
    const messageManager = useMessageManager();
    const [messageGroups, setMessageGroups] = useState<RoleMessageGroup[]   >(groupMessagesByRole(messageManager.getMessages()));

    useEffect(() => {
        const messageAddedListener = () => {
            onMessageChange();
        }
        const messageUpdatedListener = () => {
            onMessageChange();
        }
        const messagesUpdatedListener = (messages: Message[]) => {
            setMessageGroups(groupMessagesByRole(messages));
        }
        messageManager.subscribe('messageAdded', messageAddedListener);
        messageManager.subscribe('messageUpdated', messageUpdatedListener);
        messageManager.subscribe('messagesUpdated', messagesUpdatedListener);
        return () => {
            messageManager.unsubscribe('messageAdded', messageAddedListener);
            messageManager.unsubscribe('messageUpdated', messageUpdatedListener);
            messageManager.unsubscribe('messagesUpdated', messagesUpdatedListener);
        };
    }, [messageManager, onMessageChange]);
    
    return { messageGroups };
}

function useChatLimit() {
    const chatStateManager = useChatStateManager();
    const userAccessManager = useUserAccessManager();
    const [chatLimitMessage, setChatLimitMessage] = useState<ChatLimitMessage | null>(null);

    useEffect(() => {
        const limitReachedListener = (error: ChatSessionError) => {
            if (error.type === 'over_message_limit') {
                setChatLimitMessage({
                    type: 'error',
                    message: error.message,
                });
            }
        }

        const createLimitMessage = (limit: number, messageCount: number, isAuthenticated: boolean) => {
            if (messageCount >= limit) {
                return `You've reached your limit of ${limit} messages.${isAuthenticated ? ' Paid plans with higher limits are coming soon.' : ''}`;
            } else if (isAuthenticated && messageCount > 0 && Math.abs(messageCount - limit) < 10) {
                return `You have ${limit - messageCount} messages left.`;
            } else if (!isAuthenticated && messageCount > 0) {
                return `You have ${limit - messageCount} messages left.`;
            }
            return null;
        }
        
        const accessEnsuredListener = (userAccessData: UserAccessData) => {
            const limit = userAccessManager.getMessageLimit();
            const isAuthenticated = userAccessData.is_authenticated;
            const messageCount = userAccessData.user_message_count;
            const limitMessage = createLimitMessage(limit, messageCount, isAuthenticated);
            if (limitMessage) {
                setChatLimitMessage({ type: 'warning', message: limitMessage });
            }
        }
        const accessChangedListener = (userAccessData: UserAccessData | null) => {
            if (userAccessData) {
                const limit = userAccessManager.getMessageLimit();
                const isAuthenticated = userAccessData.is_authenticated;
                const messageCount = userAccessData.user_message_count;
                const limitMessage = createLimitMessage(limit, messageCount, isAuthenticated);
                if (limitMessage) {
                    setChatLimitMessage({ type: 'warning', message: limitMessage });
                }
            } 
        }

        userAccessManager.subscribe('accessEnsured', accessEnsuredListener);
        userAccessManager.subscribe('accessChanged', accessChangedListener);
        chatStateManager.subscribe('chatSessionErrorOccurred', limitReachedListener);
        return () => {
            userAccessManager.unsubscribe('accessEnsured', accessEnsuredListener);
            userAccessManager.unsubscribe('accessChanged', accessChangedListener);
            chatStateManager.unsubscribe('chatSessionErrorOccurred', limitReachedListener);
        };
    }, [userAccessManager, chatStateManager]);

    return { chatLimitMessage };
}

function useConnectionState() {
    const connectionStateManager = useConnectionStateManager();
    const [connectionState, setConnectionState] = useState<ConnectionState>(connectionStateManager.getState());

    useEffect(() => {
        const stateChangedListener = (state: ConnectionState) => setConnectionState(state);
        connectionStateManager.subscribe('stateChanged', stateChangedListener);
        return () => {
            connectionStateManager.unsubscribe('stateChanged', stateChangedListener);
        };
    }, [connectionStateManager]);

    return connectionState;
}

const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY_MS = 1000;
const MAX_RETRY_DELAY_MS = 8000;

const getRetryDelay = (retryCount: number) => {
    // Exponential backoff with jitter: 2^retryCount * INITIAL_RETRY_DELAY_MS
    const exponentialDelay = Math.min(
        INITIAL_RETRY_DELAY_MS * Math.pow(2, retryCount),
        MAX_RETRY_DELAY_MS
    );
    // Add some random jitter (±20%) to prevent thundering herd
    const jitter = exponentialDelay * 0.2;
    return exponentialDelay + (Math.random() * jitter * 2 - jitter);
};

function useLoadChatPreviousMessages() {
    const [isChatStateReady, setIsChatStateReady] = useState(false);
    const [isLoadingMoreMessages, setIsLoadingMoreMessages] = useState(false);
    const [loadingMessage, setLoadingMessage] = useState<string | null>(null);
    const [errorLoadingMoreMessages, setErrorLoadingMoreMessages] = useState<string | null>(null);
    
    const retryCountRef = useRef(0);

    const userAccessManager = useUserAccessManager();
    const chatStateManager = useChatStateManager();
    const messageManager = useMessageManager();
    const recipeManager = useRecipeManager();
    const threadsClient = useThreadsApiClient();

    const loadMorePreviousMessages = useCallback(async () => {
        if (!isChatStateReady) {
            return;
        }

        if (!chatStateManager.hasMoreMessages()) {
            setIsLoadingMoreMessages(false);
            return;
        }

        if (retryCountRef.current >= MAX_RETRIES) {
            // We need to reset the loading state since we're calling this recursively
            setIsLoadingMoreMessages(false);
            return;
        }

        const accessToken = userAccessManager.getAccessToken();
        if (!accessToken) return;

        const threadId = chatStateManager.getCurrentThreadId();
        if (!threadId) return;

        setIsLoadingMoreMessages(true);
        setLoadingMessage('Loading more messages...');
        setErrorLoadingMoreMessages(null);

        try {
            const result = await threadsClient.getThreadMessages({
                thread_id: threadId,
                limit: 50,
                from_timestamp: chatStateManager.getNextMessageTimestamp(),
                sort_by: 'created_at',
                sort_order: 'desc',
            }, accessToken);

            messageManager.prependMessages(result.paginated_messages.messages);
            chatStateManager.updateState(draft => {
                draft.nextMessageTimestamp = result.paginated_messages.next_timestamp;
                draft.hasMoreMessages = result.paginated_messages.has_more;
            });
            recipeManager.addRecipes(result.recipes);

            // Reset retry count on success
            retryCountRef.current = 0;
            setLoadingMessage(null);
            setIsLoadingMoreMessages(false);
        } catch (error) {
            console.error('Failed to load more messages:', error);
            retryCountRef.current += 1;
            
            if (retryCountRef.current < MAX_RETRIES) {
                const delay = getRetryDelay(retryCountRef.current);
                const delaySeconds = Math.round(delay / 1000);
                setLoadingMessage(`Failed to load messages. Retrying in ${delaySeconds} seconds...`);
                setTimeout(() => {
                    loadMorePreviousMessages();
                }, delay);
            } else {
                setLoadingMessage(null);
                setErrorLoadingMoreMessages('Failed to load messages after multiple attempts. Please try again later.');
                setIsLoadingMoreMessages(false);
            }
        }
    }, [threadsClient, chatStateManager, messageManager, userAccessManager, recipeManager, isChatStateReady]);

    useEffect(() => {
        const resetState = () => {
            setIsLoadingMoreMessages(false);
            setLoadingMessage(null);
            setErrorLoadingMoreMessages(null);
            retryCountRef.current = 0;
        };

        const chatStateChangedListener = () => {
            resetState();
            setIsChatStateReady(false);
        };
        const chatStateReadyListener = () => setIsChatStateReady(true);

        chatStateManager.subscribe('chatStateChanged', chatStateChangedListener);
        chatStateManager.subscribe('chatStateReady', chatStateReadyListener);
        return () => {
            chatStateManager.unsubscribe('chatStateChanged', chatStateChangedListener);
            chatStateManager.unsubscribe('chatStateReady', chatStateReadyListener);
        };
    }, [userAccessManager, chatStateManager]);

    return {
        isLoadingMoreMessages,
        loadingMessage,
        errorLoadingMoreMessages,
        loadMorePreviousMessages,
    };
}
