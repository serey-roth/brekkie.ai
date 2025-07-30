import { Routes, Route } from 'react-router-dom';
import { AuthCallback } from './components/auth/AuthCallback';
import { AuthForm } from './components/auth/AuthForm';
import { AuthGuard } from './components/auth/AuthGuard';
import { MainView } from './components/layout/MainView';
import { RootLayout } from './components/layout/RootLayout';
import { ChatProvider } from './components/providers/ChatProvider';

export default function App() {
    return (
        <Routes>
            <Route path="/auth" element={<AuthForm />} />
            <Route path="/auth/callback" element={<AuthCallback />} />
            <Route
                path="/"
                element={
                    <AuthGuard>
                        <ChatProvider>
                            <RootLayout />
                        </ChatProvider>
                    </AuthGuard>
                }
            >
                <Route index element={<MainView />} />
            </Route>
        </Routes>
    );
}
