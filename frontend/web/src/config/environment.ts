export interface EnvironmentConfig {
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
}

function getEnvVar(key: string, fallback: string): string {
    return import.meta.env[key] || fallback;
}

const developmentConfig: EnvironmentConfig = {
    apiBaseUrl: 'http://localhost:8000/api',
    wsBaseUrl: 'ws://localhost:8000/ws',
    isDevelopment: true,
    isProduction: false,
    isTest: false,
    isStaging: false,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
    featureFlags: {
        enableAuth: true,
    },
};

const productionConfig: EnvironmentConfig = {
    apiBaseUrl: 'https://brekkie-ai.fly.dev/api',
    wsBaseUrl: 'wss://brekkie-ai.fly.dev/ws',
    isDevelopment: false,
    isProduction: true,
    isTest: false,
    isStaging: false,
    enableDebugLogging: false,
    enableAnalytics: true,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
    featureFlags: {
        enableAuth: false,
    },
};

const stagingConfig: EnvironmentConfig = {
    apiBaseUrl: 'https://brekkie-ai-staging.fly.dev/api',
    wsBaseUrl: 'wss://brekkie-ai-staging.fly.dev/ws',
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
    apiBaseUrl: 'http://localhost:8000/api',
    wsBaseUrl: 'ws://localhost:8000/ws',
    isDevelopment: false,
    isProduction: false,
    isTest: true,
    isStaging: false,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
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
        apiBaseUrl: getEnvVar('VITE_API_BASE_URL', baseConfig.apiBaseUrl),
        wsBaseUrl: getEnvVar('VITE_WS_BASE_URL', baseConfig.wsBaseUrl),
        maxMessageCountAnonymous: parseInt(
            getEnvVar(
                'VITE_MAX_MESSAGE_COUNT_ANONYMOUS',
                baseConfig.maxMessageCountAnonymous.toString(),
            ),
        ),
        maxMessageCountAuthenticated: parseInt(
            getEnvVar(
                'VITE_MAX_MESSAGE_COUNT_AUTHENTICATED',
                baseConfig.maxMessageCountAuthenticated.toString(),
            ),
        ),
    };
}
