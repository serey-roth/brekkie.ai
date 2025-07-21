import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { RecipesApiClient } from '@/api-clients/recipes';
import { ThreadsApiClient } from '@/api-clients/threads';
import { UserAccessApiClient } from '@/api-clients/user-access';
import { getConfigWithOverrides, type EnvironmentConfig } from '@/config/environment';
import { AppContext, type AppContextType } from '@/context/app-context';
import { UserAccessManager } from '@/managers/user-access-manager';

interface AppProviderProps {
    children: React.ReactNode;
    config?: Partial<EnvironmentConfig>;
}

export function AppProvider({ children, config: customConfig }: AppProviderProps) {
    const config = useMemo<EnvironmentConfig>(
        () => ({
            ...getConfigWithOverrides(),
            ...customConfig,
        }),
        [customConfig],
    );

    console.log('config', config);

    const threadsApiClient = useRef<ThreadsApiClient>(new ThreadsApiClient(config.apiBaseUrl));
    const userAccessApiClient = useRef<UserAccessApiClient>(
        new UserAccessApiClient(config.apiBaseUrl),
    );
    const recipesApiClient = useRef<RecipesApiClient>(new RecipesApiClient(config.apiBaseUrl));

    const userAccessManager = useRef<UserAccessManager>(
        new UserAccessManager(userAccessApiClient.current, {
            maxMessageCountAnonymous: config.maxMessageCountAnonymous,
            maxMessageCountAuthenticated: config.maxMessageCountAuthenticated,
        }),
    );

    const [isSidebarOpen, setIsSidebarOpen] = useState(
        localStorage.getItem('brekkie-sidebar-state') === 'open',
    );

    const openSidebar = useCallback(() => {
        setIsSidebarOpen(true);
        localStorage.setItem('brekkie-sidebar-state', 'open');
    }, [setIsSidebarOpen]);

    const closeSidebar = useCallback(() => {
        setIsSidebarOpen(false);
        localStorage.setItem('brekkie-sidebar-state', 'closed');
    }, [setIsSidebarOpen]);

    const value = useMemo<AppContextType>(
        () => ({
            config,
            apiClients: {
                threadsApiClient: threadsApiClient.current,
                userAccessApiClient: userAccessApiClient.current,
                recipesApiClient: recipesApiClient.current,
            },
            managers: {
                userAccessManager: userAccessManager.current,
            },
            state: {
                isSidebarOpen,
                openSidebar,
                closeSidebar,
            },
        }),
        [config, isSidebarOpen, openSidebar, closeSidebar],
    );

    useEffect(() => {
        userAccessManager.current.ensureUserAccess();
    }, []);

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
