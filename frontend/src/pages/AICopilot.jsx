import { useContext, useState, useEffect, useRef } from "react";
import { AccountContext } from "../context/AccountContext";

const API = import.meta.env.VITE_API_URL;

const SUGGESTIONS = [
  "What are my top cost drivers this month?",
  "Which EC2 instances are idle?",
  "How much can I save with Reserved Instances?",
  "Show me my cost trend for the last 30 days",
];

export default function AICopilot() {
  const { activeAccount, getAuthHeader } = useContext(AccountContext);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm your FinOps AI Copilot. Ask me anything about your AWS costs, waste, or optimization opportunities." }
  ]);
  const [input, setInput]     = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  async function sendMessage(text) {
    const msg = text || input.trim();
    if (!msg) return;
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: msg }]);
    setLoading(true);

    try {
      const headers = await getAuthHeader();
      const chatHistory = messages.slice(-6).map(m => ({ role: m.role, content: m.content }));

      const res = await fetch(`${API}/copilot/ask`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({
          question: msg,
          chat_history: chatHistory,
        }),
      });

      const data = await res.json();
      const answer = data.answer || data.detail || "Sorry, I couldn't get a response.";
      setMessages(prev => [...prev, { role: "assistant", content: answer }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: "assistant", content: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  if (!activeAccount) return <div className="p-8 text-gray-400">Select an AWS account first.</div>;

  return (
    <div className="flex flex-col h-full gap-4 p-6" style={{ height: "calc(100vh - 80px)" }}>
      <div>
        <h1 className="text-2xl font-bold text-white">🤖 AI Copilot</h1>
        <p className="text-gray-400 text-sm mt-1">Ask questions about your AWS costs in plain English</p>
      </div>

      {/* Chat messages */}
      <div className="flex-1 bg-gray-900 border border-gray-800 rounded-xl overflow-y-auto p-4 space-y-4 min-h-0">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-lg px-4 py-3 text-sm rounded-2xl whitespace-pre-wrap ${
              m.role === "user" ? "bg-indigo-600 text-white" : "bg-gray-800 text-gray-200"
            }`}>
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 rounded-2xl px-4 py-3 text-sm text-gray-400">Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      <div className="flex flex-wrap gap-2">
        {SUGGESTIONS.map(s => (
          <button key={s} onClick={() => sendMessage(s)}
            className="text-xs px-3 py-1.5 bg-gray-800 border border-gray-700 text-gray-300 rounded-full hover:border-indigo-500 hover:text-white transition-colors">
            {s}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && sendMessage()}
          placeholder="Ask about your AWS costs..."
          className="flex-1 bg-gray-900 border border-gray-700 text-white rounded-xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500"
        />
        <button onClick={() => sendMessage()}
          className="px-5 py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-semibold text-sm transition-colors">
          Send
        </button>
      </div>
    </div>
  );
}