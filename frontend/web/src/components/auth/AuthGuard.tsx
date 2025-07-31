import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';
import { Navigate } from 'react-router-dom';
import { useUserAccessManager } from '@/context/app-context';
import { useSupabaseAuth } from '@/hooks/use-supabase-auth';

interface AuthGuardProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
}

const LoadingAnimation = () => (
    <div className="bg-background-light flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center space-y-6">
            <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="mb-12 inline-flex items-center justify-center gap-3"
            >
                <img src="/brekkie-logo.png" alt="Brekkie Logo" className="h-12 w-12" />
                <h1 className="text-contrast text-2xl font-semibold">brekkie.ai</h1>
            </motion.div>

            <motion.div
                className="text-center"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
            >
                <h2 className="text-contrast mb-2 text-2xl leading-tight font-semibold">
                    Getting you set up...
                </h2>
                <p className="text-contrast-subtle text-base">
                    Hang tight, we're getting everything ready for you!
                </p>
            </motion.div>

            <div className="flex space-x-2">
                {[0, 1, 2].map((index) => (
                    <motion.div
                        key={index}
                        className="bg-primary h-2 w-2 rounded-full"
                        animate={{
                            scale: [1, 1.5, 1],
                            opacity: [0.5, 1, 0.5],
                        }}
                        transition={{
                            duration: 1.5,
                            ease: 'easeInOut',
                            repeat: Infinity,
                            delay: index * 0.2,
                        }}
                    />
                ))}
            </div>
        </div>
    </div>
);

export function AuthGuard({ children, fallback }: AuthGuardProps) {
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const { getClaims, logout } = useSupabaseAuth();

    const userAccessManager = useUserAccessManager();

    useEffect(() => {
        const verifyAuth = async () => {
            try {
                const claims = await getClaims();
                if (claims.aud === 'authenticated') {
                    const expirationDate = new Date(claims.exp * 1000);
                    const currentDate = new Date();
                    if (currentDate > expirationDate) {
                        await logout();
                        await userAccessManager.revokeAccess();
                        setIsAuthenticated(false);
                    } else {
                        await userAccessManager.ensureAccess();
                        setIsAuthenticated(true);
                    }
                } else {
                    await userAccessManager.revokeAccess();
                    setIsAuthenticated(false);
                }
            } catch (error) {
                console.error('Error checking authentication:', error);
                setIsAuthenticated(false);
                await userAccessManager.revokeAccess();
            } finally {
                setIsLoading(false);
            }
        };

        verifyAuth();
    }, [getClaims, logout, userAccessManager]);

    if (isLoading) {
        return fallback || <LoadingAnimation />;
    }

    if (!isAuthenticated) {
        return <Navigate to="/auth" replace />;
    }

    return <>{children}</>;
}
