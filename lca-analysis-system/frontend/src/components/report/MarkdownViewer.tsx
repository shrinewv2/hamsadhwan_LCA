import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownViewerProps {
  content: string
}

export default function MarkdownViewer({ content }: MarkdownViewerProps) {
  return (
    <div className="prose prose-invert max-w-none font-body text-text-secondary leading-relaxed">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className="font-heading text-2xl font-semibold text-text-primary mt-8 mb-4 border-b border-white/10 pb-2">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="font-heading text-xl font-semibold text-text-primary mt-6 mb-3">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="font-heading text-lg font-medium text-text-primary mt-4 mb-2">
              {children}
            </h3>
          ),
          p: ({ children }) => <p className="mb-3 text-text-secondary">{children}</p>,
          ul: ({ children }) => <ul className="list-disc list-inside mb-3 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal list-inside mb-3 space-y-1">{children}</ol>,
          li: ({ children }) => <li className="text-text-secondary">{children}</li>,
          strong: ({ children }) => <strong className="text-text-primary font-semibold">{children}</strong>,
          em: ({ children }) => <em className="text-accent-green italic">{children}</em>,
          code: ({ className, children }) => {
            const isInline = !className
            if (isInline) {
              return (
                <code className="px-1.5 py-0.5 bg-white/5 rounded text-xs font-mono text-accent-green">
                  {children}
                </code>
              )
            }
            return (
              <code className={`${className} font-mono text-xs`}>{children}</code>
            )
          },
          pre: ({ children }) => (
            <pre className="bg-bg-primary rounded-lg p-4 overflow-x-auto border border-white/5 mb-4">
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto mb-4">
              <table className="md-table w-full">{children}</table>
            </div>
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-2 border-accent-green/50 pl-4 my-4 text-text-muted italic">
              {children}
            </blockquote>
          ),
          hr: () => <hr className="border-white/10 my-6" />,
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent-green hover:underline"
            >
              {children}
            </a>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
