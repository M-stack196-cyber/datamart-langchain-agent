import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Clock,
  DollarSign,
  LoaderCircle,
  LogOut,
  Mail,
  MessageSquareWarning,
  RefreshCw,
  Send,
  ShieldCheck,
  UserRound,
  Users,
  XCircle,
} from "lucide-react";

import "./admin.css";
import "./live-chat.css";


const API_URL =
  import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:8000" : "");


export default function AdminDashboard() {
  const [leads, setLeads] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [handoffs, setHandoffs] = useState([]);
  const [queue, setQueue] = useState([]);
  const [activeChats, setActiveChats] = useState([]);

  const [activeTab, setActiveTab] = useState("leads");
  const [selectedChat, setSelectedChat] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [reply, setReply] = useState("");
  const [loading, setLoading] = useState(true);
  const [checkingSession, setCheckingSession] = useState(true);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");


  useEffect(() => {
    checkSession();
  }, []);


  useEffect(() => {
    if (activeTab !== "live") return;

    loadLiveLists();
    const interval = setInterval(loadLiveLists, 3000);
    return () => clearInterval(interval);
  }, [activeTab]);


  useEffect(() => {
    if (!selectedChat) return;

    loadChatMessages(selectedChat);
    const interval = setInterval(
      () => loadChatMessages(selectedChat),
      2000
    );

    return () => clearInterval(interval);
  }, [selectedChat]);


  async function checkSession() {
    try {
      const response = await fetch(
        `${API_URL}/api/admin/session`,
        {
          method: "GET",
          credentials: "include",
        }
      );

      if (!response.ok) {
        window.location.href = "/admin/login";
        return;
      }

      const data = await response.json();

      setUsername(data.username || "admin");
      setCheckingSession(false);

      await loadDashboard();
    } catch (error) {
      console.error(error);
      window.location.href = "/admin/login";
    }
  }


  async function protectedFetch(url, options = {}) {
    const response = await fetch(url, {
      ...options,
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
    });

    if (response.status === 401) {
      window.location.href = "/admin/login";
      throw new Error("Session expired.");
    }

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(
        data.detail || `Request failed with status ${response.status}`
      );
    }

    return data;
  }


  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [leadsData, meetingsData, handoffsData] =
        await Promise.all([
          protectedFetch(`${API_URL}/api/leads`),
          protectedFetch(`${API_URL}/api/meetings`),
          protectedFetch(`${API_URL}/api/handoffs`),
        ]);

      setLeads(leadsData);
      setMeetings(meetingsData);
      setHandoffs(handoffsData);
      await loadLiveLists();
    } catch (error) {
      if (error.message !== "Session expired.") {
        setError(error.message || "Unable to load dashboard data.");
      }
    } finally {
      setLoading(false);
    }
  }


  async function loadLiveLists() {
    try {
      const [queueData, activeData] = await Promise.all([
        protectedFetch(`${API_URL}/api/admin/handoff/queue`),
        protectedFetch(`${API_URL}/api/admin/handoff/active`),
      ]);
      setQueue(queueData);
      setActiveChats(activeData);
    } catch (error) {
      console.error("Live handoff refresh failed:", error);
    }
  }


  async function claimChat(conversationId) {
    await protectedFetch(
      `${API_URL}/api/admin/handoff/${conversationId}/claim`,
      { method: "POST" }
    );
    setSelectedChat(conversationId);
    await loadLiveLists();
  }


  async function loadChatMessages(conversationId) {
    try {
      const data = await protectedFetch(
        `${API_URL}/api/admin/handoff/${conversationId}/messages`
      );
      setChatMessages(data.messages || []);
    } catch (error) {
      console.error("Unable to load live messages:", error);
    }
  }


  async function sendReply() {
    const text = reply.trim();
    if (!text || !selectedChat) return;

    await protectedFetch(
      `${API_URL}/api/admin/handoff/${selectedChat}/message`,
      {
        method: "POST",
        body: JSON.stringify({ message: text }),
      }
    );
    setReply("");
    await loadChatMessages(selectedChat);
  }


  async function endChat() {
    if (!selectedChat) return;

    await protectedFetch(
      `${API_URL}/api/admin/handoff/${selectedChat}/end`,
      { method: "POST" }
    );
    setSelectedChat(null);
    setChatMessages([]);
    await loadLiveLists();
  }


  async function handleLogout() {
    try {
      await fetch(
        `${API_URL}/api/admin/logout`,
        {
          method: "POST",
          credentials: "include",
        }
      );
    } finally {
      window.location.href = "/admin/login";
    }
  }


  if (checkingSession) {
    return (
      <main className="admin-page">
        <div className="admin-state">
          <LoaderCircle className="admin-spin" size={26} />
          <p>Verifying admin session...</p>
        </div>
      </main>
    );
  }


  return (
    <main className="admin-page">
      <section className="admin-shell">
        <header className="admin-header">
          <div>
            <button
              type="button"
              className="back-link"
              onClick={() => {
                window.location.href = "/";
              }}
            >
              <ArrowLeft size={16} />
              Back to Assistant
            </button>

            <div className="admin-title-area">
              <div className="admin-title-icon">
                <ShieldCheck size={24} />
              </div>

              <div>
                <h1>Datamart AI Admin</h1>
                <p>
                  Manage leads, meetings and live human handoffs.
                </p>
              </div>
            </div>
          </div>

          <div className="admin-header-actions">
            <div className="admin-user">
              <UserRound size={16} />
              <span>
                Signed in as <strong>{username}</strong>
              </span>
            </div>

            <button
              type="button"
              className="refresh-button"
              onClick={loadDashboard}
              disabled={loading}
            >
              <RefreshCw
                size={16}
                className={loading ? "admin-spin" : ""}
              />
              Refresh
            </button>

            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>


        <section className="admin-stats">
          <Stat icon={<Users size={21} />} label="Total Leads" value={leads.length} />
          <Stat icon={<CalendarDays size={21} />} label="Meeting Requests" value={meetings.length} />
          <Stat
            icon={<MessageSquareWarning size={21} />}
            label="Waiting Live Chats"
            value={queue.length}
          />
        </section>


        <div className="admin-tabs">
          <Tab active={activeTab === "leads"} onClick={() => setActiveTab("leads")} label="Leads" count={leads.length} />
          <Tab active={activeTab === "meetings"} onClick={() => setActiveTab("meetings")} label="Meetings" count={meetings.length} />
          <Tab active={activeTab === "handoffs"} onClick={() => setActiveTab("handoffs")} label="Handoffs" count={handoffs.length} />
          <Tab active={activeTab === "live"} onClick={() => setActiveTab("live")} label="Live Chats" count={queue.length + activeChats.length} />
        </div>


        <section className="admin-content">
          {error && (
            <div className="admin-state">
              <p>{error}</p>
            </div>
          )}

          {!error && loading && (
            <div className="admin-state">
              <LoaderCircle className="admin-spin" size={25} />
              <p>Loading dashboard data...</p>
            </div>
          )}

          {!error && !loading && activeTab === "leads" && (
            <LeadTable leads={leads} />
          )}

          {!error && !loading && activeTab === "meetings" && (
            <MeetingTable meetings={meetings} />
          )}

          {!error && !loading && activeTab === "handoffs" && (
            <HandoffTable handoffs={handoffs} />
          )}

          {!error && !loading && activeTab === "live" && (
            <LiveChatPanel
              queue={queue}
              activeChats={activeChats}
              selectedChat={selectedChat}
              setSelectedChat={setSelectedChat}
              chatMessages={chatMessages}
              claimChat={claimChat}
              reply={reply}
              setReply={setReply}
              sendReply={sendReply}
              endChat={endChat}
            />
          )}
        </section>
      </section>
    </main>
  );
}


