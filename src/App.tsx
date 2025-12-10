import { useState, useEffect, useRef } from 'react';
import {
  Send,
  Bot,
  User,
  FileCode,
  BookOpen,
  Settings,
  ArrowLeft,
  Copy,
  Cpu,
  Download
} from 'lucide-react';

/**
 * AI Co-Author Canvas
 * A dual-pane collaborative workspace for writing code and stories with AI.
 */

// --- Types ---

interface ButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success';
  className?: string;
  disabled?: boolean;
  title?: string;
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
}

// --- Components ---

const Button = ({ children, onClick, variant = 'primary', className = '', disabled = false, title = '' }: ButtonProps) => {
  const baseStyle = "px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center gap-2";
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white disabled:bg-blue-800 disabled:opacity-50",
    secondary: "bg-gray-700 hover:bg-gray-600 text-gray-200",
    ghost: "hover:bg-gray-800 text-gray-400 hover:text-white",
    danger: "hover:bg-red-900/30 text-red-400 hover:text-red-300",
    success: "bg-green-600 hover:bg-green-700 text-white"
  };

  return (
    <button
      onClick={onClick}
      className={`${baseStyle} ${variants[variant]} ${className}`}
      disabled={disabled}
      title={title}
    >
      {children}
    </button>
  );
};

const Modal = ({ isOpen, onClose, title, children }: ModalProps) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-gray-800 border border-gray-700 rounded-xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
        <div className="flex justify-between items-center p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white">✕</button>
        </div>
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
};

// --- Main Application ---

