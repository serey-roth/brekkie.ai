import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppConfig, useSupabaseAuthApiClient } from '@/context/app-context';
import { UserAccessSchema, type UserAccess } from '@/data/schemas/user-access';
import type { AuthChangeEvent, Session } from '@/supabase-client';

export const useSupabaseAuth = () => {
    const { appBaseUrl, apiBaseUrl } = useAppConfig();
    const supabaseAuthApiClient = useSupabaseAuthApiClient();
    const navigate = useNavigate();

    const loginWithGoogle = useCallback(async () => {
        try {
            const url = await supabaseAuthApiClient.googleLogin(
                `${appBaseUrl}/auth/callback`,
            );
            window.location.href = url;
        } catch (error) {
            console.error(error);
            throw error;
        }
    }, [supabaseAuthApiClient, appBaseUrl]);

    const loginWithEmail = useCallback(
        async (email: string, password: string) => {
            try {
                await supabaseAuthApiClient.emailLogin(email, password);
                navigate(`${appBaseUrl}/auth/callback`);
            } catch (error) {
                console.error(error);
                throw error;
            }
        },
        [supabaseAuthApiClient, navigate, appBaseUrl],
    );

    const signUpWithEmail = useCallback(
        async (email: string, password: string) => {
            try {
                await supabaseAuthApiClient.emailSignUp(email, password);
                navigate(`${appBaseUrl}/auth/callback`);
            } catch (error) {
                console.error(error);
                throw error;
            }
        },
        [supabaseAuthApiClient, navigate, appBaseUrl],
    );

    const resetPassword = useCallback(
        async (email: string) => {
            try {
                await supabaseAuthApiClient.resetPassword(email);
            } catch (error) {
                console.error(error);
                throw error;
            }
        },
        [supabaseAuthApiClient],
    );

    const logout = useCallback(async () => {
        try {
            await supabaseAuthApiClient.logout();
            navigate('/auth');
        } catch (error) {
            console.error(error);
            throw error;
        }
    }, [supabaseAuthApiClient, navigate]);

    const verifyJWT = async (): Promise<UserAccess> => {
        const session = await supabaseAuthApiClient.getSession();
        if (!session) {
            throw new Error('No session found');
        }
        const accessToken = session.access_token;
        const response = await fetch(`${apiBaseUrl}/auth/verify-jwt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
                Authorization: `Bearer ${accessToken}`,
            },
            credentials: 'include',
        });
        if (!response.ok) {
            throw new Error('Failed to verify token');
        }
        const json = await response.json();
        const userAccess = UserAccessSchema.safeParse(json);
        if (!userAccess.success) {
            throw new Error('Failed to verify token');
        }
        return userAccess.data;
    };

    const getClaims = useCallback(async () => {
        const claims = await supabaseAuthApiClient.getClaims();
        return claims;
    }, [supabaseAuthApiClient]);

    const addAuthStateChangeListener = useCallback(
        (callback: (event: AuthChangeEvent, session: Session | null) => void) => {
            const { data } = supabaseAuthApiClient.listenForAuthStateChanges(callback);
            return data.subscription.unsubscribe;
        },
        [supabaseAuthApiClient],
    );

    return {
        loginWithGoogle,
        loginWithEmail,
        signUpWithEmail,
        resetPassword,
        logout,
        verifyJWT,
        addAuthStateChangeListener,
        getClaims,
    };
};
