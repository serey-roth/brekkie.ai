import { motion, AnimatePresence, easeInOut } from 'framer-motion';
import { useMemo, useState, useEffect, useCallback, useRef } from 'react';
import {
    LuPanelLeftClose,
    LuMessageSquare,
    LuMessageSquarePlus,
    LuUser,
    LuLogOut,
    LuLogIn,
    LuMessageSquareWarning,
    LuArrowRightFromLine,
    LuArrowLeftFromLine,
    LuMessageSquareX,
    LuUtensils,
} from 'react-icons/lu';
import { useThreadsApiClient, useUserAccessManager } from '@/context/app-context';
import { useAuthModal, useAuth } from '@/context/auth-context';
import { useChatStateManager } from '@/context/chat-context';
import type { ChatState } from '@/data/schemas/chat-state';
import { type Thread } from '@/data/schemas/threads';
import { type UserAccessData } from '@/data/schemas/user-access';
import { getThreadGroups, formatThreadTimestamp } from '@/utils/thread-utils';

const ANIMATION_CONFIG = {
    sidebar: {
        open: { width: '20rem' },
        closed: { width: '4rem' },
    },
    content: {
        open: { opacity: 1, x: 0 },
        closed: { opacity: 0, x: -20 },
    },
    overlay: {
        open: { opacity: 1 },
        closed: { opacity: 0 },
    },
    mobileButtons: {
        open: { opacity: 1, x: 0 },
        closed: { opacity: 0, x: -20 },
    },
    threadGroup: {
        initial: { opacity: 0, y: 10 },
        animate: { opacity: 1, y: 0 },
    },
    loading: {
        initial: { opacity: 0 },
        animate: { opacity: 1 },
        exit: { opacity: 0 },
    },
};

const TRANSITIONS = {
    fast: { duration: 0.2, ease: easeInOut },
    medium: { duration: 0.3, ease: easeInOut },
    slow: { duration: 0.4, ease: easeInOut },
};

interface SidebarProps {
    isOpen: boolean;
    openSidebar: () => void;
    closeSidebar: () => void;
    showRecipeListView: () => void;
    hideRecipeListView: () => void;
}

