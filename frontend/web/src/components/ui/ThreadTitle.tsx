import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface ThreadTitleProps {
    title: string | null;
    state: 'empty' | 'loading' | 'complete';
    className?: string;
    speed?: number;
}

export const ThreadTitle = ({ 
    title, 
    state,
    className = "",
    speed = 50,
}: ThreadTitleProps) => {
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
                        className="relative h-8 flex items-center"
                    >
                        <div className="text-xl font-semibold text-contrast/60 leading-none">
                            {state === 'loading' ? 'New chat' : ''}
                        </div>
                        <motion.div
                            className="absolute inset-0 bg-gradient-to-r from-transparent via-contrast/20 to-transparent"
                            animate={{
                                x: ['-100%', '100%']
                            }}
                            transition={{
                                duration: 1.5,
                                repeat: Infinity,
                                ease: "easeInOut"
                            }}
                            style={{
                                background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)'
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
                        className="h-8 flex items-center"
                    >
                        <span className="text-xl font-semibold text-contrast leading-none">
                            {displayedText}
                            <motion.span
                                animate={{ opacity: isTyping ? [1, 0] : 0 }}
                                transition={{ 
                                    duration: 0.6, 
                                    repeat: isTyping ? Infinity : 0,
                                    ease: "easeInOut" 
                                }}
                                className="inline-block w-0.5 h-6 bg-current ml-0.5"
                            />
                        </span>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}; 
