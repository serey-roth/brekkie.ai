import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { FaArrowDown } from 'react-icons/fa';
import { FaCircleExclamation, FaTriangleExclamation } from 'react-icons/fa6';
import ChatInput from '@/components/chat/ChatInput';
import { ConnectionStatusNotification } from '@/components/chat/ConnectionStatusNotification';
import { ErrorNotification } from '@/components/ui/ErrorNotification';
import { ThreadTitle } from '@/components/ui/ThreadTitle';
import { useAppConfig } from '@/context/app-context';
import type { ConnectionStatus } from '@/data/schemas/connection-state';
import type { ChatLimitMessage } from '@/data/schemas/errors';

interface ChatLayoutProps {
    children: React.ReactNode;
    selectedRecipeId: string | null;
    scrollToBottomMessage: string | null;
    onScrollToBottom: () => void;
    onSendMessage: (message: string) => void;
    scrollRef: React.RefObject<HTMLDivElement | null>;
    connectionStatus: ConnectionStatus;
    threadTitle: string | null;
    threadTitleState: 'empty' | 'loading' | 'complete';
    appErrorMessage: string | null;
    chatSessionErrorMessage: string | null;
    chatLimitMessage: ChatLimitMessage | null;
    disableSendButton?: boolean;
    isAuthenticated?: boolean;
    onSignIn?: () => void;
}