export default function AIWriterCanvas() {
  // State
  const [content, setContent] = useState("// Start writing your code or chapter here...\n\nfunction helloWorld() {\n  console.log('Hello AI Canvas!');\n}");
  const [mode, setMode] = useState<'code' | 'story'>('code');
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'system', content: 'Welcome to your AI Canvas. I can help you write code or stories. Just ask!' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [apiProvider, setApiProvider] = useState<'openai' | 'gemini'>('openai');
  const [showSettings, setShowSettings] = useState(false);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load API Key from URL parameters or local storage on mount
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const urlKey = params.get('key');
    const urlProvider = params.get('provider');

    if (urlKey) {
      // Priority 1: URL Parameters
      setApiKey(urlKey);
      localStorage.setItem('ai_canvas_api_key', urlKey);

      if (urlProvider) {
        setApiProvider(urlProvider as 'openai' | 'gemini');
        localStorage.setItem('ai_canvas_provider', urlProvider);
      }
    } else {
      // Priority 2: Local Storage
      const storedKey = localStorage.getItem('ai_canvas_api_key');
      const storedProvider = localStorage.getItem('ai_canvas_provider');
      if (storedKey) setApiKey(storedKey);
      if (storedProvider) setApiProvider(storedProvider as 'openai' | 'gemini');
    }
  }, []);

  const saveSettings = (key: string, provider: 'openai' | 'gemini') => {
    setApiKey(key);
    setApiProvider(provider);
    localStorage.setItem('ai_canvas_api_key', key);
    localStorage.setItem('ai_canvas_provider', provider);
    setShowSettings(false);
  };

  // --- Actions ---

  const handleDownload = () => {
    const element = document.createElement("a");
    const file = new Blob([content], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = mode === 'code' ? "script.js" : "chapter.md";
    document.body.appendChild(element);
    element.click();
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const insertAtCursor = (textToInsert: string) => {
    const textarea = editorRef.current;
    if (!textarea) return;

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const previousContent = textarea.value;
    
    const newContent = 
      previousContent.substring(0, start) + 
      textToInsert + 
      previousContent.substring(end);
    
    setContent(newContent);
    
    // Restore focus and cursor position
    setTimeout(() => {
      textarea.focus();
      textarea.selectionStart = textarea.selectionEnd = start + textToInsert.length;
    }, 0);
  };

  // --- AI Logic ---

  const callAI = async (userMessage: string) => {
    setIsLoading(true);
    
    // Construct context
    const contextPrompt = `
      You are an expert AI collaborator.
      The user is currently working in "${mode === 'code' ? 'Code/Developer' : 'Story/Writer'}" mode.
      
      Here is the current content of their canvas:
      ---
      ${content.substring(0, 5000)} ${content.length > 5000 ? '...(truncated)' : ''}
      ---
      
      User Request: ${userMessage}
      
      Provide a helpful, concise response. If generating code or text updates, provide just the content so they can copy/paste easily.
    `;

    try {
      let aiResponseText = "";

      if (!apiKey) {
        // Mock Response for Demo
        await new Promise(resolve => setTimeout(resolve, 1000));
        aiResponseText = "I am currently in Demo Mode because no API Key is set.\n\nHere is a sample response based on your request:\n\nIf you were asking for code:\n```javascript\nconsole.log('This is a demo');\n```\n\nPlease configure your API Key in Settings to get real intelligence.";
      } else if (apiProvider === 'gemini') {
        // Google Gemini API
        const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contents: [{ parts: [{ text: contextPrompt }] }]
          })
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error.message);
        aiResponseText = data.candidates?.[0]?.content?.parts?.[0]?.text || "No response generated.";
      } else {
        // OpenAI API
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`
          },
          body: JSON.stringify({
            model: "gpt-4-turbo",
            messages: [
              { role: "system", content: "You are a helpful coding and writing assistant." },
              { role: "user", content: contextPrompt }
            ]
          })
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error.message);
        aiResponseText = data.choices?.[0]?.message?.content || "No response generated.";
      }

      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: aiResponseText }]);

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'assistant', content: `Error: ${errorMessage}. Please check your API Key.` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    callAI(input);
  };

  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100 font-sans overflow-hidden selection:bg-blue-500/30">
      
      {/* Header */}
      <header className="h-14 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-1.5 rounded-lg">
            <Cpu size={18} className="text-white" />
          </div>
          <h1 className="font-bold text-lg tracking-tight text-gray-100">AI Co-Author</h1>
          <div className="h-4 w-[1px] bg-gray-700 mx-2"></div>
          <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700/50">
            <button
              onClick={() => setMode('story')}
              className={`px-3 py-1 text-xs font-medium rounded-md flex items-center gap-2 transition-all ${
                mode === 'story' ? 'bg-blue-600 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <BookOpen size={14} /> Story
            </button>
            <button
              onClick={() => setMode('code')}
              className={`px-3 py-1 text-xs font-medium rounded-md flex items-center gap-2 transition-all ${
                mode === 'code' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <FileCode size={14} /> Dev
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
           <Button variant="ghost" onClick={handleDownload} title="Download File">
            <Download size={16} />
          </Button>
          <Button variant="ghost" onClick={() => setShowSettings(true)} title="Settings">
            <Settings size={16} />
          </Button>
        </div>
      </header>

      {/* Main Workspace */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Left Pane: Editor */}
        <div className="flex-1 flex flex-col min-w-0 relative group">
          <textarea
            ref={editorRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            spellCheck={false}
            className={`flex-1 w-full h-full resize-none bg-[#0d1117] text-gray-300 p-6 focus:outline-none focus:ring-0 leading-relaxed ${
              mode === 'code' 
                ? 'font-mono text-sm' 
                : 'font-serif text-lg max-w-3xl mx-auto'
            }`}
            placeholder={mode === 'code' ? "// Start coding..." : "Once upon a time..."}
          />
          <div className="absolute bottom-4 right-6 text-xs text-gray-500 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
            {content.length} characters
          </div>
        </div>

        {/* Resizer Border */}
        <div className="w-[1px] bg-gray-800 hover:bg-blue-500 transition-colors cursor-col-resize hidden md:block"></div>

        {/* Right Pane: AI Chat */}
        <div className="w-[400px] flex flex-col bg-gray-900 border-l border-gray-800 shadow-xl z-10 shrink-0">
          
          {/* Chat List */}
          <div className="flex-1 overflow-y-auto p-4 space-y-6">
            {messages.map((m) => (
              <div key={m.id} className={`flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300 ${m.role === 'user' ? 'items-end' : 'items-start'}`}>
                
                {/* Message Header */}
                <div className="flex items-center gap-2 mb-1 px-1">
                  {m.role === 'assistant' ? (
                    <>
                      <Bot size={12} className="text-blue-400" />
                      <span className="text-[10px] uppercase font-bold text-gray-500">AI Pilot</span>
                    </>
                  ) : (
                    <>
                      <span className="text-[10px] uppercase font-bold text-gray-500">You</span>
                      <User size={12} className="text-gray-400" />
                    </>
                  )}
                </div>

                {/* Message Bubble */}
                <div
                  className={`max-w-[90%] rounded-2xl px-4 py-3 text-sm whitespace-pre-wrap leading-6 shadow-sm ${
                    m.role === 'user' 
                      ? 'bg-blue-600 text-white rounded-tr-sm' 
                      : 'bg-gray-800 text-gray-200 border border-gray-700/50 rounded-tl-sm'
                  }`}
                >
                  {m.content}
                </div>

                {/* AI Actions */}
                {m.role === 'assistant' && (
                  <div className="flex items-center gap-2 mt-2 px-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button 
                      onClick={() => insertAtCursor(m.content)}
                      className="flex items-center gap-1.5 text-xs text-emerald-400 hover:text-emerald-300 bg-emerald-950/30 px-2 py-1 rounded transition-colors"
                      title="Insert at cursor position"
                    >
                      <ArrowLeft size={12} /> Insert
                    </button>
                    <button 
                      onClick={() => handleCopy(m.content)}
                      className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-800 transition-colors"
                    >
                      <Copy size={12} /> Copy
                    </button>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex items-start gap-3">
                 <div className="bg-gray-800 p-3 rounded-2xl rounded-tl-sm border border-gray-700/50">
                    <div className="flex gap-1.5">
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                      <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                    </div>
                 </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="p-4 bg-gray-900 border-t border-gray-800">
            <div className="relative">
              <form onSubmit={handleSendMessage}>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={mode === 'code' ? "Ask AI to generate a function..." : "Ask AI to write a paragraph..."}
                  className="w-full bg-gray-950 text-white placeholder-gray-500 border border-gray-700 rounded-xl pl-4 pr-12 py-3 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 transition-all"
                />
                <button
                  type="submit"
                  disabled={isLoading || !input.trim()}
                  className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                >
                  <Send size={16} />
                </button>
              </form>
              <div className="text-[10px] text-center text-gray-600 mt-2 flex justify-center items-center gap-1">
                 {apiKey ? <span className="text-emerald-500 flex items-center gap-1">● Online ({apiProvider})</span> : <span className="text-amber-500 flex items-center gap-1">● Demo Mode (Mock)</span>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      <Modal isOpen={showSettings} onClose={() => setShowSettings(false)} title="AI Settings">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">AI Provider</label>
            <div className="flex bg-gray-900 rounded-lg p-1 border border-gray-700">
              <button 
                onClick={() => setApiProvider('gemini')}
                className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${apiProvider === 'gemini' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'}`}
              >
                Google Gemini
              </button>
              <button 
                onClick={() => setApiProvider('openai')}
                className={`flex-1 py-1.5 text-sm rounded-md transition-colors ${apiProvider === 'openai' ? 'bg-green-600 text-white' : 'text-gray-400 hover:text-white'}`}
              >
                OpenAI
              </button>
            </div>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">API Key</label>
            <input 
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={`Enter your ${apiProvider === 'gemini' ? 'Gemini' : 'OpenAI'} API Key`}
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Your key is stored locally in your browser and never sent to our servers.
            </p>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowSettings(false)}>Cancel</Button>
            <Button variant="primary" onClick={() => saveSettings(apiKey, apiProvider)}>Save Configuration</Button>
          </div>
        </div>
      </Modal>

    </div>
  );
}