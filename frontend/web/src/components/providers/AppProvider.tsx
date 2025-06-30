import { useEffect, useMemo, useRef } from 'react';
import { HttpAccessTokenClient } from '@/api-clients/access-token-client';
import { HttpAuthClient } from '@/api-clients/auth-client';
import { HttpThreadsClient } from '@/api-clients/threads-client';
import { getConfigWithOverrides, type EnvironmentConfig } from '@/config/environment';
import { AppContext, type AppContextType } from '@/context/app-context';
import { UserAccessManager } from '@/managers/user-access-manager';

interface AppProviderProps {
    children: React.ReactNode;
    config?: Partial<EnvironmentConfig>;
}

export function AppProvider({ children, config: customConfig }: AppProviderProps) {
    const config = useMemo<EnvironmentConfig>(() => ({
        ...getConfigWithOverrides(),
        ...customConfig,
    }), [customConfig]);

    const authClient = useRef<HttpAuthClient>(new HttpAuthClient(config.apiBaseUrl));
    const threadsClient = useRef<HttpThreadsClient>(new HttpThreadsClient(config.apiBaseUrl));
    const accessTokenClient = useRef<HttpAccessTokenClient>(new HttpAccessTokenClient(config.apiBaseUrl));

    const userAccessManager = useRef<UserAccessManager>(new UserAccessManager(
        accessTokenClient.current,
        {
            maxMessageCountAnonymous: config.maxMessageCountAnonymous,
            maxMessageCountAuthenticated: config.maxMessageCountAuthenticated,
        }
    ));

    const value = useMemo<AppContextType>(() => ({
        config,
        apiClients: {
            authClient: authClient.current,
            threadsClient: threadsClient.current,
            accessTokenClient: accessTokenClient.current,
        },
        managers: {
            userAccessManager: userAccessManager.current,
        },
    }), [config, authClient, threadsClient, accessTokenClient, userAccessManager]);

    useEffect(() => {
        userAccessManager.current.ensureUserAccess();
    }, [userAccessManager]);

    return (
        <AppContext.Provider value={value}>
            {children}
        </AppContext.Provider>
    );
} 