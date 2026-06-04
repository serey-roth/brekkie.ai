import { useCallback, useMemo, useRef, useState } from 'react';
import { SupabaseAuthApiClient } from '@/api-clients/auth';
import { RecipesApiClient } from '@/api-clients/recipes';
import { ThreadsApiClient } from '@/api-clients/threads';
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

    const userAccessManager = useRef<UserAccessManager>(new UserAccessManager());

    const threadsApiClient = useRef<ThreadsApiClient>(
        new ThreadsApiClient(config.apiBaseUrl, () => userAccessManager.current.getJwt()),
    );
    const recipesApiClient = useRef<RecipesApiClient>(
        new RecipesApiClient(config.apiBaseUrl, () => userAccessManager.current.getJwt()),
    );
    const supabaseAuthApiClient = useRef<SupabaseAuthApiClient>(new SupabaseAuthApiClient());

    const [isSidebarOpen, setIsSidebarOpenState] = useState(
        localStorage.getItem('brekkie-sidebar-state') === 'open',
    );
    const setIsSidebarOpen = useCallback((isOpen: boolean) => {
        localStorage.setItem('brekkie-sidebar-state', isOpen ? 'open' : 'closed');
        setIsSidebarOpenState(isOpen);
    }, []);

    const [selectedRecipeId, setSelectedRecipeIdState] = useState<string | null>(null);
    const setSelectedRecipeId = useCallback((recipeId: string | null) => {
        setSelectedRecipeIdState(recipeId);
    }, []);

    const value = useMemo<AppContextType>(
        () => ({
            config,
            apiClients: {
                threadsApiClient: threadsApiClient.current,
                recipesApiClient: recipesApiClient.current,
                supabaseAuthApiClient: supabaseAuthApiClient.current,
            },
            managers: {
                userAccessManager: userAccessManager.current,
            },
            state: {
                isSidebarOpen,
                setIsSidebarOpen,
                selectedRecipeId,
                setSelectedRecipeId,
            },
        }),
        [config, isSidebarOpen, setIsSidebarOpen, selectedRecipeId, setSelectedRecipeId],
    );

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
