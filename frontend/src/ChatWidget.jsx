import { useEffect, useRef, useState } from "react";
import {
  Bot,
  Send,
  Sparkles,
  UserRound,
  LoaderCircle,
  Database,
  Workflow,
  Headphones,
  Plus,
} from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";


const API_URL =
  import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : "");

const STORAGE_KEY = "datamartConversationId";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm **Datamart's AI Assistant**. I can answer questions about Datamart, help with project enquiries, schedule meeting requests, or connect you with the team.",
};

const QUICK_PROMPTS = [
  "What AI services does Datamart provide?",
  "I need an AI solution for my company",
  "Schedule a meeting with the Datamart team",
  "Connect me with a human",
];


export default function ChatWidget() {
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [restoring, setRestoring] = useState(true);
  const [liveMode, setLiveMode] = useState("bot");
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);

  const lastLiveMessageId = useRef(0);
  const messagesEndRef = useRef(null);


  // Restore the same visitor conversation after refresh/navigation, matching
  // the public visitor behavior from the previous Datamart chatbot.
  useEffect(() => {
    restoreSavedConversation();
  }, []);


  // Poll status + new employee/system messages while a conversation exists.
  useEffect(() => {
    if (!conversationId) return;

    let cancelled = false;

    async function pollLiveChat() {
      try {
        const response = await fetch(
          `${API_URL}/api/chat/${conversationId}/live?after_id=${lastLiveMessageId.current}`
        );

        if (!response.ok || cancelled) return;

        const data = await response.json();

        setLiveMode(data.mode || "bot");

        if (Number.isInteger(data.last_message_id)) {
          lastLiveMessageId.current = Math.max(
            lastLiveMessageId.current,
            data.last_message_id
          );
        }

        const incoming = data.messages || [];

        if (incoming.length) {
          setMessages((current) => [
            ...current,
            ...incoming.map((message) => ({
              role: "assistant",
              sourceRole: message.role,
              serverId: message.id,
              content: message.content,
              live: true,
            })),
          ]);
        }
      } catch (error) {
        console.error("Live chat poll failed:", error);
      }
    }

    pollLiveChat();
    const interval = setInterval(pollLiveChat, 2500);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [conversationId]);


  useEffect(() => {
    if (messages.length === 1 && !loading) {
      return;
    }

    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [messages, loading]);


  async function restoreSavedConversation() {
    const savedId = localStorage.getItem(STORAGE_KEY);

    if (!savedId) {
      setRestoring(false);
      return;
    }

    try {
      const response = await fetch(
        `${API_URL}/api/chat/${savedId}/history`
      );

      if (!response.ok) {
        throw new Error("Unable to restore conversation.");
      }

      const data = await response.json();
      const history = data.messages || [];

      if (!history.length) {
        localStorage.removeItem(STORAGE_KEY);
        setRestoring(false);
        return;
      }

      const restored = history.map((message) => ({
        role:
          message.role === "user"
            ? "user"
            : "assistant",
        sourceRole: message.role,
        serverId: message.id,
        content: message.content,
        live:
          message.role === "agent" ||
          message.role === "system",
      }));

      const maxId = history.reduce(
        (max, message) =>
          Number.isInteger(message.id)
            ? Math.max(max, message.id)
            : max,
        0
      );

      lastLiveMessageId.current = maxId;
      setMessages(restored);
      setConversationId(savedId);

      const statusResponse = await fetch(
        `${API_URL}/api/chat/${savedId}/live?after_id=${maxId}`
      );

      if (statusResponse.ok) {
        const status = await statusResponse.json();
        setLiveMode(status.mode || "bot");
      }
    } catch (error) {
      console.error("Conversation restore failed:", error);
      localStorage.removeItem(STORAGE_KEY);
      setConversationId(null);
      setMessages([WELCOME_MESSAGE]);
      setLiveMode("bot");
      lastLiveMessageId.current = 0;
    } finally {
      setRestoring(false);
    }
  }


  function startNewConversation() {
    if (conversationId) {
      const confirmed = window.confirm(
        "Start a new conversation? Your previous chat will remain saved in the database."
      );

      if (!confirmed) return;
    }

    localStorage.removeItem(STORAGE_KEY);
    setConversationId(null);
    setLiveMode("bot");
    setMessages([WELCOME_MESSAGE]);
    setInput("");
    lastLiveMessageId.current = 0;
  }


  async function sendMessage(textOverride = null) {
    const text =
      typeof textOverride === "string"
        ? textOverride.trim()
        : input.trim();

    if (!text || loading || restoring) {
      return;
    }

    let activeConversationId = conversationId;

    if (!activeConversationId) {
      activeConversationId = crypto.randomUUID();
      localStorage.setItem(
        STORAGE_KEY,
        activeConversationId
      );
      setConversationId(activeConversationId);
    }

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
      const response = await fetch(
        `${API_URL}/api/chat`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: text,
            conversation_id: activeConversationId,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Unable to get a response."
        );
      }

      const returnedId =
        data.conversation_id || activeConversationId;

      setConversationId(returnedId);
      localStorage.setItem(STORAGE_KEY, returnedId);

      // Human mode intentionally returns an empty response: the employee reply
      // arrives through live polling instead of the AI.
      if (data.response) {
        setMessages((current) => [
          ...current,
          {
            role: "assistant",
            content: data.response,
          },
        ]);
      }
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


  const humanConnected = liveMode === "human";
  const humanWaiting = liveMode === "pending_human";
  const chatClosed = liveMode === "closed";


  if (restoring) {
    return (
      <main className="page">
        <section className="chat-shell">
          <div className="messages">
            <div className="message-row assistant">
              <div className="avatar assistant">
                <Bot size={17} />
              </div>
              <div className="message assistant thinking">
                <LoaderCircle className="spinner" size={17} />
                Restoring your conversation...
              </div>
            </div>
          </div>
        </section>
      </main>
    );
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
                  {humanConnected
                    ? "Human connected"
                    : humanWaiting
                    ? "Waiting for team"
                    : chatClosed
                    ? "Chat ended"
                    : "Online"}
                </span>
              </div>

              <p>
                LangChain Agent • Groq • RAG
              </p>
            </div>
          </div>

          <div className="header-actions">
            <div className="agent-badge">
              {humanConnected ? (
                <Headphones size={15} />
              ) : (
                <Sparkles size={15} />
              )}
              {humanConnected ? "Live Support" : "Agentic AI"}
            </div>

            <button
              type="button"
              className="admin-entry-button"
              onClick={startNewConversation}
            >
              <Plus size={15} />
              New Conversation
            </button>
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
              key={
                message.serverId
                  ? `server-${message.serverId}`
                  : `${message.role}-${index}`
              }
              className={`message-row ${message.role}`}
            >
              <div className={`avatar ${message.role}`}>
                {message.role === "assistant" ? (
                  message.live ? (
                    <Headphones size={17} />
                  ) : (
                    <Bot size={17} />
                  )
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

          {loading && !humanConnected && (
            <div className="message-row assistant">
              <div className="avatar assistant">
                <Bot size={17} />
              </div>

              <div className="message assistant thinking">
                <LoaderCircle
                  className="spinner"
                  size={17}
                />
                {humanWaiting
                  ? "Sending your message..."
                  : "Datamart AI is thinking..."}
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
              placeholder={
                humanConnected
                  ? "Message the Datamart team..."
                  : humanWaiting
                  ? "Send another message while you wait..."
                  : "Ask Datamart anything..."
              }
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
            {humanConnected
              ? "You are chatting with a Datamart team member. AI replies are paused."
              : humanWaiting
              ? "Your request is waiting in the live-support queue."
              : chatClosed
              ? "The live chat ended. You can continue with the AI or start a new conversation."
              : "AI responses are generated from Datamart's knowledge base and available agent tools."}
          </p>
        </div>
      </section>
    </main>
  );
}
