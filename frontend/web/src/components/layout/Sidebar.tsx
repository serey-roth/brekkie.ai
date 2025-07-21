import { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import {
    LuPanelLeftClose,
    LuMessageSquare,
    LuMessageSquarePlus,
    LuLogOut,
    LuLogIn,
    LuMessageSquareWarning,
    LuArrowRightFromLine,
    LuArrowLeftFromLine,
    LuMessageSquareX,
    LuUtensils,
} from 'react-icons/lu';
import {
    useAppConfig,
    useAppState,
    useThreadsApiClient,
    useUserAccessManager,
} from '@/context/app-context';
import { useChatStateManager } from '@/context/chat-context';
import type { ChatState } from '@/data/schemas/chat-state';
import type { ChatSessionError } from '@/data/schemas/errors';
import { type Thread } from '@/data/schemas/threads';
import { type UserAccess } from '@/data/schemas/user-access';
import { useAuth } from '@/hooks/useAuth';
import { getThreadGroups, formatThreadTimestamp } from '@/utils/thread-utils';

interface SidebarProps {
    showRecipeListView: () => void;
    hideRecipeListView: () => void;
}

export function Sidebar(props: SidebarProps) {
    const { showRecipeListView, hideRecipeListView } = props;
    const { isSidebarOpen: isOpen, openSidebar, closeSidebar } = useAppState();
    const { featureFlags } = useAppConfig();
    const { login, logout, isAuthenticated } = useAuth();
    const userAccessManager = useUserAccessManager();
    const userAccess = useUserAccess();
    const { hasLimitReached } = useChatLimit();
    const { currentThreadId, startThread, resumeThread, resetCurrentThread } = useCurrentThread();
    const { threadGroups, isFetching, error, fetchMoreObserverTarget } = useFetchThreads(
        isOpen,
        userAccess,
    );

    return (
        <>
            {!isOpen && (
                <div className="fixed top-4 left-4 z-50 flex flex-row gap-2 md:hidden">
                    <button
                        onClick={openSidebar}
                        className="text-contrast hover:text-primary bg-background/95 focus:ring-primary/20 border-border flex h-10 w-10 items-center justify-center rounded-xl border shadow-lg backdrop-blur-sm transition-transform duration-150 hover:scale-102 focus:ring-2 focus:outline-none active:scale-98"
                    >
                        <LuPanelLeftClose size={20} />
                    </button>
                </div>
            )}

            {isOpen && (
                <div
                    onClick={closeSidebar}
                    className="bg-contrast/20 fixed inset-0 z-40 backdrop-blur-[1px] md:hidden"
                />
            )}

            <div
                className={`bg-background/95 border-border fixed top-0 left-0 z-40 flex h-screen flex-col border-r shadow-lg backdrop-blur-sm transition-[transform,width] duration-250 ease-in-out ${isOpen ? 'w-80 translate-x-0' : 'w-16 -translate-x-full md:translate-x-0'}`}
            >
                <div className={`mt-4 flex items-center ${isOpen ? 'mx-4' : 'mx-auto'}`}>
                    {isOpen && (
                        <div className="flex flex-1 flex-row items-center gap-2">
                            <span className="text-contrast ml-3 text-xl font-bold whitespace-nowrap">
                                brekkie.ai
                            </span>
                            <span className="text-contrast-subtle bg-primary/20 rounded-full px-2 py-0.5 text-xs font-semibold">
                                beta
                            </span>
                        </div>
                    )}
                    <button
                        onClick={isOpen ? closeSidebar : openSidebar}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center justify-center rounded-xl border border-transparent p-2 transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                    >
                        {isOpen ? (
                            <LuArrowLeftFromLine size={20} />
                        ) : (
                            <LuArrowRightFromLine size={20} />
                        )}
                    </button>
                </div>

                <div className={`mt-2 flex items-center ${isOpen ? 'mx-4' : 'mx-auto'}`}>
                    <button
                        onClick={() => {
                            showRecipeListView();
                            if (isOpen) {
                                closeSidebar();
                            }
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 items-center rounded-xl border border-transparent transition-transform duration-150 hover:scale-102 focus:ring-0 focus:outline-none active:scale-98 md:flex ${!isOpen ? 'md:bg-primary/10 w-10' : 'w-full'}`}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 items-center justify-center">
                            <LuUtensils size={20} />
                        </div>
                        {isOpen && <span className="whitespace-nowrap">Recipes</span>}
                    </button>
                </div>

                <div
                    className={`mt-2 flex items-center ${isOpen ? 'mx-4' : 'mx-auto'} ${hasLimitReached ? 'pointer-events-none cursor-not-allowed opacity-50' : ''}`}
                >
                    <button
                        disabled={hasLimitReached}
                        onClick={() => {
                            startThread();
                            hideRecipeListView();
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 items-center rounded-xl border border-transparent transition-transform duration-150 hover:scale-102 focus:ring-0 focus:outline-none active:scale-98 md:flex ${!isOpen ? 'md:bg-primary/10 w-10' : 'w-full'}`}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 items-center justify-center">
                            <LuMessageSquarePlus size={20} />
                        </div>
                        {isOpen && <span className="whitespace-nowrap">New Chat</span>}
                    </button>
                </div>

                <div className="flex-1 overflow-hidden">
                    {isOpen && threadGroups.length > 0 && (
                        <div className="mt-2 flex flex-row items-center justify-between px-6">
                            <h2 className="text-contrast text-sm tracking-wider">Recent chats</h2>
                            <div className="text-contrast-subtle text-xs opacity-80">
                                Sorted by last activity
                            </div>
                        </div>
                    )}
                    <div className="h-full overflow-y-auto px-4 pt-4 pb-8">
                        {isOpen && threadGroups.length === 0 && !isFetching && !error && (
                            <div className="text-contrast-subtle py-8 text-center text-sm">
                                <div className="mb-2">
                                    <LuMessageSquareX
                                        size={32}
                                        className="text-primary/60 mx-auto"
                                    />
                                </div>
                                <p className="mx-auto max-w-[240px] font-medium">
                                    No chats yet. Milo's waiting whenever you're ready.
                                </p>
                            </div>
                        )}
                        {isOpen && error && (
                            <div className="text-contrast-subtle flex flex-col items-center justify-center gap-1 py-8 text-center text-sm">
                                <div className="mb-2">
                                    <LuMessageSquareWarning
                                        size={32}
                                        className="text-primary/60 mx-auto"
                                    />
                                </div>
                                <p className="max-w-[240px] font-medium">
                                    <span className="text-sm">Hmm, something went wrong...</span>
                                    <br />
                                    <span className="text-xs">
                                        We're currently working on it. Please come back a little bit
                                        later.
                                    </span>
                                </p>
                            </div>
                        )}
                        {isOpen &&
                            threadGroups.map((group, index) => (
                                <div
                                    key={group.label}
                                    className={`${index < threadGroups.length - 1 ? 'mb-3' : ''}`}
                                >
                                    <h3
                                        className={`text-contrast-subtle mx-2 mb-2 text-sm tracking-wider`}
                                    >
                                        {group.label}
                                    </h3>
                                    <div className="space-y-0.5">
                                        {group.items.map((thread) => (
                                            <button
                                                key={thread.id}
                                                onClick={() => {
                                                    if (currentThreadId !== thread.id) {
                                                        resumeThread(thread.id);
                                                    }
                                                    hideRecipeListView();
                                                }}
                                                className={`hover:bg-primary/10 hover:border-primary/20 flex w-full items-center gap-2 rounded-xl border border-transparent p-1 text-left text-sm transition-transform duration-150 hover:scale-102 active:scale-98 sm:p-2 ${currentThreadId === thread.id ? 'bg-primary/10 border-primary/50 hover:bg-primary/20' : ''}`}
                                            >
                                                <div className="bg-primary/10 flex h-8 w-8 items-center justify-center rounded-full">
                                                    <LuMessageSquare
                                                        size={16}
                                                        className="text-primary/80"
                                                    />
                                                </div>
                                                <div className="ml-2 min-w-0 flex-1">
                                                    <div className="text-contrast truncate font-medium">
                                                        {thread.title ?? 'New Chat'}
                                                    </div>
                                                    <div className="text-contrast-subtle text-xs italic">
                                                        {formatThreadTimestamp(thread.updated_at)}
                                                    </div>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            ))}
                        <div
                            ref={fetchMoreObserverTarget}
                            className="flex h-4 items-center justify-center"
                        >
                            {isOpen && isFetching && (
                                <div className="text-contrast-subtle flex items-center gap-2 text-sm">
                                    <div className="border-primary/20 border-t-primary h-4 w-4 animate-spin rounded-full border-2" />
                                    <span>Loading more chats...</span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {featureFlags.enableAuth && (
                    <div
                        className={`mt-2 mb-4 flex flex-shrink-0 items-center gap-2 ${isOpen ? 'mx-4' : 'mx-auto'}`}
                    >
                        {!isAuthenticated && (
                            <button
                                onClick={async () => {
                                    await login();
                                }}
                                className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 items-center rounded-xl border border-transparent transition-transform duration-150 hover:scale-102 focus:ring-0 focus:outline-none active:scale-98 md:flex ${!isOpen ? 'md:bg-primary/10 w-10' : 'w-full'}`}
                                tabIndex={0}
                            >
                                <div className="flex w-10 items-center justify-center">
                                    <LuLogIn size={20} />
                                </div>
                                {isOpen && (
                                    <span className="whitespace-nowrap">
                                        Sign in to save your chats
                                    </span>
                                )}
                            </button>
                        )}

                        {isAuthenticated && (
                            <button
                                onClick={async () => {
                                    try {
                                        await logout(window.location.origin);
                                        await userAccessManager.createAnonymousAccess();
                                        resetCurrentThread();
                                    } catch (error) {
                                        console.error('Logout failed:', error);
                                    }
                                }}
                                className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 items-center rounded-xl border border-transparent transition-transform duration-150 hover:scale-102 focus:ring-0 focus:outline-none active:scale-98 md:flex ${!isOpen ? 'md:bg-primary/10 w-10' : 'w-full'}`}
                                tabIndex={0}
                            >
                                <div className="flex w-10 items-center justify-center">
                                    <LuLogOut size={20} />
                                </div>
                                {isOpen && (
                                    <span className="text-base whitespace-nowrap">Sign out</span>
                                )}
                            </button>
                        )}
                    </div>
                )}
            </div>
        </>
    );
}

const useUserAccess = () => {
    const userAccessManager = useUserAccessManager();
    const [userAccess, setUserAccess] = useState<UserAccess | null>(
        userAccessManager.getUserAccess(),
    );

    useEffect(() => {
        const accessEnsuredListener = (userAccess: UserAccess) => setUserAccess(userAccess);
        const accessChangedListener = (userAccess: UserAccess | null) => setUserAccess(userAccess);
        userAccessManager.subscribe('accessEnsured', accessEnsuredListener);
        userAccessManager.subscribe('accessChanged', accessChangedListener);
        return () => {
            userAccessManager.unsubscribe('accessEnsured', accessEnsuredListener);
            userAccessManager.unsubscribe('accessChanged', accessChangedListener);
        };
    }, [userAccessManager]);

    return userAccess;
};

function useChatLimit() {
    const chatStateManager = useChatStateManager();
    const userAccessManager = useUserAccessManager();
    const [hasLimitReached, setHasLimitReached] = useState(false);

    const { featureFlags } = useAppConfig();

    useEffect(() => {
        const limitReachedListener = (error: ChatSessionError) => {
            if (error.type === 'over_message_limit') {
                setHasLimitReached(true);
            }
        };

        const accessEnsuredListener = (userAccess: UserAccess) => {
            const limit = userAccessManager.getMessageLimit();
            const messageCount = userAccess.user_message_count;
            setHasLimitReached(messageCount >= limit);
        };
        const accessChangedListener = (userAccess: UserAccess | null) => {
            if (userAccess) {
                const limit = userAccessManager.getMessageLimit();
                const messageCount = userAccess.user_message_count;
                setHasLimitReached(messageCount >= limit);
            } else {
                setHasLimitReached(false);
            }
        };

        userAccessManager.subscribe('accessEnsured', accessEnsuredListener);
        userAccessManager.subscribe('accessChanged', accessChangedListener);
        chatStateManager.subscribe('chatSessionErrorOccurred', limitReachedListener);
        return () => {
            userAccessManager.unsubscribe('accessEnsured', accessEnsuredListener);
            userAccessManager.unsubscribe('accessChanged', accessChangedListener);
            chatStateManager.unsubscribe('chatSessionErrorOccurred', limitReachedListener);
        };
    }, [userAccessManager, chatStateManager, featureFlags]);

    return { hasLimitReached };
}

function useCurrentThread() {
    const chatStateManager = useChatStateManager();
    const [currentThreadId, setCurrentThreadId] = useState<string | null>(
        chatStateManager.getCurrentThreadId(),
    );

    useEffect(() => {
        const currentThreadChangedListener = (threadId: { thread_id: string } | null) => {
            setCurrentThreadId(threadId?.thread_id ?? null);
        };
        const threadStartedListener = (thread: Thread) => {
            setCurrentThreadId(thread.id);
        };
        const threadResumedListener = (thread: Thread) => {
            setCurrentThreadId(thread.id);
        };
        chatStateManager.subscribe('currentThreadChanged', currentThreadChangedListener);
        chatStateManager.subscribe('threadStarted', threadStartedListener);
        chatStateManager.subscribe('threadResumed', threadResumedListener);
        return () => {
            chatStateManager.unsubscribe('currentThreadChanged', currentThreadChangedListener);
            chatStateManager.unsubscribe('threadStarted', threadStartedListener);
            chatStateManager.unsubscribe('threadResumed', threadResumedListener);
        };
    }, [chatStateManager]);

    const startThread = useCallback(() => {
        chatStateManager.startNewThread();
        setCurrentThreadId(null);
    }, [chatStateManager]);

    const resumeThread = useCallback(
        (threadId: string) => {
            chatStateManager.resumePreviousThread(threadId);
            setCurrentThreadId(threadId);
        },
        [chatStateManager],
    );

    const resetCurrentThread = useCallback(() => {
        setCurrentThreadId(null);
        chatStateManager.resetState();
    }, [chatStateManager]);

    return { currentThreadId, startThread, resumeThread, resetCurrentThread };
}

function useFetchThreads(isOpen: boolean, userAccess: UserAccess | null) {
    const [threads, setThreads] = useState<Thread[]>([]);
    const [isFetching, setIsFetching] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [hasMoreThreads, setHasMoreThreads] = useState(true);
    const [nextTimestamp, setNextTimestamp] = useState<string | null>(null);
    const hasInitiallyFetched = useRef(false);

    const fetchMoreObserverTarget = useRef<HTMLDivElement>(null);

    const chatStateManager = useChatStateManager();
    const threadsApiClient = useThreadsApiClient();

    const fetchThreads = useCallback(async () => {
        // TODO: We don't fetch if there's no access token.  Better solution?
        if (!userAccess?.access_token || isFetching || !hasMoreThreads) return;

        setIsFetching(true);
        try {
            const response = await threadsApiClient.getUserThreads({
                limit: 10,
                sort_by: 'updated_at',
                sort_order: 'desc',
                from_timestamp: nextTimestamp,
                exclude_empty: true,
            });

            setThreads((prev) => {
                // The response threads should be authoritative, so we replace the existing threads with the new ones
                const map = new Map(prev.map((t) => [t.id, t]));
                response.threads.forEach((thread) => map.set(thread.id, thread));
                return Array.from(map.values()).sort((a, b) =>
                    b.updated_at.localeCompare(a.updated_at),
                );
            });
            setHasMoreThreads(response.has_more);
            setNextTimestamp(response.next_timestamp);
        } catch (error) {
            console.error('Error fetching threads:', error);
            setError('Failed to load conversations.');
        } finally {
            setIsFetching(false);
        }
    }, [userAccess?.access_token, isFetching, hasMoreThreads, threadsApiClient, nextTimestamp]);

    useEffect(() => {
        if (!userAccess?.access_token) {
            // Reset fetch state when user access changes
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        } else if (userAccess?.access_token && hasInitiallyFetched.current) {
            // If we get a new access token (user logged in), reset fetch state to get fresh data
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        }
    }, [userAccess?.access_token]);

    useEffect(() => {
        if (isOpen && !hasInitiallyFetched.current) {
            fetchThreads();
            hasInitiallyFetched.current = true;
        }
    }, [isOpen, fetchThreads]);

    useEffect(() => {
        const firstUserMessageSentListener = () => {
            if (!userAccess) {
                return;
            }
            const chatState = chatStateManager.getState();
            if (!chatState.thread) {
                return;
            }
            setThreads((prev) => {
                // Check if the thread already exists in the list
                const existingIndex = prev.findIndex((t) => t.id === chatState.thread?.id);
                if (existingIndex !== -1) {
                    // Thread already exists, don't add it again
                    return prev;
                }
                // Add the new thread to the beginning of the list
                if (chatState.thread) {
                    return [chatState.thread, ...prev];
                }
                return prev;
            });
        };

        const chatStateChangedListener = (chatState: ChatState) => {
            setThreads((prev) => {
                if (!chatState.thread) {
                    return prev;
                }
                const index = prev.findIndex((t) => t.id === chatState.thread?.id);
                if (index !== -1) {
                    const newThreads = [...prev];
                    newThreads[index] = chatState.thread;
                    return newThreads;
                }
                return prev;
            });
        };

        chatStateManager.subscribe('firstMessageSent', firstUserMessageSentListener);
        chatStateManager.subscribe('chatStateChanged', chatStateChangedListener);
        return () => {
            chatStateManager.unsubscribe('firstMessageSent', firstUserMessageSentListener);
            chatStateManager.unsubscribe('chatStateChanged', chatStateChangedListener);
        };
    }, [chatStateManager, userAccess]);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting && !error && isOpen && userAccess?.access_token) {
                    fetchThreads();
                }
            },
            { threshold: 1 }, // 100% of the target element must be visible in the viewport
        );

        const target = fetchMoreObserverTarget.current;
        if (target) {
            observer.observe(target);
        }

        return () => {
            if (target) observer.unobserve(target);
        };
    }, [fetchThreads, error, isOpen, userAccess?.access_token]);

    const threadGroups = useMemo(() => getThreadGroups(threads), [threads]);

    return {
        threads,
        threadGroups,
        isFetching,
        error,
        hasMoreThreads,
        nextTimestamp,
        fetchMoreObserverTarget,
    };
}
