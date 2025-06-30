import React from 'react';
import ReactDOM from 'react-dom/client';
import { AppProvider } from '@/components/providers/AppProvider';
import { AuthProvider } from '@/components/providers/AuthProvider';
import { ChatProvider } from '@/components/providers/ChatProvider';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <AppProvider>
            <AuthProvider>
                <ChatProvider>
                    <App />
                </ChatProvider>
            </AuthProvider>
        </AppProvider>
    </React.StrictMode>
);
