import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { Markdown } from '@/components/ui/Markdown';

const WaveIcon = () => (
    <motion.span
        className="inline-block text-3xl"
        animate={{ rotate: [0, 10, -5, 10, 0] }}
        transition={{
            duration: 1.2,
            ease: 'easeInOut',
            repeat: Infinity,
            repeatDelay: 3,
        }}
        style={{
            transformOrigin: '70% 70%',
            willChange: 'transform',
        }}
    >
        👋
    </motion.span>
);

const USER_PROMPTS = [
    "I'm staring at my fridge with no idea what to make",
    "I'm so bored of my usual meals",
    "I found a recipe but it's not gluten-free/vegan",
    'I got this craving but no clue how to make it',
    'I have 3 random ingredients and need ideas',
    'I want to impress someone with my cooking',
    "I saw something on Instagram but don't know where to start",
    "I'm trying to meal prep but keep getting stuck",
    "I got invited to a potluck and don't know what to bring",
    "My kids are picky eaters and I'm running out of ideas",
    "I want to cook something fancy but I'm not great at cooking",
    'I have veggies that are about to go bad',
    "I'm craving pad thai but don't have the right ingredients",
    "I got some chicken and rice but that's it",
    "I want to make that pasta I saw online but I'm missing stuff",
    "I'm trying to cook for my date but I'm not great at cooking",
    'I have a bunch of spices but no clue what to do with them',
    "I want to make pizza but I don't have the right stuff",
    'I have a bunch of eggs and need to use them up',
    'I want to make something healthy but it always tastes boring',
];

type UserPromptCardProps = {
    message: string;
    onClick: () => void;
    disabled: boolean;
};
export function UserPromptCard({ message, onClick, disabled }: UserPromptCardProps) {
    return (
        <button
            className={`border-border text-contrast hover:bg-secondary-light focus:ring-primary/30 flex w-full items-start rounded-xl border bg-white px-4 py-2.5 text-left text-sm font-medium shadow-sm transition hover:shadow-md focus:ring-2 focus:outline-none active:scale-95 sm:min-h-12 sm:text-base ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
            onClick={onClick}
            disabled={disabled}
        >
            <motion.span
                key={message}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
            >
                {message}
            </motion.span>
        </button>
    );
}

const TAGLINES = [
    'I take *what you have* and make **something amazing.**',
    'I look at *your ingredients* and see **just the right meal.**',
    'I know just what to make with *whatever you have.*',
    'I turn *your kitchen basics* into **really good food.**',
];

const RotatingTagline = () => {
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % TAGLINES.length);
        }, 8000);

        return () => clearInterval(interval);
    }, []);

    return (
        <div className="relative">
            <AnimatePresence mode="wait">
                <motion.div
                    key={currentIndex}
                    initial={{ opacity: 0, y: 2 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -2 }}
                    transition={{ duration: 0.8, ease: 'easeInOut' }}
                    className="prose prose-sm sm:prose-base md:prose-lg"
                >
                    <Markdown>{TAGLINES[currentIndex]}</Markdown>
                </motion.div>
            </AnimatePresence>
        </div>
    );
};

interface WelcomeScreenProps {
    onSendMessage: (message: string) => void;
    disabled: boolean;
}

export function WelcomeScreen({ onSendMessage, disabled }: WelcomeScreenProps) {
    const [currentMessageIndex, setCurrentMessageIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setCurrentMessageIndex((prevIndex) => (prevIndex + 1) % USER_PROMPTS.length);
        }, 180000); // Rotate every 3 minutes

        return () => clearInterval(interval);
    }, []);

    // Get 4 messages starting from current index, wrapping around if needed
    const getDisplayMessages = () => {
        const messages = [];
        for (let i = 0; i < 4; i++) {
            const index = (currentMessageIndex + i) % USER_PROMPTS.length;
            messages.push(USER_PROMPTS[index]);
        }
        return messages;
    };

    return (
        <div className="bg-background flex flex-col items-center justify-center px-4">
            <div className="mb-4 w-full max-w-lg text-center">
                <h1 className="text-contrast font-heading mb-2 flex flex-col items-center justify-center gap-1 text-3xl font-medium">
                    <div className="flex items-center gap-2">
                        <WaveIcon />
                        <span>Hey, I'm Milo! Your AI food buddy.</span>
                    </div>
                </h1>
                <div className="mx-auto mb-2 text-sm leading-snug sm:max-w-lg sm:text-base md:max-w-xl">
                    <RotatingTagline />
                </div>
            </div>
            <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                {getDisplayMessages().map((message, idx) => (
                    <UserPromptCard
                        key={`${currentMessageIndex}-${idx}`}
                        message={message}
                        onClick={() => onSendMessage(message)}
                        disabled={disabled}
                    />
                ))}
            </div>
        </div>
    );
}
