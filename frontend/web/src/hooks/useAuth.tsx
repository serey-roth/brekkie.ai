import { useAuth0 } from '@auth0/auth0-react';
import { useCallback } from 'react';
import { useAppConfig } from '@/context/app-context';
import { UserAccessSchema, type UserAccess } from '@/data/schemas/user-access';

export const useAuth = () => {
    const { apiBaseUrl } = useAppConfig();

    const {
        loginWithRedirect,
        loginWithPopup,
        logout: logoutAuth0,
        isAuthenticated,
        user,
        isLoading,
        getAccessTokenSilently,
    } = useAuth0();

    const login = useCallback(
        async (options?: {
            authorizationParams?: {
                screen_hint?: 'login' | 'signup';
                login_hint?: string;
                connection?: string;
            };
            appState?: {
                returnTo?: string;
            };
        }) => {
            return loginWithRedirect(options);
        },
        [loginWithRedirect],
    );

    const loginWithPopupMethod = useCallback(
        async (options?: {
            authorizationParams?: {
                screen_hint?: 'login' | 'signup';
                login_hint?: string;
                connection?: string;
            };
            appState?: {
                returnTo?: string;
            };
        }) => {
            return loginWithPopup(options);
        },
        [loginWithPopup],
    );

    const logout = useCallback(
        async (redirectTo?: string) => {
            await logoutAuth0({
                logoutParams: {
                    returnTo: redirectTo ?? window.location.origin,
                },
            });
        },
        [logoutAuth0],
    );

    const verifyJWT = async (): Promise<UserAccess> => {
        const accessToken = await getAccessTokenSilently();
        const response = await fetch(`${apiBaseUrl}/auth/verify-token`, {
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

    return {
        login,
        loginWithPopup: loginWithPopupMethod,
        logout,
        isAuthenticated,
        user,
        isSubmitting: isLoading,
        verifyJWT,
    };
};
