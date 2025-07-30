interface AvatarProps {
    name: string;
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
                        // Fallback to initials if image fails to load
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                        const parent = target.parentElement;
                        if (parent) {
                            parent.innerHTML = `<span class="text-primary font-medium">${getInitials(name)}</span>`;
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
            <span className="text-primary font-medium">{getInitials(name)}</span>
        </div>
    );
}