function Stat({ icon, label, value }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <div>
        <span>{label}</span>
        <strong>{value}</strong>
      </div>
    </div>
  );
}


function Tab({ active, onClick, label, count }) {
  return (
    <button
      type="button"
      className={active ? "active" : ""}
      onClick={onClick}
    >
      {label}
      <span>{count}</span>
    </button>
  );
}


function LiveChatPanel({
  queue,
  activeChats,
  selectedChat,
  setSelectedChat,
  chatMessages,
  claimChat,
  reply,
  setReply,
  sendReply,
  endChat,
}) {
  return (
    <div className="live-grid">
      <aside className="live-sidebar">
        <h3>Waiting queue</h3>
        {!queue.length && <p className="live-muted">No visitors waiting.</p>}
        {queue.map((chat) => (
          <div className="live-card" key={chat.conversation_id}>
            <strong>{chat.visitor_name || "Visitor"}</strong>
            <span>{chat.visitor_email || "No email"}</span>
            <p>{chat.reason || "Human support requested"}</p>
            <button onClick={() => claimChat(chat.conversation_id)}>
              Claim chat
            </button>
          </div>
        ))}

        <h3>Active</h3>
        {!activeChats.length && <p className="live-muted">No active chats.</p>}
        {activeChats.map((chat) => (
          <button
            className={`live-active-button ${
              selectedChat === chat.conversation_id ? "selected" : ""
            }`}
            key={chat.conversation_id}
            onClick={() => setSelectedChat(chat.conversation_id)}
          >
            {chat.visitor_name || "Visitor"}
          </button>
        ))}
      </aside>

      <section className="live-workspace">
        {!selectedChat ? (
          <div className="admin-state">
            <p>Claim or open a live chat to start messaging.</p>
          </div>
        ) : (
          <>
            <div className="live-messages">
              {chatMessages.map((message) => (
                <div
                  key={message.id}
                  className={`live-message ${message.role}`}
                >
                  <small>{message.role}</small>
                  <div>{message.content}</div>
                </div>
              ))}
            </div>

            <div className="live-composer">
              <input
                value={reply}
                onChange={(event) => setReply(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter") sendReply();
                }}
                placeholder="Reply to visitor..."
              />
              <button onClick={sendReply}>
                <Send size={16} />
                Send
              </button>
              <button className="live-end" onClick={endChat}>
                <XCircle size={16} />
                End
              </button>
            </div>
          </>
        )}
      </section>
    </div>
  );
}


