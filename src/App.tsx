import React, { useState, useEffect, useRef } from 'react';
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

interface BackendMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  create_time?: string;
  metadata?: unknown;
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
  const [mode, setMode] = useState<'code' | 'story'>('code'); // 'code' | 'story'
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'system', content: 'Welcome to your AI Canvas. I can help you write code or stories. Please configure your Backend URL in Settings.' }
  ]);
  const [input, setInput] = useState('');
  const [baseURL, setBaseURL] = useState(''); // Custom backend URL for user_message and heartbeat
  const [sessionId, setSessionId] = useState<string | null>(null); // Session ID for the polling session
  const [sessionStatus, setSessionStatus] = useState<string | null>(null); // Current session status from heartbeat
  const [showSettings, setShowSettings] = useState(false);

  const editorRef = useRef<HTMLTextAreaElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load Base URL from local storage on mount
  useEffect(() => {
    const storedBaseURL = localStorage.getItem('ai_canvas_base_url');
    if (storedBaseURL) setBaseURL(storedBaseURL);
  }, []);

  const saveSettings = (base: string) => {
    setBaseURL(base);
    localStorage.setItem('ai_canvas_base_url', base);
    setShowSettings(false);
  };

  // --- Heartbeat (Polling) Logic ---
  useEffect(() => {
    if (!sessionId || !baseURL) return;

    const poll = async () => {
      try {
        const url = `${baseURL}/heartbeat`;
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId })
        });

        if (!response.ok) {
          throw new Error(`Heartbeat failed with status: ${response.status}`);
        }
        
        // Backend response structure expectation: 
        // { 
        //   status: "processing" | "completed", 
        //   session_id: "...", 
        //   messages: [{id, role, content, create_time, metadata}, ...] 
        // }
        const data = await response.json();
        
        // 1. Process Messages
        if (data.messages && Array.isArray(data.messages)) {
          setMessages(prev => {
            // Create a Set of existing IDs to prevent duplicates
            const existingIds = new Set(prev.map(m => m.id));
            
            // Filter incoming messages that we don't already have
            const newMessages = data.messages
              .filter((m: BackendMessage) => !existingIds.has(m.id))
              .map((m: BackendMessage): Message => ({
                  id: m.id || Date.now().toString(), // Use backend UUID
                  role: m.role,
                  content: m.content
                  // Note: create_time and metadata are available here if needed in the future
              }));

            if (newMessages.length > 0) {
              return [...prev, ...newMessages];
            }
            return prev;
          });
        }
        
        // 2. Check Status
        // Update session status for UI display
        if (data.status) {
          setSessionStatus(data.status);
        }

        // If status is ANYTHING other than 'processing', we assume the job is done/stopped.
        if (data.status && data.status !== 'processing') {
          setSessionId(null);
          setSessionStatus(null);

          if (data.status === 'failed' || data.status === 'error') {
             setMessages(prev => [...prev, {
              id: Date.now().toString(),
              role: 'system',
              content: "Backend reported job failure."
            }]);
          }
        }

      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown polling error';
        console.error("Polling error:", errorMessage);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'system',
          content: `Connection Error: ${errorMessage}. Stopping poll.`
        }]);
        setSessionId(null);
        setSessionStatus(null);
      }
    };

    // Set up polling interval (e.g., every 2 seconds)
    const intervalId = setInterval(poll, 2000);

    // Clean up interval on unmount or when sessionId changes to null
    return () => clearInterval(intervalId);
  }, [sessionId, baseURL, messages]);

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
    // Fallback for secure contexts where navigator.clipboard.writeText might not work in an iframe
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text);
    } else {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
        } catch (err) {
            console.error('Fallback copy failed', err);
        }
        document.body.removeChild(textarea);
    }
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

  // --- Send Message to Backend ---

  const sendUserMessage = async (userMessage: string) => {
    if (!baseURL) {
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'system', content: 'Error: Backend URL is not configured. Please check Settings.' }]);
      return;
    }

    const payload = {
      user_message: userMessage,
      canvas_content: content,
      mode: mode,
      // Pass the current messages history for context
      chat_history: messages.map(m => ({ role: m.role, content: m.content })),
    };

    try {
      const url = `${baseURL}/user_message`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Backend request failed with status: ${response.status}`);
      }

      // Backend should return a session_id
      const data = await response.json();
      const newSessionId = data.session_id;

      if (newSessionId) {
        setSessionId(newSessionId);
        setSessionStatus('processing'); // Set initial status
      } else {
        throw new Error("Backend did not return a session identifier.");
      }

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown network error occurred';
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'system', content: `Failed to initiate AI job: ${errorMessage}.` }]);
    }
  };

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Optimistically add user message
    // Note: If the backend returns this same message with a different ID (UUID vs timestamp),
    // it might appear twice. To fix this, backends often return the full chat history,
    // or we can deduplicate by content. For now, we use simple ID checking.
    // TODO: add temp visualization before return from the heartbeat
    // const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    // setMessages(prev => [...prev, userMsg]);
    
    const messageToProcess = input;
    setInput('');
    
    // Start the process: send message to backend
    sendUserMessage(messageToProcess);
  };
  
  const statusDisplay = baseURL 
    ? (sessionId ? <span className="text-blue-500 flex items-center gap-1">● Running (Session: {sessionId.substring(0, 4)}...)</span> : <span className="text-emerald-500 flex items-center gap-1">● Idle (Ready)</span>)
    : <span className="text-amber-500 flex items-center gap-1">● Config Needed</span>;


  return (
    <div className="flex flex-col h-screen bg-gray-950 text-gray-100 font-sans overflow-hidden selection:bg-blue-500/30">
      
      {/* Header */}
      <header className="h-14 border-b border-gray-800 bg-gray-900/50 flex items-center justify-between px-4 shrink-0">
        <div className="flex items-center gap-3">
          <div className="bg-blue-600 p-1.5 rounded-lg">
            <Cpu size={18} className="text-white" />
          </div>
          <h1 className="font-bold text-lg tracking-tight text-gray-100">AI Co-Author (Backend)</h1>
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
                  {m.role === 'assistant' || m.role === 'system' ? (
                    <>
                      <Bot size={12} className="text-blue-400" />
                      <span className="text-[10px] uppercase font-bold text-gray-500">{m.role === 'system' ? 'System' : 'AI Pilot'}</span>
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
                      : m.role === 'system'
                        ? 'bg-gray-700/50 text-gray-400 border border-gray-700/50 rounded-tl-sm'
                        : 'bg-gray-800 text-gray-200 border border-gray-700/50 rounded-tl-sm'
                  }`}
                >
                  {m.content}
                </div>

                {/* AI Actions */}
                {m.role === 'assistant' && (
                  <div className="flex items-center gap-2 mt-2 px-1 opacity-100 transition-opacity">
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
            
            {/* Processing Indicator */}
            {sessionStatus === 'processing' && (
              <div className="flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300 items-start">
                <div className="flex items-center gap-2 mb-1 px-1">
                  <Bot size={12} className="text-blue-400" />
                  <span className="text-[10px] uppercase font-bold text-gray-500">AI Pilot</span>
                </div>
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
                  disabled={!input.trim() || !baseURL}
                  className="absolute right-2 top-2 p-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-500 disabled:opacity-50 disabled:hover:bg-blue-600 transition-colors"
                >
                  <Send size={16} />
                </button>
              </form>
              <div className="text-[10px] text-center text-gray-600 mt-2 flex justify-center items-center gap-1">
                 {statusDisplay}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Settings Modal */}
      <Modal isOpen={showSettings} onClose={() => setShowSettings(false)} title="Backend Settings">
        <div className="space-y-4">
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Backend URL</label>
            <input 
              type="text"
              value={baseURL}
              onChange={(e) => setBaseURL(e.target.value)}
              placeholder="e.g., https://your-backend.com/api"
              className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              This URL is used to initiate new jobs (`/user_message`) and poll for updates (`/heartbeat`).
            </p>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setShowSettings(false)}>Cancel</Button>
            <Button variant="primary" onClick={() => saveSettings(baseURL)}>Save Configuration</Button>
          </div>
        </div>
      </Modal>

    </div>
  );
}