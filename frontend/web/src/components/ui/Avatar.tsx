interface AvatarProps {
    name: string;
    size?: 'sm' | 'md' | 'lg';
    className?: string;
}

export function Avatar({ name, size = 'md', className = '' }: AvatarProps) {
    const getInitials = (name: string) => {
        return name
            .split(' ')
            .map(word => word[0])
            .join('')
            .toUpperCase()
            .slice(0, 2);
    };

    const sizeClasses = {
        sm: 'w-8 h-8 text-sm',
        md: 'w-10 h-10 text-base',
        lg: 'w-14 h-14 text-xl',
    };

    return (
        <div
            className={`bg-primary/10 border-primary/20 flex items-center justify-center rounded-full border ${sizeClasses[size]} ${className}`}
        >
            <span className="text-primary font-medium">{getInitials(name)}</span>
        </div>
    );
}