export function Sidebar({
    isOpen,
    openSidebar,
    closeSidebar,
    showRecipeListView,
    hideRecipeListView,
}: SidebarProps) {
    const { openAuthModal } = useAuthModal();
    const { signout } = useAuth();

    const userAccessData = useUserAccessData();
    const { currentThreadId, startThread, resumeThread, resetCurrentThread } = useCurrentThread();
    const { threadGroups, isFetching, error, fetchMoreObserverTarget } = useFetchThreads(
        isOpen,
        userAccessData,
    );

    return (
        <>
            <AnimatePresence>
                {!isOpen && (
                    <motion.div
                        variants={ANIMATION_CONFIG.mobileButtons}
                        initial="closed"
                        animate="open"
                        exit="closed"
                        transition={TRANSITIONS.fast}
                        className="fixed top-4 left-4 z-50 flex flex-row gap-2 md:hidden"
                    >
                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={openSidebar}
                            className="text-contrast hover:text-primary bg-background/95 focus:ring-primary/20 border-border flex h-10 w-10 items-center justify-center rounded-xl border shadow-lg backdrop-blur-sm transition-colors duration-200 focus:ring-2 focus:outline-none"
                        >
                            <LuPanelLeftClose size={20} />
                        </motion.button>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        variants={ANIMATION_CONFIG.overlay}
                        initial="closed"
                        animate="open"
                        exit="closed"
                        transition={TRANSITIONS.fast}
                        onClick={closeSidebar}
                        className="bg-contrast/20 fixed inset-0 z-40 backdrop-blur-[1px] md:hidden"
                    />
                )}
            </AnimatePresence>

            <motion.div
                initial={false}
                animate={isOpen ? 'open' : 'closed'}
                variants={ANIMATION_CONFIG.sidebar}
                transition={TRANSITIONS.medium}
                className={`bg-background/95 border-border fixed top-0 left-0 z-40 flex h-screen flex-col border-r shadow-lg backdrop-blur-sm transition-transform duration-200 ease-in-out ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}`}
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
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={isOpen ? closeSidebar : openSidebar}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center justify-center rounded-xl border border-transparent p-2 transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                    >
                        {isOpen ? (
                            <LuArrowLeftFromLine size={20} />
                        ) : (
                            <LuArrowRightFromLine size={20} />
                        )}
                    </motion.button>
                </div>

                <div className={`mt-2 flex items-center ${isOpen ? 'mx-4' : 'mx-auto'}`}>
                    <motion.button
                        onClick={() => {
                            showRecipeListView();
                            if (isOpen) {
                                closeSidebar();
                            }
                        }}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.95 }}
                        transition={TRANSITIONS.fast}
                        animate={{
                            width: isOpen ? '100%' : '2.5rem',
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center rounded-xl border border-transparent transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                        style={{ minWidth: '2.5rem', maxWidth: '100%' }}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 items-center justify-center">
                            <LuUtensils size={20} />
                        </div>
                        {isOpen && <span className="whitespace-nowrap">Recipes</span>}
                    </motion.button>
                </div>

                <div className={`mt-2 flex items-center ${isOpen ? 'mx-4' : 'mx-auto'}`}>
                    <motion.button
                        onClick={() => {
                            startThread();
                            hideRecipeListView();
                        }}
                        whileHover={{ scale: 1.01 }}
                        whileTap={{ scale: 0.95 }}
                        transition={TRANSITIONS.fast}
                        animate={{
                            width: isOpen ? '100%' : '2.5rem',
                        }}
                        className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center rounded-xl border border-transparent transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                        style={{ minWidth: '2.5rem', maxWidth: '100%' }}
                        tabIndex={0}
                    >
                        <div className="flex h-10 w-10 items-center justify-center">
                            <LuMessageSquarePlus size={20} />
                        </div>
                        {isOpen && <span className="whitespace-nowrap">New Chat</span>}
                    </motion.button>
                </div>

                <motion.div
                    variants={ANIMATION_CONFIG.content}
                    initial="closed"
                    animate={isOpen ? 'open' : 'closed'}
                    transition={TRANSITIONS.medium}
                    className="flex-1 overflow-hidden"
                >
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
                        {threadGroups.map((group, index) => (
                            <motion.div
                                key={group.label}
                                variants={ANIMATION_CONFIG.threadGroup}
                                initial="initial"
                                animate="animate"
                                transition={TRANSITIONS.medium}
                                className={`${index < threadGroups.length - 1 ? 'mb-3' : ''}`}
                            >
                                <h3
                                    className={`text-contrast-subtle mx-2 mb-2 text-sm tracking-wider`}
                                >
                                    {group.label}
                                </h3>
                                <div className="space-y-0.5">
                                    {group.items.map((thread) => (
                                        <motion.button
                                            key={thread.id}
                                            whileHover={{ scale: 1.01 }}
                                            whileTap={{ scale: 0.99 }}
                                            onClick={() => {
                                                if (currentThreadId !== thread.id) {
                                                    resumeThread(thread.id);
                                                }
                                                hideRecipeListView();
                                            }}
                                            className={`hover:bg-primary/10 hover:border-primary/20 flex w-full items-center gap-2 rounded-xl border border-transparent p-1 text-left text-sm transition-colors duration-200 sm:p-2 ${currentThreadId === thread.id ? 'bg-primary/10 border-primary/50 hover:bg-primary/20' : ''}`}
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
                                        </motion.button>
                                    ))}
                                </div>
                            </motion.div>
                        ))}
                        <div
                            ref={fetchMoreObserverTarget}
                            className="flex h-4 items-center justify-center"
                        >
                            {isFetching && (
                                <motion.div
                                    variants={ANIMATION_CONFIG.loading}
                                    initial="initial"
                                    animate="animate"
                                    exit="exit"
                                    className="text-contrast-subtle flex items-center gap-2 text-sm"
                                >
                                    <div className="border-primary/20 border-t-primary h-4 w-4 animate-spin rounded-full border-2" />
                                    <span>Loading more chats...</span>
                                </motion.div>
                            )}
                        </div>
                    </div>
                </motion.div>

                {isOpen && userAccessData?.is_authenticated && userAccessData?.name && (
                    <motion.div
                        variants={ANIMATION_CONFIG.content}
                        initial="closed"
                        animate="open"
                        transition={TRANSITIONS.medium}
                        className="border-border/50 h-12 flex-shrink-0 border-t"
                    >
                        <div className="mr-4 ml-2 flex h-full items-center gap-2 px-2 sm:px-4">
                            <LuUser size={20} className="flex-shrink-0" />
                            <span className="text-contrast-subtle min-w-0 flex-1 truncate text-sm">
                                {userAccessData?.name}
                            </span>
                        </div>
                    </motion.div>
                )}

                <div
                    className={`mt-2 mb-4 flex flex-shrink-0 items-center gap-2 ${isOpen ? 'mx-4' : 'mx-auto'}`}
                >
                    {!userAccessData?.is_authenticated && (
                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.95 }}
                            animate={{
                                width: isOpen ? '100%' : '2.5rem',
                            }}
                            transition={TRANSITIONS.fast}
                            onClick={() => openAuthModal('login')}
                            className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center rounded-xl border border-transparent transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                            style={{ minWidth: '2.5rem', maxWidth: '100%' }}
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
                        </motion.button>
                    )}

                    {userAccessData?.is_authenticated && userAccessData?.name && (
                        <motion.button
                            whileHover={{ scale: 1.01 }}
                            whileTap={{ scale: 0.95 }}
                            animate={{
                                width: isOpen ? '100%' : '2.5rem',
                            }}
                            transition={TRANSITIONS.fast}
                            onClick={async () => {
                                await signout();
                                resetCurrentThread();
                            }}
                            className={`text-contrast hover:text-primary hover:bg-primary/10 focus:ring-primary/20 hover:border-primary/20 flex h-10 w-10 items-center rounded-xl border border-transparent transition-colors duration-200 focus:ring-0 focus:outline-none md:flex ${!isOpen ? 'md:bg-primary/10' : ''}`}
                            style={{ minWidth: '2.5rem', maxWidth: '100%' }}
                            tabIndex={0}
                        >
                            <div className="flex w-10 items-center justify-center">
                                <LuLogOut size={20} />
                            </div>
                            {isOpen && (
                                <span className="text-base whitespace-nowrap">Sign out</span>
                            )}
                        </motion.button>
                    )}
                </div>
            </motion.div>
        </>
    );
}

