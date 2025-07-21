import { Auth0Provider } from '@auth0/auth0-react';
import { Routes, Route } from 'react-router-dom';
import { AuthCallback } from './components/auth/AuthCallback';
import { Main } from './components/layout/Main';
import { RootLayout } from './components/layout/RootLayout';
import { ChatProvider } from './components/providers/ChatProvider';
import { useAppConfig } from './context/app-context';

export default function App() {
    const { appBaseUrl, auth0Domain, auth0ClientId, auth0Audience } = useAppConfig();

    return (
        <Auth0Provider
            domain={auth0Domain}
            clientId={auth0ClientId}
            authorizationParams={{
                audience: auth0Audience,
                redirect_uri: `${appBaseUrl}/auth/callback?from=auth0`,
            }}
        >
            <ChatProvider>
                <Routes>
                    <Route path="/" element={<RootLayout />}>
                        <Route index element={<Main />} />
                        <Route path="auth/callback" element={<AuthCallback />} />
                    </Route>
                </Routes>
            </ChatProvider>
        </Auth0Provider>
    );
}
