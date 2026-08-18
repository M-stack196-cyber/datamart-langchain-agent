import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Send,
  Sparkles,
  UserRound,
  LoaderCircle,
  Database,
  Workflow,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

const QUICK_PROMPTS = [
  "What AI services does Datamart provide?",
  "I need an AI solution for my company",
  "Schedule a meeting with the Datamart team",
  "Connect me with a human",
];

export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm **Datamart's AI Assistant**. I can answer questions about Datamart, help with project enquiries, schedule meeting requests, or connect you with the team.",
    },
  ]);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loading]);

  async function sendMessage(textOverride = null) {
    const text =
      typeof textOverride === "string"
        ? textOverride.trim()
        : input.trim();

    if (!text || loading) return;

    setMessages((current) => [
      ...current,
      {
        role: "user",
        content: text,
      },
    ]);

    setInput("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to get a response."
        );
      }

      setConversationId(data.conversation_id);

      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: data.response,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content:
            `Sorry, I couldn't process that request.\n\n` +
            `**Error:** ${error.message}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    sendMessage();
  }

  return (
    <main className="page">
      <div className="background-orb orb-one" />
      <div className="background-orb orb-two" />

      <section className="chat-shell">
        <header className="header">
          <div className="brand">
            <div className="brand-icon">
              <Bot size={26} />
            </div>

            <div className="brand-copy">
              <div className="title-row">
                <h1>Datamart AI Assistant</h1>

                <span className="status">
                  <span className="status-dot" />
                  Online
                </span>
              </div>

              <p>
                LangChain Agent • Groq • RAG
              </p>
            </div>
          </div>

          <div className="agent-badge">
            <Sparkles size={15} />
            Agentic AI
          </div>
        </header>

        <div className="capability-strip">
          <span>
            <Database size={14} />
            Datamart Knowledge
          </span>

          <span>
            <Workflow size={14} />
            Tool Calling
          </span>

          <span>
            <Sparkles size={14} />
            Conversation Memory
          </span>
        </div>

        <div className="messages">
          {messages.map((message, index) => (
            <div
              key={`${message.role}-${index}`}
              className={`message-row ${message.role}`}
            >
              <div className={`avatar ${message.role}`}>
                {message.role === "assistant" ? (
                  <Bot size={17} />
                ) : (
                  <UserRound size={17} />
                )}
              </div>

              <div
                className={`message ${message.role}`}
              >
                {message.role === "assistant" ? (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                  >
                    {message.content}
                  </ReactMarkdown>
                ) : (
                  message.content
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="message-row assistant">
              <div className="avatar assistant">
                <Bot size={17} />
              </div>

              <div className="message assistant thinking">
                <LoaderCircle
                  className="spinner"
                  size={17}
                />
                Datamart AI is thinking...
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {messages.length === 1 && (
          <div className="quick-prompts">
            <p>Try asking:</p>

            <div className="prompt-grid">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => sendMessage(prompt)}
                  disabled={loading}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="composer-section">
          <form
            className="composer"
            onSubmit={handleSubmit}
          >
            <input
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              placeholder="Ask Datamart anything..."
              disabled={loading}
              autoFocus
            />

            <button
              type="submit"
              disabled={loading || !input.trim()}
              aria-label="Send message"
            >
              {loading ? (
                <LoaderCircle
                  className="spinner"
                  size={19}
                />
              ) : (
                <Send size={19} />
              )}
            </button>
          </form>

          <p className="disclaimer">
            AI responses are generated from Datamart's
            knowledge base and available agent tools.
          </p>
        </div>
      </section>
    </main>
  );
}