const useUserAccessData = () => {
    const userAccessManager = useUserAccessManager();
    const [userAccessData, setUserAccessData] = useState<UserAccessData | null>(
        userAccessManager.getUserAccessData(),
    );

    useEffect(() => {
        const accessEnsuredListener = (userAccessData: UserAccessData) =>
            setUserAccessData(userAccessData);
        const accessChangedListener = (userAccessData: UserAccessData | null) =>
            setUserAccessData(userAccessData);
        userAccessManager.subscribe('accessEnsured', accessEnsuredListener);
        userAccessManager.subscribe('accessChanged', accessChangedListener);
        return () => {
            userAccessManager.unsubscribe('accessEnsured', accessEnsuredListener);
            userAccessManager.unsubscribe('accessChanged', accessChangedListener);
        };
    }, [userAccessManager]);

    return userAccessData;
};

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
        chatStateManager.resetState();
        setCurrentThreadId(null);
    }, [chatStateManager]);

    return { currentThreadId, startThread, resumeThread, resetCurrentThread };
}

function useFetchThreads(isOpen: boolean, userAccessData: UserAccessData | null) {
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
        if (!userAccessData?.access_token || isFetching || !hasMoreThreads) return;

        setIsFetching(true);
        try {
            const response = await threadsApiClient.getUserThreads(
                {
                    limit: 10,
                    sort_by: 'updated_at',
                    sort_order: 'desc',
                    from_timestamp: nextTimestamp,
                    exclude_empty: true,
                },
                userAccessData.access_token,
            );

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
    }, [userAccessData?.access_token, isFetching, hasMoreThreads, threadsApiClient, nextTimestamp]);

    useEffect(() => {
        if (!userAccessData?.access_token) {
            // Reset fetch state when user access changes
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        } else if (userAccessData?.access_token && hasInitiallyFetched.current) {
            // If we get a new access token (user logged in), reset fetch state to get fresh data
            setThreads([]);
            setHasMoreThreads(true);
            setNextTimestamp(null);
            hasInitiallyFetched.current = false;
            setError(null);
        }
    }, [userAccessData?.access_token]);

    useEffect(() => {
        if (isOpen && !hasInitiallyFetched.current) {
            fetchThreads();
            hasInitiallyFetched.current = true;
        }
    }, [isOpen, fetchThreads]);

    useEffect(() => {
        const firstUserMessageSentListener = () => {
            if (!userAccessData) {
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
    }, [chatStateManager, userAccessData]);

    useEffect(() => {
        const observer = new IntersectionObserver(
            (entries) => {
                console.log('🔄 IntersectionObserver - entries:', entries);
                if (entries[0].isIntersecting && !error && isOpen && userAccessData?.access_token) {
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
    }, [fetchThreads, error, isOpen, userAccessData?.access_token]);

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
