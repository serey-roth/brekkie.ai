export const TypingIndicator = () => (
    <div className="flex items-start gap-3">
        <div className="bg-primary/10 border-primary/20 flex h-8 w-8 items-center justify-center rounded-full border">
            🌿
        </div>
        <div className="border-border max-w-[200px] rounded-2xl rounded-tl-md border bg-white px-4 py-3 shadow-sm">
            <div className="flex h-4 items-center gap-1">
                {[0, 150, 300].map((delay, i) => (
                    <div
                        key={i}
                        className="bg-primary/40 h-2 w-2 animate-bounce rounded-full"
                        style={{ animationDelay: `${delay}ms` }}
                    />
                ))}
            </div>
        </div>
    </div>
);
