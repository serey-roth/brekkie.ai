export interface EnvironmentConfig {
    appBaseUrl: string;
    apiBaseUrl: string;
    wsBaseUrl: string;
    isDevelopment: boolean;
    isProduction: boolean;
    isTest: boolean;
    isStaging: boolean;
    version?: string;
    enableDebugLogging?: boolean;
    enableAnalytics?: boolean;
    maxMessageCountAnonymous: number;
    maxMessageCountAuthenticated: number;
    featureFlags: {
        enableAuth: boolean;
    };
    supabaseUrl: string;
    supabaseApiKey: string;
}

function getEnvVar(key: string, fallback: string): string {
    return import.meta.env[key] || fallback;
}

const developmentConfig: EnvironmentConfig = {
    appBaseUrl: 'http://localhost:5173',
    apiBaseUrl: 'http://localhost:8000/api',
    wsBaseUrl: 'ws://localhost:8000/ws',
    supabaseUrl: 'https://supabase-project.supabase.co',
    supabaseApiKey: 'supabase_api_key',
    isDevelopment: true,
    isProduction: false,
    isTest: false,
    isStaging: false,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 25,
    featureFlags: {
        enableAuth: true,
    },
};

const productionConfig: EnvironmentConfig = {
    appBaseUrl: 'https://brekkie-ai.fly.dev',
    apiBaseUrl: 'https://brekkie-ai.fly.dev/api',
    wsBaseUrl: 'wss://brekkie-ai.fly.dev/ws',
    supabaseUrl: 'https://supabase-project.supabase.co',
    supabaseApiKey: 'supabase_api_key',
    isDevelopment: false,
    isProduction: true,
    isTest: false,
    isStaging: false,
    enableDebugLogging: false,
    enableAnalytics: true,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 25,
    featureFlags: {
        enableAuth: true,
    },
};

const stagingConfig: EnvironmentConfig = {
    appBaseUrl: 'https://brekkie-ai-staging.fly.dev',
    apiBaseUrl: 'https://brekkie-ai-staging.fly.dev/api',
    wsBaseUrl: 'wss://brekkie-ai-staging.fly.dev/ws',
    supabaseUrl: 'https://supabase-project.supabase.co',
    supabaseApiKey: 'supabase_api_key',
    isDevelopment: false,
    isProduction: false,
    isTest: false,
    isStaging: true,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
    featureFlags: {
        enableAuth: true,
    },
};

// Test configuration
const testConfig: EnvironmentConfig = {
    appBaseUrl: 'http://localhost:5173',
    apiBaseUrl: 'http://localhost:8000/api',
    wsBaseUrl: 'ws://localhost:8000/ws',
    supabaseUrl: 'https://supabase-project.supabase.co',
    supabaseApiKey: 'supabase_api_key',
    isDevelopment: false,
    isProduction: false,
    isTest: true,
    isStaging: false,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 25,
    featureFlags: {
        enableAuth: true,
    },
};

export function getEnvironmentConfig(): EnvironmentConfig {
    if (import.meta.env.VITE_ENVIRONMENT === 'staging') {
        return stagingConfig;
    }
    if (import.meta.env.MODE === 'production') {
        return productionConfig;
    }
    if (import.meta.env.MODE === 'test') {
        return testConfig;
    }
    return developmentConfig;
}

export function getConfigWithOverrides(): EnvironmentConfig {
    const baseConfig = getEnvironmentConfig();

    return {
        ...baseConfig,
        appBaseUrl: getEnvVar('VITE_APP_BASE_URL', baseConfig.appBaseUrl),
        apiBaseUrl: getEnvVar('VITE_API_BASE_URL', baseConfig.apiBaseUrl),
        wsBaseUrl: getEnvVar('VITE_WS_BASE_URL', baseConfig.wsBaseUrl),
        supabaseUrl: getEnvVar('VITE_SUPABASE_URL', baseConfig.supabaseUrl),
        supabaseApiKey: getEnvVar('VITE_SUPABASE_API_KEY', baseConfig.supabaseApiKey),
    };
}
