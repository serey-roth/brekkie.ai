import { createContext, useContext } from 'react';
import { RecipesApiClient } from '@/api-clients/recipes';
import { ThreadsApiClient } from '@/api-clients/threads';
import { UserAccessApiClient } from '@/api-clients/user-access';
import { type EnvironmentConfig } from '@/config/environment';
import type { UserAccessManager } from '@/managers/user-access-manager';

interface ApiClients {
    threadsApiClient: ThreadsApiClient;
    userAccessApiClient: UserAccessApiClient;
    recipesApiClient: RecipesApiClient;
}

interface AppManagers {
    userAccessManager: UserAccessManager;
}

export interface AppState {
    isSidebarOpen: boolean;
    openSidebar: () => void;
    closeSidebar: () => void;
}

export interface AppContextType {
    config: EnvironmentConfig;
    apiClients: ApiClients;
    managers: AppManagers;
    state: AppState;
}

export const AppContext = createContext<AppContextType | undefined>(undefined);

export function useAppContext() {
    const context = useContext(AppContext);
    if (!context) {
        throw new Error('useAppContext must be used within a AppProvider');
    }
    return context;
}

export function useAppConfig() {
    const { config } = useAppContext();
    return config;
}

export function useApiClients() {
    const { apiClients } = useAppContext();
    return apiClients;
}

export function useThreadsApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.threadsApiClient;
}

export function useUserAccessApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.userAccessApiClient;
}

export function useRecipesApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.recipesApiClient;
}

export function useUserAccessManager() {
    const { managers } = useAppContext();
    return managers.userAccessManager;
}

export function useAppState() {
    const { state } = useAppContext();
    return state;
}
