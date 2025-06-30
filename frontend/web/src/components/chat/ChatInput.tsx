import { useState, useRef, useEffect } from 'react';
import { FiArrowUp } from 'react-icons/fi';

type ChatInputProps = {
    onSend: (message: string) => void;
    disabled?: boolean;
    inputContainerRef?: React.RefObject<HTMLDivElement | null>;
};

export default function ChatInput({ onSend, disabled, inputContainerRef }: ChatInputProps) {
    const [input, setInput] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    const adjustHeight = () => {
        const textarea = textareaRef.current;
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
        }
    };

    useEffect(() => {
        adjustHeight();
        // Scroll to bottom if textarea is overflowing
        const textarea = textareaRef.current;
        if (textarea && textarea.scrollHeight > textarea.clientHeight) {
            textarea.scrollTop = textarea.scrollHeight;
        }
    }, [input]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim()) {
            onSend(input.trim());
            setInput('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit(e);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="pointer-events-none flex justify-center">
            <div className="pointer-events-auto w-full" ref={inputContainerRef}>
                <div
                    className="bg-background-light border-border flex flex-col rounded-t-3xl rounded-b-none border transition-shadow duration-200"
                    style={{ boxShadow: '0 2px 8px 0 rgba(0, 0, 0, 0.08)' }}
                >
                    <div className="chat-input-container px-4 pt-6 pb-2 sm:px-6">
                        <textarea
                            ref={textareaRef}
                            autoFocus={true}
                            value={input}
                            onChange={e => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            className="text-contrast placeholder-contrast-subtle max-h-[200px] min-h-[36px] w-full resize-none border-none bg-transparent p-0 text-left text-base leading-relaxed outline-none sm:text-[18px]"
                            placeholder="What's on your mind?"
                            rows={1}
                        />
                    </div>
                    <div className="flex items-end justify-end px-4 pb-5 sm:px-6">
                        <button
                            type="submit"
                            disabled={!input.trim() || disabled}
                            className={`flex h-10 min-h-[44px] w-10 min-w-[44px] items-center justify-center rounded-full text-lg shadow-md transition-all duration-200 ${
                                input.trim() && !disabled
                                    ? 'bg-primary hover:bg-primary-dark text-white'
                                    : 'bg-background-light/50 text-contrast-subtle/50 opacity-80 cursor-not-allowed'
                            }`}
                        >
                            <FiArrowUp
                                size={20}
                                className={input.trim() && !disabled ? 'text-white' : 'text-inherit'}
                            />
                        </button>
                    </div>
                </div>
            </div>
        </form>
    );
}
