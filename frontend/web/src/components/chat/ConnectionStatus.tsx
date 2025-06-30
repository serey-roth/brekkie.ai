import { AnimatePresence, motion } from "framer-motion";
import { useMemo } from "react";
import { FaCircleExclamation } from "react-icons/fa6";
import { LuWifiOff, LuLoader, LuWifi } from "react-icons/lu";
import type { ConnectionState, ConnectionStatus } from "@/data/schemas/connection-state";

interface ConnectionStatusProps {
    connectionState: ConnectionState;
}

const STATUS_CONFIG: Record<Exclude<ConnectionStatus, 'disconnecting'>, {
    icon: React.ReactNode;
    className: string;
    message: string;
}> = {
    connected: {
        icon: <LuWifi className="w-4 h-4" />,
        className: "bg-secondary/90 border-secondary-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Connected"
    },
    error: {
        icon: <FaCircleExclamation className="w-4 h-4" />,
        className: "bg-primary/90 border-primary-dark/50 text-white bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Something went wrong"
    },
    connecting: {
        icon: <LuLoader className="w-4 h-4 animate-spin" />,
        className: "bg-accent/90 border-accent-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Connecting..."
    },
    reconnecting: {
        icon: <LuLoader className="w-4 h-4 animate-spin" />,
        className: "bg-accent/90 border-accent-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Reconnecting..."
    },
    disconnected: {
        icon: <LuWifiOff className="w-4 h-4" />,
        className: "bg-contrast-subtle/90 border-contrast/50 text-background-light bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Not connected"
    },
    idle: {
        icon: <LuWifiOff className="w-4 h-4" />,
        className: "bg-contrast-subtle/90 border-contrast/50 text-background-light bg-opacity-90 border shadow-lg backdrop-blur-sm",
        message: "Not connected"
    }
};

export function ConnectionStatus({ connectionState }: ConnectionStatusProps) {
    const statusConfig = useMemo(() => {
        if (connectionState.status === 'disconnecting') {
            return undefined;
        }
        return STATUS_CONFIG[connectionState.status];
    }, [connectionState.status]);

    if (!statusConfig) {
        return null;
    }

    return (
        <AnimatePresence mode="wait">
            <motion.div
                initial={{ opacity: 0, y: -20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -20, scale: 0.95 }}
                transition={{ 
                    type: "spring", 
                    damping: 25, 
                    stiffness: 200,
                    staggerChildren: 0.1
                }}
                className={`absolute top-6 right-4 z-50 flex flex-col items-end gap-1`}
            >
                <motion.div 
                    className={`flex items-center gap-2 rounded-lg px-2 py-2 group ${statusConfig.className}`}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ 
                        type: "spring",
                        stiffness: 300,
                        damping: 25,
                        mass: 0.5
                    }}
                >
                    <motion.div
                        animate={connectionState.status === 'connected' ? { scale: [1, 1.2, 1] } : {}}
                        transition={{ duration: 0.5, ease: "easeInOut" }}
                        className="flex items-center justify-center"
                    >
                        {statusConfig.icon}
                    </motion.div>
                    <motion.span 
                        className="text-sm font-medium hidden group-hover:inline"
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ 
                            type: "spring",
                            stiffness: 300,
                            damping: 25,
                            mass: 0.5
                        }}
                    >
                        {statusConfig.message}
                    </motion.span>
                </motion.div>

                <AnimatePresence>
                    {connectionState.errorMessage && (
                        <motion.div 
                            initial={{ opacity: 0, height: 0, y: -10 }}
                            animate={{ opacity: 1, height: "auto", y: 0 }}
                            exit={{ opacity: 0, height: 0, y: -10 }}
                            transition={{ 
                                type: "spring",
                                stiffness: 300,
                                damping: 25,
                                mass: 0.5
                            }}
                            className="group text-sm flex items-start text-white bg-primary/90 backdrop-blur-sm border border-primary-dark/50 px-2 py-2 rounded-lg max-w-96 shadow-lg"
                        >
                            <motion.div
                                className="flex-shrink-0 md:mt-0.5"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ 
                                    type: "spring",
                                    stiffness: 300,
                                    damping: 25,
                                    mass: 0.5
                                }}
                            >
                                <FaCircleExclamation className="w-4 h-4" />
                            </motion.div>
                            <motion.div 
                                className="flex-1 min-w-0"
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                transition={{ 
                                    type: "spring",
                                    stiffness: 300,
                                    damping: 25,
                                    mass: 0.5
                                }}
                            >
                                <span className="hidden group-hover:inline text-sm break-words ml-2">
                                    {connectionState.errorMessage}
                                </span>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </motion.div>
        </AnimatePresence>
    );
}