import re
from datetime import datetime, timezone

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.db.models import (
    ConversationFlowState,
    ConversationMessage,
    HandoffRequest,
    HandoffSession,
)
from app.graph.state import ChatState


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,148}$")


def _latest_user_text(state: ChatState) -> str:
    for message in reversed(state.get("messages", [])):
        if getattr(message, "type", "") == "human":
            return str(getattr(message, "content", "")).strip()
    return ""


def _flow(db: Session, conversation_id: str) -> ConversationFlowState:
    row = (
        db.query(ConversationFlowState)
        .filter(ConversationFlowState.conversation_id == conversation_id)
        .first()
    )
    if not row:
        row = ConversationFlowState(conversation_id=conversation_id, mode="bot")
        db.add(row)
        db.flush()
    return row


def _session(db: Session, conversation_id: str) -> HandoffSession:
    row = (
        db.query(HandoffSession)
        .filter(HandoffSession.conversation_id == conversation_id)
        .first()
    )
    if not row:
        row = HandoffSession(conversation_id=conversation_id, mode="collecting")
        db.add(row)
        db.flush()
    return row


def make_process_handoff_node(db: Session, conversation_id: str):
    def process_handoff(state: ChatState) -> dict:
        text = _latest_user_text(state)
        flow = _flow(db, conversation_id)
        handoff = _session(db, conversation_id)

        # Already waiting/connected: the normal chat service handles new visitor
        # messages without invoking the AI. This protects human-mode silence.
        if handoff.mode == "pending_human":
            return {
                "response": (
                    "Your request is already in the Datamart live-chat queue. "
                    "You can keep sending messages while you wait."
                )
            }

        if handoff.mode == "human":
            return {"response": "Your message was sent to the Datamart team."}

        if flow.active_flow != "handoff":
            flow.active_flow = "handoff"
            flow.pending_field = "name"
            handoff.mode = "collecting"
            db.commit()
            return {"response": "Before I connect you, what is your **full name**?"}

        pending = flow.pending_field or "name"

        if pending == "name":
            if len(text.split()) < 2 or not NAME_RE.match(text.strip()):
                return {
                    "response": (
                        "Please enter your **full name** "
                        "(for example, `Ali Khan`)."
                    )
                }
            handoff.visitor_name = text.strip()
            flow.pending_field = "email"
            db.commit()
            return {
                "response": (
                    "Thanks. What is your **email address** so the team can "
                    "follow up if the live chat disconnects?"
                )
            }

        if pending == "email":
            email = text.strip().lower()
            if not EMAIL_RE.match(email):
                return {"response": "Please enter a **valid email address**."}
            handoff.visitor_email = email
            flow.pending_field = "reason"
            db.commit()
            return {
                "response": (
                    "Briefly, what would you like to **speak with the team about**?"
                )
            }

        if pending == "reason":
            if len(text.strip()) < 3:
                return {
                    "response": (
                        "Please give a short reason for the handoff request."
                    )
                }

            now = datetime.now(timezone.utc)
            handoff.reason = text.strip()
            handoff.mode = "pending_human"
            handoff.requested_at = now

            existing = (
                db.query(HandoffRequest)
                .filter(
                    HandoffRequest.conversation_id == conversation_id,
                    HandoffRequest.status.in_(["pending", "claimed"]),
                )
                .order_by(HandoffRequest.id.desc())
                .first()
            )
            if not existing:
                db.add(
                    HandoffRequest(
                        conversation_id=conversation_id,
                        reason=handoff.reason,
                        status="pending",
                    )
                )

            flow.active_flow = None
            flow.pending_field = None
            flow.mode = "pending_human"

            db.commit()

            return {
                "response": (
                    "Your live-chat request is now in the **Datamart team queue**. "
                    "You can keep this page open and continue sending messages. "
                    "The assistant will stay silent once a team member joins."
                )
            }

        flow.pending_field = "name"
        db.commit()
        return {"response": "Before I connect you, what is your **full name**?"}

    return process_handoff


def build_handoff_subgraph(db: Session, conversation_id: str):
    builder = StateGraph(ChatState)
    builder.add_node(
        "process_handoff",
        make_process_handoff_node(db, conversation_id),
    )
    builder.add_edge(START, "process_handoff")
    builder.add_edge("process_handoff", END)
    return builder.compile()