export function ChatLayout({
    children,
    selectedRecipeId,
    scrollToBottomMessage,
    scrollRef,
    disableSendButton,
    connectionStatus,
    appErrorMessage,
    threadTitle,
    threadTitleState,
    chatSessionErrorMessage,
    chatLimitMessage,
    onScrollToBottom,
    onSendMessage,
    isAuthenticated,
    onSignIn,
}: ChatLayoutProps) {
    const { featureFlags } = useAppConfig();
    const { messageInputGapRef } = useMessageInputGapResize({
        onResize: ({ height }) => {
            if (scrollRef.current) {
                scrollRef.current.style.paddingBottom = `${height + 16}px`;
            }
        },
    });
    const { inputContainerRef } = useChatInputResize({
        onResize: ({ height }) => {
            if (messageInputGapRef.current) {
                messageInputGapRef.current.style.bottom = `${height}px`;
            }
        },
    });

    return (
        <motion.div
            className={`relative ${selectedRecipeId ? 'col-span-1' : 'w-full lg:col-span-1 lg:mx-auto'}`}
            animate={{
                x: selectedRecipeId ? '0%' : '0%',
                width: selectedRecipeId ? '100%' : '100%',
            }}
            transition={{ type: 'tween', duration: 0.2 }}
        >
            <div className={`absolute top-5 right-4 z-50 flex flex-col items-end gap-1`}>
                <ConnectionStatusNotification status={connectionStatus} />
                {appErrorMessage && <ErrorNotification errorMessage={appErrorMessage} />}
            </div>
            <div
                className={`bg-background absolute top-0 right-0 bottom-0 left-0 z-10 h-20 w-full transition-all duration-300 ease-in-out ${threadTitle || threadTitleState !== 'empty' ? 'border-border border-b shadow-sm' : 'border-b border-transparent shadow-none'}`}
            >
                {/* TODO: The title is sandwiched between absolute-positioned icons on smaller devices, making for awkward alignment */}
                <div className="mt-[1.15rem] flex h-8 w-full pl-16 md:pl-4">
                    <ThreadTitle
                        title={threadTitle}
                        state={threadTitleState}
                        className="max-w-[350px] truncate text-ellipsis md:max-w-none"
                        speed={30}
                    />
                </div>
            </div>
            <motion.div
                layout
                className="mx-auto flex h-screen max-w-3xl flex-col items-center overflow-hidden"
            >
                <div
                    className="custom-scrollbar w-full flex-1 overflow-y-auto px-4 pt-[100px] pb-4 transition-all duration-300"
                    ref={scrollRef}
                >
                    {children}
                </div>
                <div
                    className="absolute bottom-0 left-1/2 flex w-full max-w-3xl -translate-x-1/2 flex-col items-center gap-2 px-4"
                    ref={messageInputGapRef}
                >
                    <motion.div
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2 }}
                        className="flex w-full flex-col items-center justify-center"
                    >
                        <AnimatePresence>
                            {chatLimitMessage && (
                                <motion.div
                                    key="limit-message"
                                    layout
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="mb-2 flex items-center justify-center gap-2 text-center"
                                >
                                    <div className="flex max-w-xl items-center justify-center">
                                        <div className="bg-background border-primary/50 text-contrast rounded-xl border px-3 py-2 text-base leading-relaxed shadow-md backdrop-blur-sm sm:text-sm">
                                            <div className="flex flex-wrap items-center justify-center gap-1">
                                                <div className="flex flex-nowrap items-center gap-2 text-sm">
                                                    {chatLimitMessage.type === 'warning' && (
                                                        <FaTriangleExclamation className="h-4 w-4 text-yellow-500" />
                                                    )}
                                                    {chatLimitMessage.type === 'error' && (
                                                        <FaCircleExclamation className="h-4 w-4 text-red-500" />
                                                    )}
                                                    <span>{chatLimitMessage.message}</span>
                                                </div>
                                                {featureFlags.enableAuth &&
                                                !isAuthenticated &&
                                                onSignIn ? (
                                                    <div className="flex items-center gap-1 text-sm">
                                                        <button
                                                            onClick={onSignIn}
                                                            className="text-primary-dark hover:text-primary text-sm font-medium underline"
                                                        >
                                                            Sign in
                                                        </button>
                                                        <span> to unlock a higher limit.</span>
                                                    </div>
                                                ) : (
                                                    chatLimitMessage.type === 'error' && (
                                                        <div className="flex items-center gap-1 text-sm">
                                                            <span>Please check back later.</span>
                                                        </div>
                                                    )
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                            {chatSessionErrorMessage && (
                                <motion.div
                                    key="chat-error"
                                    layout
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="mb-4 flex w-full max-w-xl items-center justify-center gap-2 text-center"
                                >
                                    <div className="flex w-full items-center justify-center">
                                        <div className="bg-background rounded-2xl border border-red-300 px-4 py-3 text-base leading-relaxed text-red-700 shadow-md sm:text-sm">
                                            <div className="flex items-center gap-2">
                                                <FaCircleExclamation className="h-4 w-4" />
                                                <span>{chatSessionErrorMessage}</span>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            )}
                            {scrollToBottomMessage && (
                                <motion.button
                                    key="scroll-btn"
                                    initial={{ opacity: 0, scale: 0.9 }}
                                    animate={{ opacity: 1, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    transition={{ duration: 0.2, ease: 'easeOut' }}
                                    onClick={onScrollToBottom}
                                    className="bg-background text-contrast/80 hover:text-contrast border-border shadow-background mb-3 flex items-center justify-center gap-2 rounded-full border px-4 py-2 shadow-sm transition-all"
                                >
                                    <motion.div
                                        animate={{ y: [0, 4, 0] }}
                                        transition={{
                                            duration: 1.5,
                                            repeat: Infinity,
                                            ease: 'easeInOut',
                                        }}
                                    >
                                        <FaArrowDown />
                                    </motion.div>
                                    <span className="text-contrast text-sm">
                                        {scrollToBottomMessage}
                                    </span>
                                </motion.button>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>
                <div className="w-full">
                    <ChatInput
                        onSend={onSendMessage}
                        disabled={disableSendButton}
                        inputContainerRef={inputContainerRef}
                    />
                </div>
            </motion.div>
        </motion.div>
    );
}

function useChatInputResize({
    onResize,
}: {
    onResize: (args: { height: number; width: number }) => void;
}) {
    const inputContainerRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (!inputContainerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            const height = entries[0].contentRect.height;
            const width = entries[0].contentRect.width;
            onResize({ height, width });
        });

        resizeObserver.observe(inputContainerRef.current);
        return () => resizeObserver.disconnect();
    }, [onResize]);

    return { inputContainerRef };
}

function useMessageInputGapResize({
    onResize,
}: {
    onResize: (args: { height: number; width: number }) => void;
}) {
    const messageInputGapRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
        if (!messageInputGapRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            const height = entries[0].contentRect.height;
            const width = entries[0].contentRect.width;
            onResize({ height, width });
        });

        resizeObserver.observe(messageInputGapRef.current);
    }, [onResize]);

    return { messageInputGapRef };
}
