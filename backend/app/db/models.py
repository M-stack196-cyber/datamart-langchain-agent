from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    project_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    budget: Mapped[str | None] = mapped_column(String(100), nullable=True)
    timeline: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MeetingRequest(Base):
    __tablename__ = "meeting_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    preferred_date: Mapped[str | None] = mapped_column(String(80), nullable=True)
    preferred_time: Mapped[str | None] = mapped_column(String(80), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="requested")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class HandoffRequest(Base):
    __tablename__ = "handoff_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConversationFlowState(Base):
    """
    Durable workflow state for LangGraph business flows.
    """

    __tablename__ = "conversation_flow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )
    active_flow: Mapped[str | None] = mapped_column(String(40), nullable=True)
    pending_field: Mapped[str | None] = mapped_column(String(80), nullable=True)
    skipped_fields: Mapped[str] = mapped_column(Text, default="")
    mode: Mapped[str] = mapped_column(String(40), default="bot")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MeetingFlowState(Base):
    """
    Meeting-only transient state.

    A separate table avoids altering existing production columns and gives us a
    durable place to keep the exact slot list presented to the visitor.
    """

    __tablename__ = "meeting_flow_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(64), unique=True, index=True
    )
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    slots_json: Mapped[str] = mapped_column(Text, default="[]")
    selected_start_utc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    selected_end_utc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    selected_display: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )


class MeetingBooking(Base):
    """
    Google Calendar booking result. New table = no destructive SQLite migration.
    """

    __tablename__ = "meeting_bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    meeting_request_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    google_event_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_meet_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    html_link: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_utc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    end_utc: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="booked")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
