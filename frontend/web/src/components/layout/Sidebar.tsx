import {
    PanelLeftClose,
    MessageCircle,
    MessageCirclePlus,
    LogIn,
    MessageCircleWarning,
    SidebarOpenIcon,
    SidebarCloseIcon,
    MessageCircleX,
    Utensils,
    LogOut,
    Info,
    Mail,
} from 'lucide-react';
import { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Avatar } from '@/components/ui/Avatar';
import { Menu } from '@/components/ui/Menu';
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
import { useSupabaseAuth } from '@/hooks/use-supabase-auth';
import type { UserMetadata } from '@/supabase-client';
import { getThreadGroups, formatThreadTimestamp } from '@/utils/thread-utils';

interface SidebarProps {
    showRecipeListView: () => void;
    hideRecipeListView: () => void;
}

export function Sidebar({ showRecipeListView, hideRecipeListView }: SidebarProps) {
    const { isSidebarOpen: isOpen, setIsSidebarOpen } = useAppState();
    const { featureFlags } = useAppConfig();

    const { getClaims, logout, addAuthStateChangeListener } = useSupabaseAuth();
    const userAccess = useUserAccess();

    const { hasLimitReached } = useChatLimit();
    const { currentThreadId, startThread, resumeThread, resetCurrentThread } = useCurrentThread();
    const { threadGroups, isFetching, error, fetchMoreObserverTarget } = useFetchThreads(
        isOpen,
        userAccess,
    );

    const [user, setUser] = useState<UserMetadata | null>(null);
    useEffect(() => {
        const unsubscribe = addAuthStateChangeListener((event, session) => {
            if (event === 'SIGNED_IN' && session?.user) {
                setUser(session.user.user_metadata);
            } else if (event === 'SIGNED_IN' && !session) {
                setUser(null);
            } else if (event === 'SIGNED_OUT') {
                setUser(null);
            }
        });

        const checkAuth = async () => {
            const claims = await getClaims();
            if (claims.aud === 'authenticated') {
                setUser(claims['user_metadata']);
            } else {
                setUser(null);
            }
        };

        checkAuth();
        return () => {
            unsubscribe();
        };
    }, [addAuthStateChangeListener, getClaims]);

    const navigate = useNavigate();
    const userAccessManager = useUserAccessManager();

    return (
        <>
            {!isOpen && (
                <div className="fixed top-4 left-4 z-50 flex flex-row gap-2 md:hidden">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="text-contrast hover:text-primary bg-background/95 focus:ring-primary/20 border-border flex h-10 w-10 items-center justify-center rounded-xl border shadow-lg backdrop-blur-sm transition-all duration-200 focus:ring-2 focus:outline-none"
                    >
                        <PanelLeftClose size={20} />
                    </button>
                </div>
            )}

            {isOpen && (
                <div
                    onClick={() => setIsSidebarOpen(false)}
                    className="bg-contrast/20 fixed inset-0 z-40 backdrop-blur-[1px] md:hidden"
                />
            )}

            <div
                className={`bg-background/95 border-border fixed top-0 left-0 z-40 flex h-screen flex-col border-r shadow-lg backdrop-blur-sm transition-all duration-300 ease-in-out ${isOpen ? 'w-80 translate-x-0' : 'w-14 -translate-x-full md:translate-x-0'}`}
            >
                <div className="mx-2 mt-2 flex items-center">
                    <div
                        className="flex flex-1 flex-shrink-0 flex-row items-center"
                        title={!isOpen ? 'Open sidebar' : ''}
                    >
                        <div
                            className={`group relative flex h-10 w-10 items-center justify-center`}
                        >
                            <img
                                src="/brekkie-logo.png"
                                alt="Brekkie Logo"
                                className={`h-8 w-8 ${!isOpen ? 'opacity-100 transition-opacity duration-200 group-hover:opacity-0' : ''}`}
                            />
                            {!isOpen && (
                                <div
                                    className={`group-hover:bg-primary/10 absolute top-0 left-0 flex h-full w-full items-center justify-center rounded-xl opacity-0 transition-opacity duration-200 group-hover:opacity-100`}
                                    onClick={() => setIsSidebarOpen(true)}
                                >
                                    <SidebarOpenIcon size={18} className="text-contrast-subtle" />
                                </div>
                            )}
                        </div>
                        <div
                            className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}
                        >
                            <div className="flex items-center gap-2 whitespace-nowrap">
                                <span className="text-contrast text-xl font-bold">brekkie.ai</span>
                                <span className="text-contrast-subtle bg-primary/20 rounded-full px-2 py-0.5 text-xs font-semibold">
                                    beta
                                </span>
                            </div>
                        </div>
                    </div>
                    {isOpen && (
                        <button
                            onClick={() => setIsSidebarOpen(false)}
                            className={`text-contrast hover:text-primary hover:bg-primary/5 focus:ring-primary/20 hover:border-primary/10 flex h-10 w-10 items-center justify-center rounded-xl border border-transparent p-2 transition-colors duration-200 focus:ring-0 focus:outline-none md:flex`}
                            title="Close sidebar"
                        >
                            <SidebarCloseIcon size={18} />
                        </button>
                    )}
                </div>

                <div className="mx-2 flex items-center">
                    <button
                        onClick={() => {
                            if (isOpen) {
                                setIsSidebarOpen(false);
                            }
                            showRecipeListView();
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/5 focus:ring-primary/20 hover:border-primary/10 flex h-10 items-center rounded-xl border border-transparent transition-all duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/5 w-10' : 'w-full'}`}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center">
                            <Utensils size={18} />
                        </div>
                        <div
                            className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}
                        >
                            <span className="text-sm whitespace-nowrap">Cookbook</span>
                        </div>
                    </button>
                </div>

                <div
                    className={`mx-2 flex items-center ${hasLimitReached ? 'pointer-events-none cursor-not-allowed opacity-50' : ''}`}
                >
                    <button
                        disabled={hasLimitReached}
                        onClick={() => {
                            startThread();
                            hideRecipeListView();
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/5 focus:ring-primary/20 hover:border-primary/10 flex h-10 items-center rounded-xl border border-transparent transition-all duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/5 w-10' : 'w-full'}`}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center">
                            <MessageCirclePlus size={18} />
                        </div>
                        <div
                            className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}
                        >
                            <span className="text-sm whitespace-nowrap">New Chat</span>
                        </div>
                    </button>
                </div>

                <div className="flex-1 overflow-hidden">
                    {isOpen && threadGroups.length > 0 && (
                        <div className="mx-4 mt-2 flex flex-row items-center justify-between">
                            <h2 className="text-contrast text-sm tracking-wider">Recent chats</h2>
                            <div className="text-contrast-subtle text-xs opacity-80">
                                Sorted by last activity
                            </div>
                        </div>
                    )}
                    <div className="custom-scrollbar h-full overflow-y-auto pt-2 pb-8">
                        {isOpen && threadGroups.length === 0 && !isFetching && !error && (
                            <div className="text-contrast-subtle py-8 text-center text-sm">
                                <div className="mb-2">
                                    <MessageCircleX size={32} className="text-primary/60 mx-auto" />
                                </div>
                                <p className="mx-auto max-w-[240px] font-medium">
                                    No chats yet. Milo's waiting whenever you're ready.
                                </p>
                            </div>
                        )}
                        {isOpen && error && (
                            <div className="text-contrast-subtle flex flex-col items-center justify-center gap-1 py-8 text-center text-sm">
                                <div className="mb-2">
                                    <MessageCircleWarning
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
                                        className={`text-contrast-subtle mx-4 mb-1 text-sm tracking-wider`}
                                    >
                                        {group.label}
                                    </h3>
                                    <div className="mx-2 space-y-0.5">
                                        {group.items.map((thread) => (
                                            <button
                                                key={thread.id}
                                                onClick={() => {
                                                    if (currentThreadId !== thread.id) {
                                                        resumeThread(thread.id);
                                                    }
                                                    hideRecipeListView();
                                                }}
                                                className={`hover:bg-primary/5 hover:border-primary/10 flex w-full items-center gap-2 rounded-xl border border-transparent p-1 text-left text-sm transition-all duration-200 ${currentThreadId === thread.id ? 'bg-primary/10 border-primary/50 hover:bg-primary/15' : ''}`}
                                            >
                                                <div className="bg-primary/10 flex h-8 w-8 items-center justify-center rounded-full">
                                                    <MessageCircle
                                                        size={16}
                                                        className="text-primary/80"
                                                    />
                                                </div>
                                                <div className="ml-2 min-w-0 flex-1">
                                                    <div className="text-contrast truncate text-xs">
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
                    <div className="mx-2 mt-2 mb-4 flex">
                        {user ? (
                            <Menu
                                placement="top"
                                align="start"
                                containerClassName="w-full"
                                menuClassName="bg-background-light"
                                submenuClassName="bg-background-light"
                                offset={4}
                                trigger={
                                    <button
                                        className={`text-contrast focus:ring-primary/20 flex w-full items-center justify-center rounded-xl border border-transparent p-1 transition-all duration-200 focus:ring-0 focus:outline-none md:flex ${
                                            !isOpen
                                                ? ''
                                                : 'hover:bg-primary/5 hover:border-primary/10'
                                        }`}
                                        tabIndex={0}
                                    >
                                        <div className="flex w-full items-center gap-2">
                                            <div className="flex-shrink-0">
                                                <Avatar
                                                    name={user?.name || 'User'}
                                                    avatarUrl={user?.avatar_url}
                                                    size="sm"
                                                />
                                            </div>
                                            <div
                                                className={`overflow-hidden transition-all duration-300 ease-in-out ${
                                                    isOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'
                                                }`}
                                            >
                                                <div className="flex flex-col items-start">
                                                    <span className="text-sm whitespace-nowrap">
                                                        {user?.name}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    </button>
                                }
                                items={[
                                    {
                                        label: user?.email || 'User',
                                        icon: <></>,
                                    },
                                    {
                                        label: '',
                                        icon: (
                                            <div className="flex items-center gap-2">
                                                <Avatar
                                                    name={user?.name ?? null}
                                                    avatarUrl={user?.avatar_url}
                                                    size="sm"
                                                />
                                                <div className="flex flex-col items-start">
                                                    <span className="text-sm whitespace-nowrap">
                                                        {user?.name}
                                                    </span>
                                                </div>
                                            </div>
                                        ),
                                    },
                                    {
                                        label: 'Contact Support',
                                        icon: <Mail size={16} />,
                                        onClick: () =>
                                            window.open(
                                                'mailto:sereyratanakroth@gmail.com',
                                                '_self',
                                            ),
                                    },
                                    {
                                        label: 'About',
                                        icon: <Info size={16} />,
                                        onClick: () =>
                                            window.open(
                                                'https://meet-brekkie-ai.vercel.app',
                                                '_blank',
                                                'noopener,noreferrer',
                                            ),
                                    },
                                    {
                                        label: 'Sign Out',
                                        icon: <LogOut size={16} />,
                                        onClick: async () => {
                                            try {
                                                await logout();
                                                userAccessManager.clearAuth();
                                                resetCurrentThread();
                                            } catch (error) {
                                                console.error('Logout failed:', error);
                                            }
                                        },
                                    },
                                ]}
                            />
                        ) : (
                            <button
                                onClick={async () => {
                                    navigate('/auth');
                                }}
                                className={`text-contrast hover:text-primary hover:bg-primary/5 focus:ring-primary/20 hover:border-primary/10 flex h-10 items-center rounded-xl border border-transparent py-1 transition-all duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/5 w-10' : 'w-full'}`}
                                tabIndex={0}
                                title="Sign in to save your chats"
                            >
                                <div className="flex w-10 flex-shrink-0 items-center justify-center">
                                    <LogIn size={18} />
                                </div>
                                <div
                                    className={`overflow-hidden transition-all duration-300 ease-in-out ${isOpen ? 'w-auto opacity-100' : 'w-0 opacity-0'}`}
                                >
                                    <span className="text-sm whitespace-nowrap">Sign in</span>
                                </div>
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
    const [hasLimitReached, setHasLimitReached] = useState(false);

    useEffect(() => {
        const limitReachedListener = (error: ChatSessionError) => {
            if (error.type === 'over_message_limit') {
                setHasLimitReached(true);
            }
        };

        chatStateManager.subscribe('chatSessionErrorOccurred', limitReachedListener);
        return () => {
            chatStateManager.unsubscribe('chatSessionErrorOccurred', limitReachedListener);
        };
    }, [chatStateManager]);

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
        if (!userAccess?.jwt || isFetching || !hasMoreThreads) return;

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
    }, [userAccess?.jwt, isFetching, hasMoreThreads, threadsApiClient, nextTimestamp]);

    useEffect(() => {
        if (!userAccess?.jwt) {
            // Reset fetch state when user access changes
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        } else if (userAccess?.jwt && hasInitiallyFetched.current) {
            // If we get a new access token (user logged in), reset fetch state to get fresh data
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        }
    }, [userAccess?.jwt]);

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
                if (entries[0].isIntersecting && !error && isOpen && userAccess?.jwt) {
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
    }, [fetchThreads, error, isOpen, userAccess?.jwt]);

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
