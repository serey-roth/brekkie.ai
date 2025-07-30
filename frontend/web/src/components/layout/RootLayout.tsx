import { Outlet } from 'react-router-dom';

export function RootLayout() {
    return (
        <div className="bg-background px-safe pb-safe min-h-screen">
            <Outlet />
        </div>
    );
}
