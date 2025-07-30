/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_ENVIRONMENT: string;
    readonly VITE_AUTH0_DOMAIN: string;
    readonly VITE_AUTH0_CLIENT_ID: string;
    readonly VITE_API_BASE_URL: string;
    readonly VITE_WS_BASE_URL: string;
    readonly VITE_SUPABASE_URL: string;
    readonly VITE_SUPABASE_API_KEY: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}
