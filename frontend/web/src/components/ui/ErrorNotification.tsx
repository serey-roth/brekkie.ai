import { motion } from 'framer-motion';
import { CircleAlert } from 'lucide-react';

export function ErrorNotification({ errorMessage }: { errorMessage: string }) {
    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{
                duration: 0.2,
                ease: 'easeOut',
            }}
            className="group bg-primary/90 border-primary-dark/50 flex max-w-96 items-start rounded-lg border px-2 py-2 text-sm text-white shadow-lg backdrop-blur-sm"
        >
            <motion.div
                className="flex-shrink-0 md:mt-0.5"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                    duration: 0.2,
                    ease: 'easeOut',
                }}
            >
                <CircleAlert className="h-4 w-4" />
            </motion.div>
            <motion.div
                className="min-w-0 flex-1"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{
                    duration: 0.2,
                    ease: 'easeOut',
                }}
            >
                <span className="ml-2 hidden text-sm break-words group-hover:inline">
                    {errorMessage}
                </span>
            </motion.div>
        </motion.div>
    );
}
