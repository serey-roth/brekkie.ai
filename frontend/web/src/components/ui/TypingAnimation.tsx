import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

interface TypingAnimationProps {
    text: string;
    speed?: number; // milliseconds per character
    className?: string;
    onComplete?: () => void;
}

export const TypingAnimation = ({ 
    text, 
    speed = 50, 
    className = "",
    onComplete 
}: TypingAnimationProps) => {
    const [displayedText, setDisplayedText] = useState('');
    const [isTyping, setIsTyping] = useState(false);

    useEffect(() => {
        if (!text) {
            setDisplayedText('');
            setIsTyping(false);
            return;
        }

        setIsTyping(true);
        setDisplayedText('');

        let currentIndex = 0;
        const interval = setInterval(() => {
            if (currentIndex < text.length) {
                setDisplayedText(text.slice(0, currentIndex + 1));
                currentIndex++;
            } else {
                setIsTyping(false);
                clearInterval(interval);
                onComplete?.();
            }
        }, speed);

        return () => clearInterval(interval);
    }, [text, speed, onComplete]);

    return (
        <div className={className}>
            <AnimatePresence mode="wait">
                <motion.span
                    key={text}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                >
                    {displayedText}
                    {isTyping && (
                        <motion.span
                            animate={{ opacity: [1, 0] }}
                            transition={{ 
                                duration: 0.6, 
                                repeat: Infinity, 
                                ease: "easeInOut" 
                            }}
                            className="inline-block w-0.5 h-6 bg-current ml-0.5"
                        />
                    )}
                </motion.span>
            </AnimatePresence>
        </div>
    );
}; 