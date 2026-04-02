'use client';
import { useState } from 'react';
import { nlqApi, type NLQResponse } from '@/lib/api';
import { MagnifyingGlassIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';

interface Props {
  datasetId?: number;
}

interface Message {
  type: 'user' | 'assistant';
  text: string;
  result?: unknown;
}

export default function NLQInterface({ datasetId }: Props) {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);

  const sendQuery = async () => {
    if (!query.trim() || loading) return;
    const userMsg = query.trim();
    setQuery('');
    setMessages((prev) => [...prev, { type: 'user', text: userMsg }]);
    setLoading(true);
    try {
      const res = await nlqApi.query(userMsg, datasetId);
      setMessages((prev) => [
        ...prev,
        { type: 'assistant', text: res.data.explanation, result: res.data.result },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { type: 'assistant', text: 'Sorry, I could not process that query.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendQuery();
    }
  };

  return (
    <div className="card flex flex-col h-80">
      <div className="flex items-center gap-2 mb-4">
        <MagnifyingGlassIcon className="h-5 w-5 text-blue-500" />
        <h3 className="font-semibold text-slate-800">Natural Language Query</h3>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 mb-3">
        {messages.length === 0 && (
          <div className="text-slate-400 text-sm text-center py-4">
            Ask questions about your data in plain English.
            <br />
            <span className="text-xs">e.g. &quot;What is the average revenue?&quot; or &quot;How many rows?&quot;</span>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs px-3 py-2 rounded-2xl text-sm ${
                msg.type === 'user'
                  ? 'bg-blue-600 text-white rounded-br-sm'
                  : 'bg-slate-100 text-slate-800 rounded-bl-sm'
              }`}
            >
              <p>{msg.text}</p>
              {msg.result != null && (
                <pre className="mt-1 text-xs opacity-75 overflow-auto">
                  {JSON.stringify(msg.result, null, 2)}
                </pre>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 px-3 py-2 rounded-2xl rounded-bl-sm" role="status" aria-label="Loading response">
              <div className="flex gap-1" aria-hidden="true">
                {[0, 1, 2].map((i) => (
                  <div key={i} className="h-2 w-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.1}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-2">
        <input
          type="text"
          className="flex-1 border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Ask a question about your data..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKey}
        />
        <button
          onClick={sendQuery}
          disabled={!query.trim() || loading}
          className="btn-primary px-3 disabled:opacity-50"
        >
          <PaperAirplaneIcon className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
