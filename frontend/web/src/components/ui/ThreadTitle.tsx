import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface ThreadTitleProps {
    title: string | null;
    state: 'empty' | 'loading' | 'complete';
    className?: string;
    speed?: number;
}

export const ThreadTitle = ({ title, state, className = '', speed = 50 }: ThreadTitleProps) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [showShimmer, setShowShimmer] = useState(false);

    useEffect(() => {
        switch (state) {
            case 'empty':
                setDisplayedText('');
                setIsTyping(false);
                setShowShimmer(false);
                break;

            case 'loading':
                setDisplayedText('');
                setIsTyping(false);
                setShowShimmer(true);
                break;

            case 'complete':
                if (title) {
                    setShowShimmer(false);
                    setIsTyping(true);
                    setDisplayedText('');

                    let currentIndex = 0;
                    const interval = setInterval(() => {
                        if (currentIndex < title.length) {
                            setDisplayedText(title.slice(0, currentIndex + 1));
                            currentIndex++;
                        } else {
                            setIsTyping(false);
                            clearInterval(interval);
                        }
                    }, speed);

                    return () => clearInterval(interval);
                }
                break;
        }
    }, [state, title, speed]);

    return (
        <div className={className} style={{ visibility: state === 'empty' ? 'hidden' : 'visible' }}>
            <AnimatePresence mode="wait">
                {showShimmer ? (
                    <motion.div
                        key="shimmer"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="relative flex h-8 items-center"
                    >
                        <div className="text-contrast/60 text-xl leading-none font-semibold">
                            {state === 'loading' ? 'New chat' : ''}
                        </div>
                        <motion.div
                            className="via-contrast/20 absolute inset-0 bg-gradient-to-r from-transparent to-transparent"
                            animate={{
                                x: ['-100%', '100%'],
                            }}
                            transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                ease: 'easeInOut',
                            }}
                            style={{
                                background:
                                    'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
                            }}
                        />
                    </motion.div>
                ) : (
                    <motion.div
                        key="actual-text"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="flex h-8 items-center"
                    >
                        <span className="text-contrast text-xl leading-none font-semibold">
                            {displayedText}
                            <motion.span
                                animate={{ opacity: isTyping ? [1, 0] : 0 }}
                                transition={{
                                    duration: 0.6,
                                    repeat: isTyping ? Infinity : 0,
                                    ease: 'easeInOut',
                                }}
                                className="ml-0.5 inline-block h-6 w-0.5 bg-current"
                            />
                        </span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};
