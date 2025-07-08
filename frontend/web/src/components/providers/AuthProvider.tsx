import { useState, useCallback } from 'react';
import { useAuthApiClient, useUserAccessManager } from '@/context/app-context';
import { AuthContext } from '@/context/auth-context';
import { type UserSigninPayload, type UserSignupPayload } from '@/data/schemas/users';

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [authModalMode, setAuthModalMode] = useState<'login' | 'register'>('login');

    const authClient = useAuthApiClient();
    const userAccessManager = useUserAccessManager();

    const signin = useCallback(
        async (payload: UserSigninPayload) => {
            setIsSubmitting(true);
            setError(null);
            try {
                const accessData = await authClient.signin(payload);
                userAccessManager.setUserAccessData(accessData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to sign in');
                throw err;
            } finally {
                setIsSubmitting(false);
            }
        },
        [authClient, userAccessManager],
    );

    const signup = useCallback(
        async (payload: UserSignupPayload) => {
            setIsSubmitting(true);
            setError(null);
            try {
                const accessData = await authClient.signup(payload);
                userAccessManager.setUserAccessData(accessData);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to sign up');
                throw err;
            } finally {
                setIsSubmitting(false);
            }
        },
        [authClient, userAccessManager],
    );

    const signout = useCallback(async () => {
        await authClient.signout();
        await userAccessManager.ensureUserAccess();
    }, [authClient, userAccessManager]);

    const openAuthModal = useCallback((mode?: 'login' | 'register') => {
        setIsAuthModalOpen(true);
        setAuthModalMode(mode ?? 'login');
    }, []);

    const closeAuthModal = useCallback(() => {
        setIsAuthModalOpen(false);
        setAuthModalMode('login');
    }, []);

    return (
        <AuthContext.Provider
            value={{
                signin,
                signup,
                signout,
                isSubmitting,
                error,
                isAuthModalOpen,
                openAuthModal,
                authModalMode,
                closeAuthModal,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}
