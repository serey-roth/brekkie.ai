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
            className={`border-border text-contrast hover:bg-secondary-light focus:ring-primary/30 w-full rounded-xl border bg-white px-4 py-2.5 text-left text-sm font-medium shadow-sm transition hover:shadow-md focus:ring-2 focus:outline-none active:scale-95 sm:min-h-12 sm:text-base ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
            onClick={onClick}
            disabled={disabled}
        >
            {message}
        </button>
    );
}
