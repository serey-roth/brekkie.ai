import { motion } from 'framer-motion';
import { useMemo } from 'react';
import { FaCircleExclamation } from 'react-icons/fa6';
import { LuWifiOff, LuLoader, LuWifi } from 'react-icons/lu';
import type { ConnectionStatus } from '@/data/schemas/connection-state';

interface ConnectionStatusProps {
    status: ConnectionStatus;
}

const STATUS_CONFIG: Record<
    Exclude<ConnectionStatus, 'disconnecting'>,
    {
        icon: React.ReactNode;
        className: string;
        message: string;
    }
> = {
    connected: {
        icon: <LuWifi className="h-4 w-4" />,
        className:
            'bg-secondary/90 border-secondary-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Connected',
    },
    error: {
        icon: <FaCircleExclamation className="h-4 w-4" />,
        className:
            'bg-primary/90 border-primary-dark/50 text-white bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Something went wrong',
    },
    connecting: {
        icon: <LuLoader className="h-4 w-4 animate-spin" />,
        className:
            'bg-accent/90 border-accent-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Connecting...',
    },
    reconnecting: {
        icon: <LuLoader className="h-4 w-4 animate-spin" />,
        className:
            'bg-accent/90 border-accent-dark/50 text-contrast bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Reconnecting...',
    },
    disconnected: {
        icon: <LuWifiOff className="h-4 w-4" />,
        className:
            'bg-contrast-subtle/90 border-contrast/50 text-background-light bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Not connected',
    },
    idle: {
        icon: <LuWifiOff className="h-4 w-4" />,
        className:
            'bg-contrast-subtle/90 border-contrast/50 text-background-light bg-opacity-90 border shadow-lg backdrop-blur-sm',
        message: 'Not connected',
    },
};

export function ConnectionStatusNotification({ status }: ConnectionStatusProps) {
    const statusConfig = useMemo(() => {
        if (status === 'disconnecting') {
            return undefined;
        }
        return STATUS_CONFIG[status];
    }, [status]);

    if (!statusConfig) {
        return null;
    }

    return (
        <motion.div
            className={`group flex items-center gap-2 rounded-lg px-2 py-2 ${statusConfig.className}`}
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{
                type: 'spring',
                stiffness: 300,
                damping: 25,
                mass: 0.5,
            }}
        >
            <motion.div
                animate={
                    status === 'connected' ? { scale: [1, 1.2, 1] } : {}
                }
                transition={{ duration: 0.5, ease: 'easeInOut' }}
                className="flex items-center justify-center"
            >
                {statusConfig.icon}
            </motion.div>
            <motion.span
                className="hidden text-sm font-medium group-hover:inline"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{
                    type: 'spring',
                    stiffness: 300,
                    damping: 25,
                    mass: 0.5,
                }}
            >
                {statusConfig.message}
            </motion.span>
        </motion.div>
    );
}
