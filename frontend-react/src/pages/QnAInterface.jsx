import { useState, useRef, useEffect } from 'react';
import api from '../lib/api';
import { Send, Bot, User, Sparkles } from 'lucide-react';

const WELCOME =
  "Hi — I'm BookInsight. Ask about any book, author, or reading mood. I blend your project's library with Google Books + Open Library and remember our chat in this session so we can go deeper together.";

const QUICK_PROMPTS = [
  'Epic myths like the Ramayana — what should I read next?',
  'Best recent literary fiction in translation',
  'Short audiobooks under 6 hours',
];

export default function QnAInterface() {
  const [messages, setMessages] = useState([{ role: 'assistant', content: WELCOME }]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [history, setHistory] = useState([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    const loadHistory = async () => {
      try {
        const res = await api.get('/chat-history/');
        setHistory(res.data.data || []);
      } catch (err) {
        console.error(err);
      }
    };
    loadHistory();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    let priorConversation = messages
      .filter((m) => m.role === 'user' || m.role === 'assistant')
      .slice(-10)
      .map(({ role, content }) => ({ role, content: String(content).slice(0, 6000) }));
    if (
      priorConversation.length &&
      priorConversation[0].role === 'assistant' &&
      priorConversation[0].content === WELCOME
    ) {
      priorConversation = priorConversation.slice(1);
    }

    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setLoading(true);

    try {
      setError('');
      // 1. Q&A: multi-turn + RAG + web catalogs (backend)
      const qaRes = await api.post('/ask/', {
        question: userMessage,
        conversation: priorConversation,
      });
      let answerText = qaRes.data.answer;

      if (qaRes.data.citations && qaRes.data.citations.length > 0) {
        answerText += `\n\n**Sources:**`;
        qaRes.data.citations.forEach((source, i) => {
          answerText += `\n${i + 1}. ${source}`;
        });
      }
      if (qaRes.data.cached) {
        answerText += `\n\n(Served from cache for faster response)`;
      }

      setMessages(prev => [...prev, { role: 'assistant', content: answerText }]);
      setHistory((prev) => [
        {
          id: Date.now(),
          question: userMessage,
          answer: answerText,
        },
        ...prev,
      ].slice(0, 20));

    } catch (err) {
      console.error(err);
      const isTimeout = err.code === 'ECONNABORTED' || err.message?.includes('timeout');
      const backendDown = !err.response && err.request;
      const detail =
        err.response?.data?.message ||
        err.response?.data?.error ||
        (isTimeout ? 'Request timed out.' : err.message) ||
        '';
      setError(
        backendDown
          ? 'Cannot reach the API at http://127.0.0.1:8000 — is the Django server running?'
          : isTimeout
            ? 'The answer took too long. Ensure LM Studio is running (port 1234) or try again.'
            : `Unable to complete the request. ${detail}`.trim()
      );
      setMessages(prev => [...prev, { role: 'assistant', content: '❌ System Error: Unable to reach the backend AI engine.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid xl:grid-cols-[2fr,1fr] gap-6 max-w-7xl mx-auto">
    <div className="h-[calc(100vh-120px)] sm:h-[80vh] flex flex-col bg-white rounded-3xl border border-slate-200 shadow-sm animate-in fade-in slide-in-from-bottom-4 duration-700 overflow-hidden">
      
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-green-100 border border-green-200 flex items-center justify-center">
            <Bot className="w-5 h-5 text-green-600" />
          </div>
          <div>
            <h2 className="text-slate-900 font-bold text-lg">BookInsight · RAG + web</h2>
            <p className="text-xs text-slate-500 flex items-center gap-1 font-medium">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
              Multi-turn chat · Local DB + catalogs
            </p>
          </div>
        </div>
        <Sparkles className="w-5 h-5 text-green-400" />
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar bg-white">
        {error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`flex gap-4 max-w-[85%] ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              
              {/* Avatar */}
              <div className="flex-shrink-0 mt-1">
                {msg.role === 'user' ? (
                   <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center shadow-sm">
                     <User className="w-4 h-4 text-white" />
                   </div>
                ) : (
                  <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center shadow-sm">
                     <Bot className="w-4 h-4 text-white" />
                   </div>
                )}
              </div>

              {/* Bubble */}
              <div className={`p-4 rounded-2xl text-sm sm:text-base leading-relaxed whitespace-pre-wrap shadow-sm ${
                msg.role === 'user' 
                  ? 'bg-green-600 text-white rounded-tr-sm' 
                  : 'bg-slate-50 text-slate-800 rounded-tl-sm border border-slate-200'
              }`}>
                {msg.content}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-2xl rounded-tl-sm p-4 text-slate-600 shadow-sm">
              <span className="flex gap-1">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></span>
              </span>
              Thinking with your library and the web…
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-white border-t border-slate-200 space-y-2">
        <div className="flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              type="button"
              disabled={loading}
              onClick={() => setInput(p)}
              className="text-xs font-medium rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-slate-700 hover:border-green-300 hover:bg-green-50/80 transition-colors disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            placeholder="Ask anything about books — worldwide titles, themes, or what to read next…"
            className="w-full bg-white border border-slate-300 text-slate-900 rounded-xl pl-5 pr-14 py-4 focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500 transition-all disabled:opacity-50 placeholder:text-slate-400 shadow-sm"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2 bg-green-600 hover:bg-green-700 text-white rounded-lg disabled:opacity-50 transition-colors shadow-sm"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>

    </div>
    <aside className="rounded-3xl border border-slate-200 bg-white p-4 sm:p-6 h-fit max-h-[80vh] overflow-auto shadow-sm">
      <h3 className="text-sm uppercase tracking-[0.2em] text-slate-500 mb-4 font-bold">Recent Chat History</h3>
      {history.length === 0 ? (
        <p className="text-sm text-slate-500 font-medium">No chats yet. Ask a question to save history.</p>
      ) : (
        <div className="space-y-3">
          {history.map((item, index) => (
            <div key={item.id || index} className="rounded-xl border border-slate-200 bg-slate-50 p-3 shadow-sm">
              <p className="text-xs text-green-700 font-semibold mb-1 line-clamp-2">{item.question}</p>
              <p className="text-xs text-slate-600 line-clamp-3">{item.answer}</p>
            </div>
          ))}
        </div>
      )}
    </aside>
    </div>
  );
}
