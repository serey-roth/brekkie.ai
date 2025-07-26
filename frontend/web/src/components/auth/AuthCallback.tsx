import { motion } from 'framer-motion';
import { Utensils } from 'lucide-react';
import { useLayoutEffect, useState, useCallback, useRef } from 'react';
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';

const LoadingAnimation = ({ name }: { name: string | undefined }) => (
    <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center space-y-6">
            <div className="text-primary/40 flex items-center justify-center">
                <Utensils className="h-24 w-24" />
            </div>

            <motion.div
                className="text-center"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <h2 className="text-contrast font-heading text-xl font-semibold">
                    Welcome back{name ? `, ${name}!` : '!'}
                </h2>
                <p className="text-contrast-subtle mt-2 text-sm">
                    Just a moment while we get everything ready…
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

            <motion.div
                className="absolute inset-0 -z-10"
                animate={{
                    background: [
                        'radial-gradient(circle at 20% 80%, rgba(248, 102, 115, 0.1) 0%, transparent 50%)',
                        'radial-gradient(circle at 80% 20%, rgba(185, 227, 198, 0.1) 0%, transparent 50%)',
                        'radial-gradient(circle at 40% 40%, rgba(168, 213, 186, 0.1) 0%, transparent 50%)',
                        'radial-gradient(circle at 20% 80%, rgba(248, 102, 115, 0.1) 0%, transparent 50%)',
                    ],
                }}
                transition={{
                    duration: 4,
                    ease: 'easeInOut',
                    repeat: Infinity,
                }}
            />
        </div>
    </div>
);

const ErrorAnimation = () => (
    <motion.div
        className="bg-background flex min-h-screen items-center justify-center"
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
            <div className="flex items-center justify-center">
                <Utensils className="h-24 w-24 text-red-500" />
            </div>
            <div>
                <h2 className="text-contrast font-heading text-lg font-semibold">
                    Authentication Failed
                </h2>
                <p className="text-contrast-subtle mt-1 text-sm">
                    Redirecting you back to the home page...
                </p>
            </div>
        </motion.div>
    </motion.div>
);

export function AuthCallback() {
    const [authError, setAuthError] = useState(false);
    const hasExecutedRef = useRef(false);

    const { user, isAuthenticated, verifyJWT, logout } = useAuth();
    const navigate = useNavigate();

    const [searchParams] = useSearchParams();
    const from = searchParams.get('from');

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
                }, 500);
            } else {
                throw new Error('User not authenticated');
            }
        } catch (error) {
            console.error('Auth verification failed:', error);
            setAuthError(true);

            try {
                await logout();
            } catch (logoutError) {
                console.error('Failed to logout from Auth0:', logoutError);
                setTimeout(() => {
                    navigate('/');
                }, 2000);
            }
        }
    }, [verifyJWT, navigate, logout]);

    useLayoutEffect(() => {
        handleAuthCallback();
    }, [handleAuthCallback]);

    if (from !== 'auth0') {
        return <Navigate to="/" />;
    }

    if (authError) {
        return <ErrorAnimation />;
    }

    if (isAuthenticated) {
        return <LoadingAnimation name={user?.name} />;
    }

    return <></>;
}
