import { motion } from "framer-motion";
import { SuggestedUserMessageCard } from '@/components/chat/SuggestedUserMessageCard';
import { SUGGESTED_USER_MESSAGES } from '@/data/constants/suggested-user-messages';

const WaveIcon = () => (
  <motion.span
    className="text-3xl inline-block"
    animate={{ rotate: [0, 10, -5, 10, 0] }}
    transition={{
      duration: 1.2,
      ease: "easeInOut",
      repeat: Infinity,
      repeatDelay: 3,
    }}
    style={{ 
      transformOrigin: "70% 70%",
      willChange: "transform"
    }}
  >
    👋
  </motion.span>
);


interface WelcomeScreenProps {
    onSendMessage: (message: string) => void;
    disabled: boolean;
}

export function WelcomeScreen({ onSendMessage, disabled }: WelcomeScreenProps) {
    return (
        <div className="bg-background flex flex-col items-center justify-center px-4">
            <div className="mb-4 w-full max-w-lg text-center">
                <h1 className="text-contrast mb-4 text-3xl font-heading font-semibold flex items-center justify-center gap-2">
                    <WaveIcon />
                    <span>Hey, I'm Milo</span>
                </h1>
                <p className="text-contrast-subtle text-sm sm:text-base leading-snug mb-1 mx-auto sm:max-w-lg md:max-w-xl">
                    Your food sidekick who's all about making your life easier 
                </p>
                <p className="text-contrast-subtle text-sm sm:text-base leading-snug mb-4 mx-auto sm:max-w-lg md:max-w-xl">
                    Stuck on what to make? Need a little inspo? I got you 💪
                </p>
            </div>
            <div className="grid w-full max-w-md grid-cols-1 gap-2 sm:grid-cols-2">
                {SUGGESTED_USER_MESSAGES.map((message, idx) => (
                    <SuggestedUserMessageCard
                        key={idx}
                        message={message}
                        onClick={() => onSendMessage(message)}
                        disabled={disabled}
                    />
                ))}
            </div>
        </div>
    );
} 