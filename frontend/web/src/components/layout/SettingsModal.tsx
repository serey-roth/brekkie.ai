import { User, CreditCard, LogOut, Mail } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Modal } from '@/components/ui/Modal';
import { useUserAccessManager } from '@/context/app-context';
import { useSupabaseAuth } from '@/hooks/use-supabase-auth';
import type { UserMetadata } from '@/supabase-client';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    user: UserMetadata | null;
}

type TabType = 'profile' | 'account';

export function SettingsModal({ isOpen, onClose, user }: SettingsModalProps) {
    const [activeTab, setActiveTab] = useState<TabType>('profile');
    const { logout } = useSupabaseAuth();
    const navigate = useNavigate();
    const userAccessManager = useUserAccessManager();

    const tabs = [
        {
            id: 'profile' as TabType,
            label: 'Profile',
            icon: <User size={16} />,
        },
        {
            id: 'account' as TabType,
            label: 'Account',
            icon: <CreditCard size={16} />,
        },
    ];

    const handleSignOut = async () => {
        try {
            await logout();
            await userAccessManager.revokeAccess();
            onClose();
            navigate('/');
        } catch (error) {
            console.error('Logout failed:', error);
        }
    };

    return (
        <Modal
            isOpen={isOpen}
            onClose={onClose}
            title="Settings"
            size="lg"
            className="bg-background-light border-border rounded-lg border"
        >
            <div className="flex h-[500px]">
                {/* Sidebar */}
                <div className="border-accent w-64 border-r pr-6">
                    <nav className="space-y-1">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors duration-150 ${
                                    activeTab === tab.id
                                        ? 'bg-primary/20 text-primary border-primary/40 border'
                                        : 'text-contrast hover:bg-primary/10 hover:text-primary'
                                }`}
                            >
                                <span className="text-contrast-subtle">{tab.icon}</span>
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </nav>
                </div>

                {/* Content */}
                <div className="flex-1 pl-6">
                    {activeTab === 'profile' && (
                        <div className="space-y-6">
                            <div>
                                <div className="space-y-4">
                                    <div>
                                        <label className="text-contrast mb-2 block text-sm font-medium">
                                            Name
                                        </label>
                                        <input
                                            type="text"
                                            value={user?.name || ''}
                                            readOnly
                                            className="bg-background border-border text-contrast w-full rounded-lg border px-3 py-2 focus:ring-0 focus:outline-none"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-contrast mb-2 block text-sm font-medium">
                                            Email
                                        </label>
                                        <input
                                            type="email"
                                            value={user?.email || ''}
                                            readOnly
                                            className="bg-background border-border text-contrast w-full rounded-lg border px-3 py-2 focus:ring-0 focus:outline-none"
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {activeTab === 'account' && (
                        <div className="space-y-6">
                            <div>
                                <h3 className="text-contrast mb-4 text-base">Account</h3>
                                <div className="flex items-center gap-2">
                                    <p className="text-contrast-subtle flex-1 text-sm">
                                        Sign out of this device.
                                    </p>
                                    <button
                                        onClick={handleSignOut}
                                        className="flex items-center gap-2 rounded-lg px-3 py-2 text-left text-red-500 transition-colors duration-150 hover:bg-red-500/10 hover:text-red-600"
                                    >
                                        <LogOut size={16} />
                                        <span>Sign Out</span>
                                    </button>
                                </div>
                                <div className="mt-2 flex items-center gap-2">
                                    <p className="text-contrast-subtle flex-1 text-sm">
                                        Need help?
                                    </p>
                                    <a
                                        href="mailto:serey.brekkie@gmail.com"
                                        className="text-primary hover:bg-primary/10 hover:text-primary flex items-center gap-2 rounded-lg px-3 py-2 text-left transition-colors duration-150"
                                    >
                                        <Mail size={16} />
                                        <span>Contact Support</span>
                                    </a>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </Modal>
    );
}
