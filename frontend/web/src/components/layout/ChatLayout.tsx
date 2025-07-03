import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef } from 'react';
import { FaArrowDown } from 'react-icons/fa';
import { FaCircleExclamation, FaTriangleExclamation } from 'react-icons/fa6';
import ChatInput from '@/components/chat/ChatInput';
import { ConnectionStatus } from '@/components/chat/ConnectionStatus';
import type { ConnectionState } from '@/data/schemas/connection-state';
import type { ChatLimitMessage } from '@/data/schemas/errors';
import { TypingAnimation } from '../ui/TypingAnimation';

interface ChatLayoutProps {
    children: React.ReactNode;
    selectedRecipeId: string | null;
    scrollToBottomMessage: string | null;
    onScrollToBottom: () => void;
    onSendMessage: (message: string) => void;
    scrollRef: React.RefObject<HTMLDivElement | null>;
    connectionState: ConnectionState;
    isAuthenticated: boolean;
    threadTitle: string | null;
    disableSendButton?: boolean;
    chatSessionErrorMessage?: string;
    chatLimitMessage?: ChatLimitMessage;
    onSignIn?: () => void;
}

export function ChatLayout({
    children,
    selectedRecipeId,
    scrollToBottomMessage,
    scrollRef,
    disableSendButton,
    connectionState,
    threadTitle,
    chatSessionErrorMessage,
    chatLimitMessage,
    isAuthenticated,
    onSignIn,
    onScrollToBottom,
    onSendMessage,
}: ChatLayoutProps) {
    const { messageInputGapRef } = useMessageInputGapResize({ onResize: ({ height }) => {
        if (scrollRef.current) {
            scrollRef.current.style.paddingBottom = `${height}px`;
        }
    }});
    const { inputContainerRef } = useChatInputResize({ onResize: ({ height }) => {
        if (messageInputGapRef.current) {
            messageInputGapRef.current.style.bottom = `${height}px`;
        }
    }});

    return (
        <motion.div
            className={`relative ${selectedRecipeId ? 'col-span-1' : 'w-full lg:col-span-1 lg:mx-auto'}`}
            animate={{
                x: selectedRecipeId ? '0%' : '0%',
                width: selectedRecipeId ? '100%' : '100%',
            }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
        >
            <ConnectionStatus connectionState={connectionState} />
            {threadTitle && <div className={`absolute top-0 left-0 right-0 bottom-0 z-10 h-20 bg-background border-b border-border shadow-sm transition-all duration-300 w-full`}>
                {/* TODO: The title is sandwiched between absolute-positioned icons on smaller devices, making for awkward alignment */}
                <div className="w-full flex pl-16 md:pl-4 mt-6">
                    <TypingAnimation 
                        text={threadTitle} 
                        speed={30}
                        className="text-xl font-semibold text-contrast truncate text-ellipsis max-w-[350px] md:max-w-none"
                    />
                </div>
            </div>}
            <motion.div
                layout
                className="mx-auto flex h-screen max-w-3xl flex-col items-center overflow-hidden"
            >
                <div className="w-full flex-1 overflow-y-auto px-4 pb-4 pt-[100px] custom-scrollbar transition-all duration-300" ref={scrollRef}>
                    {children}
                </div>
                <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full max-w-3xl px-4 flex flex-col items-center gap-2" ref={messageInputGapRef}>
                    <motion.div
                        layout
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.2 }}
                        className="w-full flex flex-col items-center justify-center"
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
                                    className="flex gap-2 items-center justify-center mb-2  text-center"
                                >
                                    <div className="flex items-center justify-center max-w-xl">
                                        <div className="bg-background border border-primary/50 shadow-md text-contrast px-3 text-base leading-relaxed sm:text-sm py-2 rounded-xl backdrop-blur-sm">
                                            <div className="flex flex-wrap justify-center items-center gap-1">
                                                <div className="flex items-center gap-2 flex-nowrap text-sm">
                                                    {chatLimitMessage.type === 'warning' && <FaTriangleExclamation className="w-4 h-4 text-yellow-500" />}
                                                    {chatLimitMessage.type === 'error' && <FaCircleExclamation className="w-4 h-4 text-red-500" />}
                                                    <span>{chatLimitMessage.message}</span>
                                                </div>
                                                {!isAuthenticated && onSignIn && <div className="flex items-center gap-1 text-sm">
                                                    <button 
                                                        onClick={onSignIn}
                                                        className="text-primary-dark hover:text-primary font-medium underline text-sm"
                                                    >
                                                        Sign in
                                                    </button>
                                                    <span> to unlock a higher limit.</span>
                                                </div>}
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
                                    className="flex gap-2 items-center justify-center max-w-xl mb-4 w-full text-center"
                                >
                                    <div className="flex items-center justify-center w-full">
                                        <div className="bg-background border border-red-300 shadow-md text-red-700 px-4 text-base leading-relaxed sm:text-sm py-3 rounded-2xl">
                                            <div className="flex items-center gap-2">
                                                <FaCircleExclamation className="w-4 h-4" />
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
                                    transition={{ duration: 0.2, ease: "easeOut" }}
                                    onClick={onScrollToBottom}
                                    className="bg-background text-contrast/80 hover:text-contrast mb-3 flex items-center justify-center gap-2 rounded-full px-4 py-2 shadow-sm border border-border shadow-background transition-all"
                                >
                                    <motion.div
                                        animate={{ y: [0, 4, 0] }}
                                        transition={{
                                            duration: 1.5,
                                            repeat: Infinity,
                                            ease: "easeInOut"
                                        }}
                                    >
                                        <FaArrowDown />
                                    </motion.div>
                                    <span className="text-contrast text-sm">{scrollToBottomMessage}</span>
                                </motion.button>
                            )}
                        </AnimatePresence>
                    </motion.div>
                </div>
                <div className='w-full'>
                    <ChatInput onSend={onSendMessage} disabled={disableSendButton} inputContainerRef={inputContainerRef} />
                </div>
            </motion.div>
        </motion.div>
    );
} 

function useChatInputResize({ onResize }: { onResize: (args: { height: number, width: number }) => void }) {
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

function useMessageInputGapResize({ onResize }: { onResize: (args: { height: number, width: number }) => void }) {
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
