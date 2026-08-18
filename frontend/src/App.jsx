import { useState } from "react";
import { Bot, Send } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm Datamart's AI assistant. How can I help?" },
  ]);

  async function sendMessage(event) {
    event.preventDefault();
    const text = input.trim();
    if (!text || loading) return;

    setMessages((current) => [...current, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, conversation_id: conversationId }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Request failed");
      setConversationId(data.conversation_id);
      setMessages((current) => [...current, { role: "assistant", content: data.response }]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        { role: "assistant", content: `Error: ${error.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="chat-shell">
        <header className="header">
          <div className="brand-icon"><Bot size={24} /></div>
          <div>
            <h1>Datamart AI Assistant</h1>
            <p>Powered by LangChain</p>
          </div>
        </header>

        <div className="messages">
          {messages.map((message, index) => (
            <div key={index} className={`message ${message.role}`}>
              {message.content}
            </div>
          ))}
          {loading && <div className="message assistant muted">Thinking…</div>}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask Datamart anything…"
          />
          <button type="submit" disabled={loading || !input.trim()} aria-label="Send">
            <Send size={18} />
          </button>
        </form>
      </section>
    </main>
  );
}
