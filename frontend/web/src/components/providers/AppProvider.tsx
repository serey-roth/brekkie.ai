import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { SupabaseAuthApiClient } from '@/api-clients/auth';
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

    const threadsApiClient = useRef<ThreadsApiClient>(new ThreadsApiClient(config.apiBaseUrl));
    const userAccessApiClient = useRef<UserAccessApiClient>(
        new UserAccessApiClient(config.apiBaseUrl),
    );
    const recipesApiClient = useRef<RecipesApiClient>(new RecipesApiClient(config.apiBaseUrl));
    const supabaseAuthApiClient = useRef<SupabaseAuthApiClient>(new SupabaseAuthApiClient());

    const userAccessManager = useRef<UserAccessManager>(
        new UserAccessManager(userAccessApiClient.current, {
            maxMessageCountAnonymous: config.maxMessageCountAnonymous,
            maxMessageCountAuthenticated: config.maxMessageCountAuthenticated,
        }),
    );

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

    const [showRecipeListView, setShowRecipeListViewState] = useState(true);
    const setShowRecipeListView = useCallback((show: boolean) => {
        setShowRecipeListViewState(show);
    }, []);

    const value = useMemo<AppContextType>(
        () => ({
            config,
            apiClients: {
                threadsApiClient: threadsApiClient.current,
                userAccessApiClient: userAccessApiClient.current,
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
                showRecipeListView,
                setShowRecipeListView,
            },
        }),
        [
            config,
            isSidebarOpen,
            setIsSidebarOpen,
            selectedRecipeId,
            setSelectedRecipeId,
            showRecipeListView,
            setShowRecipeListView,
        ],
    );

    useEffect(() => {
        const checkAuth = async () => {
            const claims = await supabaseAuthApiClient.current.getClaims();
            const authExpirationDate = new Date(claims.exp * 1000);
            const currentDate = new Date();
            if (currentDate > authExpirationDate) {
                await supabaseAuthApiClient.current.logout();
                await userAccessApiClient.current.createAnonymousAccess();
                userAccessManager.current.resetState();
            } else {
                userAccessManager.current.ensureUserAccess();
            }
        };
        checkAuth();
    }, []);

    return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
