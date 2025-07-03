import { createContext, useContext } from 'react';
import { HttpAccessTokenClient } from '@/api-clients/access-token-client';
import { HttpAuthClient } from '@/api-clients/auth-client';
import { HttpRecipesClient } from '@/api-clients/recipes-client';
import { HttpThreadsClient } from '@/api-clients/threads-client';
import { type EnvironmentConfig } from '@/config/environment';
import type { UserAccessManager } from '@/managers/user-access-manager';


interface ApiClients {
    authClient: HttpAuthClient;
    threadsClient: HttpThreadsClient;
    accessTokenClient: HttpAccessTokenClient;
    recipesClient: HttpRecipesClient;
}

interface AppManagers {
    userAccessManager: UserAccessManager;
}

export interface AppContextType {
    config: EnvironmentConfig;
    apiClients: ApiClients;
    managers: AppManagers;
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

export function useAuthApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.authClient;
}

export function useThreadsApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.threadsClient;
}

export function useAccessTokenApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.accessTokenClient;
}

export function useRecipesApiClient() {
    const { apiClients } = useAppContext();
    return apiClients.recipesClient;
}   

export function useUserAccessManager() {
    const { managers } = useAppContext();
    return managers.userAccessManager;
}