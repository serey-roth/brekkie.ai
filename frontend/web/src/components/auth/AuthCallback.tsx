import { motion } from 'framer-motion';
import { useLayoutEffect, useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useUserAccessManager } from '@/context/app-context';
import { useSupabaseAuth } from '@/hooks/use-supabase-auth';
import type { AuthChangeEvent, User, Session as AuthSession } from '@/supabase-client';

const LoadingAnimation = ({ name }: { name: string | undefined }) => (
    <div className="bg-background-light flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center space-y-6">
            <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="mb-12 inline-flex items-center justify-center gap-3"
            >
                <Link to="/" className="inline-flex items-center justify-center gap-3">
                    <img src="/brekkie-logo.png" alt="Brekkie Logo" className="h-12 w-12" />
                    <h1 className="text-contrast text-2xl font-medium">brekkie.ai</h1>
                </Link>
            </motion.div>

            <motion.div
                className="text-center"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
            >
                <h2 className="text-contrast mb-2 text-2xl leading-tight font-medium">
                    Hey there{name ? `, ${name}!` : '!'}
                </h2>
                <p className="text-contrast-subtle text-base">
                    Almost there, just getting things sorted for you...
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

const ErrorAnimation = () => (
    <motion.div
        className="bg-background-light flex min-h-screen items-center justify-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
    >
        <motion.div
            className="flex flex-col items-center space-y-4 text-center"
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
        >
            <motion.div
                initial={{ scale: 0.8 }}
                animate={{ scale: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                className="mb-12 inline-flex items-center justify-center gap-3"
            >
                <Link to="/" className="inline-flex items-center justify-center gap-3">
                    <img src="/brekkie-logo.png" alt="Brekkie Logo" className="h-12 w-12" />
                    <h1 className="text-contrast text-2xl font-medium">brekkie.ai</h1>
                </Link>
            </motion.div>
            <div>
                <h2 className="text-contrast mb-2 text-2xl leading-tight font-medium">
                    Oops! Something went wrong
                </h2>
                <p className="text-contrast-subtle text-base">
                    Redirecting you to sign in...
                </p>
            </div>

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
        </motion.div>
    </motion.div>
);

export function AuthCallback() {
    const hasExecutedRef = useRef(false);
    const [authError, setAuthError] = useState(false);
    const [user, setUser] = useState<User | null>(null);

    const userAccessManager = useUserAccessManager();   
    const { verifyJWT, logout, getClaims, addAuthStateChangeListener } = useSupabaseAuth();
    const navigate = useNavigate();

    useEffect(() => {
        const listener = (event: AuthChangeEvent, session: AuthSession | null) => {
            if (event === 'SIGNED_IN' && session?.user) {
                setUser(session.user);
            }
        };
        const unsubscribe = addAuthStateChangeListener(listener);
        return () => {
            unsubscribe();
        };
    }, [addAuthStateChangeListener]);

    const handleAuthCallback = useCallback(async () => {
        if (hasExecutedRef.current) {
            return;
        }
        hasExecutedRef.current = true;

        try {
            const userAccess = await verifyJWT();
            if (userAccess.is_authenticated) {
                setTimeout(() => {
                    navigate('/');
                }, 1000);
            } else {
                console.error('Failed to authenticate user');
                setAuthError(true);
                setTimeout(() => {
                    navigate('/auth');
                }, 1000);
            }
        } catch (error) {
            console.error('Auth verification failed:', error);
            setAuthError(true);
            try {
                const claims = await getClaims();
                if (claims.aud === 'authenticated') {
                    await logout();
                    await userAccessManager.revokeAccess();
                } else {
                    setTimeout(() => {
                        navigate('/auth');
                    }, 1000);
                }
            } catch {
                console.error('Failed to logout');
                setTimeout(() => {
                    navigate('/auth');
                }, 1000);
            }
        }
    }, [verifyJWT, navigate, logout, getClaims, userAccessManager]);

    useLayoutEffect(() => {
        handleAuthCallback();
    }, [handleAuthCallback]);

    if (authError) {
        return <ErrorAnimation />;
    }

    if (user) {
        return <LoadingAnimation name={user.user_metadata?.name} />;
    }

    return <ErrorAnimation />;
}
