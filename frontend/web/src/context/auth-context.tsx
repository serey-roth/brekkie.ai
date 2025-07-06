import { createContext, useContext } from 'react';
import type { UserSigninPayload, UserSignupPayload } from '@/data/schemas/users';

interface AuthContextType {
    isSubmitting: boolean;
    error: string | null;
    signin: (payload: UserSigninPayload) => Promise<void>;
    signup: (payload: UserSignupPayload) => Promise<void>;
    signout: () => Promise<void>;

    isAuthModalOpen: boolean;
    authModalMode: 'login' | 'register';
    openAuthModal: (mode?: 'login' | 'register') => void;
    closeAuthModal: () => void;
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

function useAuthContext() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}

export const useAuthModal = () => {
    const ctx = useAuthContext();
    const isAuthModalOpen = ctx.isAuthModalOpen;
    const authModalMode = ctx.authModalMode;
    const openAuthModal = ctx.openAuthModal;
    const closeAuthModal = ctx.closeAuthModal;
    return { isAuthModalOpen, authModalMode, openAuthModal, closeAuthModal };
};

export const useAuth = () => {
    const ctx = useAuthContext();
    const isSubmitting = ctx.isSubmitting;
    const error = ctx.error;
    const signin = ctx.signin;
    const signup = ctx.signup;
    const signout = ctx.signout;
    return { isSubmitting, error, signin, signup, signout };
};
