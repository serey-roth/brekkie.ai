import { Outlet } from 'react-router-dom';
import { useAppState } from '@/context/app-context';
import { Sidebar } from './Sidebar';

export function RootLayout() {
    const { isSidebarOpen, selectedRecipeId } = useAppState();
    return (
        <div className="bg-background px-safe pb-safe min-h-screen">
            <Sidebar />
            <div
                className={`bg-background grid min-h-screen overflow-hidden transition-all duration-300 ${
                    selectedRecipeId ? 'lg:grid-cols-2' : 'lg:grid-cols-1'
                } ${isSidebarOpen ? 'md:ml-16 lg:ml-[20rem]' : 'md:ml-16'}`}
            >
                <Outlet />
            </div>
        </div>
    );
}
