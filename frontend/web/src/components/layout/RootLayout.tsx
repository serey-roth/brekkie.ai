import { Outlet } from 'react-router-dom';

export function RootLayout() {
    return (
        <div className="bg-background min-h-screen">
            <main>
                <Outlet />
            </main>
        </div>
    );
}