function LeadTable({ leads }) {
  if (!leads.length) return <EmptyState message="No leads have been captured yet." />;

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>Contact</th><th>Company</th><th>Project</th>
            <th>Budget</th><th>Timeline</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td>
                <div className="primary-cell"><UserRound size={15} />{lead.name || "Unknown"}</div>
                {lead.email && <div className="secondary-cell"><Mail size={13} />{lead.email}</div>}
                {lead.phone && <div className="secondary-cell">{lead.phone}</div>}
              </td>
              <td><div className="primary-cell"><Building2 size={15} />{lead.company || "—"}</div></td>
              <td>{lead.project_description || "—"}</td>
              <td><div className="primary-cell"><DollarSign size={15} />{lead.budget || "—"}</div></td>
              <td><div className="primary-cell"><Clock size={15} />{lead.timeline || "—"}</div></td>
              <td><StatusBadge status={lead.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function MeetingTable({ meetings }) {
  if (!meetings.length) return <EmptyState message="No meeting requests yet." />;

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>Contact</th><th>Date</th><th>Time</th>
            <th>Timezone</th><th>Notes</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          {meetings.map((meeting) => (
            <tr key={meeting.id}>
              <td>
                <div className="primary-cell"><UserRound size={15} />{meeting.name || "Unknown"}</div>
                {meeting.email && <div className="secondary-cell"><Mail size={13} />{meeting.email}</div>}
              </td>
              <td>{meeting.preferred_date || "—"}</td>
              <td>{meeting.preferred_time || "—"}</td>
              <td>{meeting.timezone || "—"}</td>
              <td>{meeting.notes || "—"}</td>
              <td><StatusBadge status={meeting.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function HandoffTable({ handoffs }) {
  if (!handoffs.length) return <EmptyState message="No human handoff requests yet." />;

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr><th>ID</th><th>Conversation</th><th>Reason</th><th>Status</th></tr>
        </thead>
        <tbody>
          {handoffs.map((handoff) => (
            <tr key={handoff.id}>
              <td>#{handoff.id}</td>
              <td><span className="conversation-id">{handoff.conversation_id}</span></td>
              <td>{handoff.reason || "—"}</td>
              <td><StatusBadge status={handoff.status} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function StatusBadge({ status }) {
  const normalizedStatus = (status || "unknown")
    .toLowerCase()
    .replaceAll(" ", "-");

  return (
    <span className={`admin-status ${normalizedStatus}`}>
      {status || "Unknown"}
    </span>
  );
}


function EmptyState({ message }) {
  return (
    <div className="admin-state">
      <p>{message}</p>
    </div>
  );
}
