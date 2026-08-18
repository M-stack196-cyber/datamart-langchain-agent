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
  ShieldCheck,
  UserRound,
  Users,
} from "lucide-react";

import "./admin.css";


const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";


export default function AdminDashboard() {
  const [leads, setLeads] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [handoffs, setHandoffs] = useState([]);

  const [activeTab, setActiveTab] = useState("leads");
  const [loading, setLoading] = useState(true);
  const [checkingSession, setCheckingSession] = useState(true);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");


  useEffect(() => {
    checkSession();
  }, []);


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


  async function fetchProtected(url) {
    const response = await fetch(url, {
      credentials: "include",
    });

    if (response.status === 401) {
      window.location.href = "/admin/login";
      throw new Error("Session expired.");
    }

    if (!response.ok) {
      throw new Error(
        `Request failed with status ${response.status}`
      );
    }

    return response.json();
  }


  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const [
        leadsData,
        meetingsData,
        handoffsData,
      ] = await Promise.all([
        fetchProtected(`${API_URL}/api/leads`),
        fetchProtected(`${API_URL}/api/meetings`),
        fetchProtected(`${API_URL}/api/handoffs`),
      ]);

      setLeads(leadsData);
      setMeetings(meetingsData);
      setHandoffs(handoffsData);
    } catch (error) {
      if (error.message !== "Session expired.") {
        setError(
          error.message ||
            "Unable to load dashboard data."
        );
      }
    } finally {
      setLoading(false);
    }
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
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      window.location.href = "/admin/login";
    }
  }


  if (checkingSession) {
    return (
      <main className="admin-page">
        <div className="admin-state">
          <LoaderCircle
            className="admin-spin"
            size={26}
          />
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
                  Manage chatbot leads, meeting requests,
                  and human handoffs.
                </p>
              </div>
            </div>
          </div>

          <div className="admin-header-actions">
            <div className="admin-user">
              <UserRound size={16} />

              <span>
                Signed in as{" "}
                <strong>{username}</strong>
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
                className={
                  loading ? "admin-spin" : ""
                }
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
          <div className="stat-card">
            <div className="stat-icon">
              <Users size={21} />
            </div>

            <div>
              <span>Total Leads</span>
              <strong>{leads.length}</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <CalendarDays size={21} />
            </div>

            <div>
              <span>Meeting Requests</span>
              <strong>{meetings.length}</strong>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">
              <MessageSquareWarning size={21} />
            </div>

            <div>
              <span>Human Handoffs</span>
              <strong>{handoffs.length}</strong>
            </div>
          </div>
        </section>


        <div className="admin-tabs">
          <button
            type="button"
            className={
              activeTab === "leads" ? "active" : ""
            }
            onClick={() => setActiveTab("leads")}
          >
            Leads
            <span>{leads.length}</span>
          </button>

          <button
            type="button"
            className={
              activeTab === "meetings" ? "active" : ""
            }
            onClick={() => setActiveTab("meetings")}
          >
            Meetings
            <span>{meetings.length}</span>
          </button>

          <button
            type="button"
            className={
              activeTab === "handoffs" ? "active" : ""
            }
            onClick={() => setActiveTab("handoffs")}
          >
            Handoffs
            <span>{handoffs.length}</span>
          </button>
        </div>


        <section className="admin-content">
          {error && (
            <div className="admin-state">
              <p>{error}</p>

              <button
                type="button"
                className="refresh-button"
                onClick={loadDashboard}
              >
                Try Again
              </button>
            </div>
          )}

          {!error && loading && (
            <div className="admin-state">
              <LoaderCircle
                className="admin-spin"
                size={25}
              />
              <p>Loading dashboard data...</p>
            </div>
          )}

          {!error &&
            !loading &&
            activeTab === "leads" && (
              <LeadTable leads={leads} />
            )}

          {!error &&
            !loading &&
            activeTab === "meetings" && (
              <MeetingTable meetings={meetings} />
            )}

          {!error &&
            !loading &&
            activeTab === "handoffs" && (
              <HandoffTable handoffs={handoffs} />
            )}
        </section>
      </section>
    </main>
  );
}


function LeadTable({ leads }) {
  if (!leads.length) {
    return (
      <EmptyState message="No leads have been captured yet." />
    );
  }

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>Contact</th>
            <th>Company</th>
            <th>Project</th>
            <th>Budget</th>
            <th>Timeline</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {leads.map((lead) => (
            <tr key={lead.id}>
              <td>
                <div className="primary-cell">
                  <UserRound size={15} />
                  {lead.name || "Unknown"}
                </div>

                {lead.email && (
                  <div className="secondary-cell">
                    <Mail size={13} />
                    {lead.email}
                  </div>
                )}

                {lead.phone && (
                  <div className="secondary-cell">
                    {lead.phone}
                  </div>
                )}
              </td>

              <td>
                <div className="primary-cell">
                  <Building2 size={15} />
                  {lead.company || "—"}
                </div>
              </td>

              <td>
                {lead.project_description || "—"}
              </td>

              <td>
                <div className="primary-cell">
                  <DollarSign size={15} />
                  {lead.budget || "—"}
                </div>
              </td>

              <td>
                <div className="primary-cell">
                  <Clock size={15} />
                  {lead.timeline || "—"}
                </div>
              </td>

              <td>
                <StatusBadge status={lead.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function MeetingTable({ meetings }) {
  if (!meetings.length) {
    return (
      <EmptyState message="No meeting requests yet." />
    );
  }

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>Contact</th>
            <th>Date</th>
            <th>Time</th>
            <th>Timezone</th>
            <th>Notes</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {meetings.map((meeting) => (
            <tr key={meeting.id}>
              <td>
                <div className="primary-cell">
                  <UserRound size={15} />
                  {meeting.name || "Unknown"}
                </div>

                {meeting.email && (
                  <div className="secondary-cell">
                    <Mail size={13} />
                    {meeting.email}
                  </div>
                )}
              </td>

              <td>
                {meeting.preferred_date || "—"}
              </td>

              <td>
                {meeting.preferred_time || "—"}
              </td>

              <td>
                {meeting.timezone || "—"}
              </td>

              <td>
                {meeting.notes || "—"}
              </td>

              <td>
                <StatusBadge
                  status={meeting.status}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function HandoffTable({ handoffs }) {
  if (!handoffs.length) {
    return (
      <EmptyState message="No human handoff requests yet." />
    );
  }

  return (
    <div className="table-wrapper">
      <table className="admin-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Conversation</th>
            <th>Reason</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>
          {handoffs.map((handoff) => (
            <tr key={handoff.id}>
              <td>#{handoff.id}</td>

              <td>
                <span className="conversation-id">
                  {handoff.conversation_id}
                </span>
              </td>

              <td>{handoff.reason || "—"}</td>

              <td>
                <StatusBadge
                  status={handoff.status}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}


function StatusBadge({ status }) {
  const normalizedStatus = (
    status || "unknown"
  )
    .toLowerCase()
    .replaceAll(" ", "-");

  return (
    <span
      className={`admin-status ${normalizedStatus}`}
    >
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