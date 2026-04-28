import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Components } from 'react-markdown';

// Override the background so code blocks match the dark canvas theme
const syntaxStyle = {
  ...vscDarkPlus,
  'pre[class*="language-"]': {
    ...vscDarkPlus['pre[class*="language-"]'],
    background: '#0b0b18',
    margin: 0,
  },
  'code[class*="language-"]': {
    ...vscDarkPlus['code[class*="language-"]'],
    background: 'transparent',
  },
};

const components: Components = {
  code({ className, children, ...props }) {
    const codeString = String(children);
    const match = /language-(\w+)/.exec(className || '');
    // Block code: has a language fence OR multi-line content
    const isBlock = Boolean(match) || codeString.includes('\n');

    if (!isBlock) {
      return (
        <code
          className="bg-canvas-overlay border border-canvas-border rounded px-1.5 py-0.5 text-violet-300 font-mono text-[0.8em]"
          {...props}
        >
          {children}
        </code>
      );
    }

    return (
      <SyntaxHighlighter
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        style={syntaxStyle as any}
        language={match?.[1] ?? 'text'}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: '0.5rem',
          border: '1px solid #1e1e3a',
          fontSize: '0.8125rem',
          lineHeight: '1.6',
        }}
      >
        {codeString.replace(/\n$/, '')}
      </SyntaxHighlighter>
    );
  },
};

export default function MarkdownContent({ content }: { content: string }) {
  return (
    <div className="markdown-body">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {content}
      </ReactMarkdown>
    </div>
  );
}
