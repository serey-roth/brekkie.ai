import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAppConfig, useSupabaseAuthApiClient } from '@/context/app-context';
import type { AuthChangeEvent, Session } from '@/supabase-client';

export const useSupabaseAuth = () => {
    const { apiBaseUrl, appBaseUrl } = useAppConfig();
    const supabaseAuthApiClient = useSupabaseAuthApiClient();
    const navigate = useNavigate();

    const loginWithGoogle = useCallback(async () => {
        try {
            const url = await supabaseAuthApiClient.googleLogin(`${appBaseUrl}/auth/callback`);
            navigate(url);
        } catch (error) {
            console.error(error);
            throw error;
        }
    }, [supabaseAuthApiClient, navigate, appBaseUrl]);

    const logout = useCallback(async () => {
        try {
            await supabaseAuthApiClient.logout();
            navigate('/auth');
        } catch (error) {
            console.error(error);
            throw error;
        }
    }, [supabaseAuthApiClient, navigate]);

    const verifyJWT = async (): Promise<{ user_id: string; jwt: string }> => {
        const session = await supabaseAuthApiClient.getSession();
        if (!session) {
            throw new Error('No session found');
        }
        const jwt = session.access_token;
        const response = await fetch(`${apiBaseUrl}/auth/verify-jwt`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                Accept: 'application/json',
                Authorization: `Bearer ${jwt}`,
            },
        });
        if (!response.ok) {
            throw new Error('Failed to verify token');
        }
        const json = await response.json();
        if (!json.user_id) {
            throw new Error('Failed to verify token');
        }
        return { user_id: json.user_id, jwt };
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
        logout,
        verifyJWT,
        addAuthStateChangeListener,
        getClaims,
    };
};
