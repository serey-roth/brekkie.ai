export interface EnvironmentConfig {
    apiBaseUrl: string;
    wsBaseUrl: string;
    isDevelopment: boolean;
    isProduction: boolean;
    isTest: boolean;
    version?: string;
    enableDebugLogging?: boolean;
    enableAnalytics?: boolean;
    maxMessageCountAnonymous: number;
    maxMessageCountAuthenticated: number;
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
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
};

const productionConfig: EnvironmentConfig = {
    apiBaseUrl: 'https://api.foodagent.com/api',
    wsBaseUrl: 'wss://api.foodagent.com/ws',
    isDevelopment: false,
    isProduction: true,
    isTest: false,
    enableDebugLogging: false,
    enableAnalytics: true,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
};

// Test configuration
const testConfig: EnvironmentConfig = {
    apiBaseUrl: 'http://localhost:8000/api',
    wsBaseUrl: 'ws://localhost:8000/ws',
    isDevelopment: false,
    isProduction: false,
    isTest: true,
    enableDebugLogging: true,
    enableAnalytics: false,
    maxMessageCountAnonymous: 10,
    maxMessageCountAuthenticated: 50,
};

export function getEnvironmentConfig(): EnvironmentConfig {
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
        wsBaseUrl: getEnvVar('VITE_WEBSOCKET_URL', baseConfig.wsBaseUrl),
        maxMessageCountAnonymous: parseInt(getEnvVar('VITE_MAX_MESSAGE_COUNT_ANONYMOUS', baseConfig.maxMessageCountAnonymous.toString())),
        maxMessageCountAuthenticated: parseInt(getEnvVar('VITE_MAX_MESSAGE_COUNT_AUTHENTICATED', baseConfig.maxMessageCountAuthenticated.toString())),
    };
} 