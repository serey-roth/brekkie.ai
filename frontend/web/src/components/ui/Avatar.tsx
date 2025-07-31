import { User } from 'lucide-react';

interface AvatarProps {
    name?: string | null;
    avatarUrl?: string | null;
    size?: 'xs' | 'sm' | 'md' | 'lg';
    className?: string;
}

export function Avatar({ name, avatarUrl, size = 'md', className = '' }: AvatarProps) {
    const getInitials = (name: string) => {
        return name
            .split(' ')
            .map((word) => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    const getIconSize = (size: string) => {
        switch (size) {
            case 'xs': return 14;
            case 'sm': return 18;
            case 'md': return 20;
            case 'lg': return 24;
            default: return 20;
        }
    };

    const sizeClasses = {
        xs: 'w-6 h-6 text-xs',
        sm: 'w-8 h-8 text-sm',
        md: 'w-10 h-10 text-base',
        lg: 'w-14 h-14 text-xl',
    };

    if (avatarUrl) {
        return (
            <div className={`${sizeClasses[size]} ${className}`}>
                <img
                    src={avatarUrl}
                    alt={`${name}'s avatar`}
                    className="h-full w-full rounded-full object-cover"
                    onError={(e) => {
                        // Fallback to initials or user icon if image fails to load
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const parent = target.parentElement;
                        if (parent) {
                            if (name) {
                                parent.innerHTML = `<span class="text-primary font-medium">${getInitials(name)}</span>`;
                            } else {
                                parent.innerHTML = `<svg class="text-primary" width="${getIconSize(size)}" height="${getIconSize(size)}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
                            }
                        }
                    }}
                />
            </div>
        );
    }

    return (
        <div
            className={`bg-primary/10 border-primary/20 flex items-center justify-center rounded-full border ${sizeClasses[size]} ${className}`}
        >
            {name ? (
                <span className="text-primary font-medium">{getInitials(name)}</span>
            ) : (
                <User size={getIconSize(size)} className="text-primary" />
            )}
        </div>
    );
}
