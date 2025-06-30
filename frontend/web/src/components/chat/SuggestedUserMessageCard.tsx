type SuggestedUserMessageCardProps = {
    message: string;
    onClick: () => void;
    disabled: boolean;
};
export function SuggestedUserMessageCard({
    message,
    onClick,
    disabled,
}: SuggestedUserMessageCardProps) {
    return (
        <button
            className={`border-border text-contrast hover:bg-secondary-light focus:ring-primary/30 py-2.5 px-4 w-full rounded-xl border bg-white text-left text-sm sm:text-base sm:min-h-12 font-medium shadow-sm transition hover:shadow-md focus:ring-2 focus:outline-none active:scale-95 ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={onClick}
            disabled={disabled}
        >
            {message}
        </button>
    );
}
