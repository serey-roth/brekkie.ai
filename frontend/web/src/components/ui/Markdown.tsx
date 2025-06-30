import ReactMarkdown from 'react-markdown';
import remarkBreaks from 'remark-breaks';

export function Markdown({ children }: { children: string }) {
    return (
        <ReactMarkdown
            remarkPlugins={[remarkBreaks]}
            components={{
                p: ({ children }) => <p className="py-1">{children}</p>,
                h1: ({ children }) => <h1 className="mb-4 text-2xl font-bold">{children}</h1>,
                h2: ({ children }) => <h2 className="mb-3 text-xl font-bold">{children}</h2>,
                h3: ({ children }) => <h3 className="mb-2 text-lg font-bold">{children}</h3>,
                ul: ({ children }) => <ul className="mb-4 list-disc space-y-1 pl-6">{children}</ul>,
                ol: ({ children }) => (
                    <ol className="mb-4 list-decimal space-y-1 pl-6">{children}</ol>
                ),
                li: ({ children }) => <li className="mb-1">{children}</li>,
                a: ({ children, href }) => (
                    <a
                        href={href}
                        className="text-primary hover:text-primary/80 underline transition-colors"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        {children}
                    </a>
                ),
            }}
        >
            {children}
        </ReactMarkdown>
    );
}
