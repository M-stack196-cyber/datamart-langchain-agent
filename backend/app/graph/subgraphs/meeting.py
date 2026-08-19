import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.db.models import (
    ConversationFlowState,
    MeetingBooking,
    MeetingFlowState,
    MeetingRequest,
)
from app.graph.state import ChatState
from app.services.google_calendar_service import (
    GoogleCalendarConfigurationError,
    SlotUnavailableError,
    create_google_meeting,
    generate_available_slots,
    is_google_calendar_configured,
    parse_rfc3339,
    slot_display,
)


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,148}$")
YES_WORDS = {"yes", "y", "confirm", "confirmed", "book", "book it", "yes please"}
NO_WORDS = {"no", "n", "change", "another", "different", "choose another"}
CANCEL_WORDS = {"cancel", "cancel meeting", "stop", "never mind", "nevermind"}

FIELD_PROMPTS = {
    "name": "What is your **full name**?",
    "email": "What is your **email address**?",
    "timezone": (
        "What is your **timezone**? Please use a timezone such as "
        "`Asia/Karachi`, `Europe/London`, or `America/New_York`."
    ),
    "purpose": "What would you like to **discuss in the meeting**?",
    "preferred_date": (
        "Google Calendar is not connected yet, so I can save a meeting request. "
        "What is your **preferred date**?"
    ),
    "preferred_time": "What is your **preferred time**?",
}


def _latest_user_text(state: ChatState) -> str:
    for message in reversed(state.get("messages", [])):
        if getattr(message, "type", "") == "human":
            return str(getattr(message, "content", "")).strip()
    return ""


def _get_flow(db: Session, conversation_id: str) -> ConversationFlowState:
    flow = (
        db.query(ConversationFlowState)
        .filter(ConversationFlowState.conversation_id == conversation_id)
        .first()
    )
    if not flow:
        flow = ConversationFlowState(
            conversation_id=conversation_id,
            mode="bot",
        )
        db.add(flow)
        db.flush()
    return flow


def _get_meeting_state(db: Session, conversation_id: str) -> MeetingFlowState:
    meeting_state = (
        db.query(MeetingFlowState)
        .filter(MeetingFlowState.conversation_id == conversation_id)
        .first()
    )
    if not meeting_state:
        meeting_state = MeetingFlowState(
            conversation_id=conversation_id,
            slots_json="[]",
        )
        db.add(meeting_state)
        db.flush()
    return meeting_state


def _new_meeting_request(db: Session, conversation_id: str) -> MeetingRequest:
    request = MeetingRequest(
        conversation_id=conversation_id,
        status="collecting",
    )
    db.add(request)
    db.flush()
    return request


def _current_meeting_request(
    db: Session,
    conversation_id: str,
) -> MeetingRequest | None:
    return (
        db.query(MeetingRequest)
        .filter(
            MeetingRequest.conversation_id == conversation_id,
            MeetingRequest.status == "collecting",
        )
        .order_by(MeetingRequest.id.desc())
        .first()
    )


def _reset_meeting_state(meeting_state: MeetingFlowState) -> None:
    meeting_state.purpose = None
    meeting_state.slots_json = "[]"
    meeting_state.selected_start_utc = None
    meeting_state.selected_end_utc = None
    meeting_state.selected_display = None


def _valid_timezone(value: str) -> bool:
    try:
        ZoneInfo(value)
        return True
    except ZoneInfoNotFoundError:
        return False


def _slot_message(slots: list[dict], visitor_timezone: str) -> str:
    if not slots:
        return (
            "I couldn't find an available slot in the next 14 days. "
            "Please ask the Datamart team for a manual meeting time."
        )

    lines = [
        "Here are the next available **30-minute** slots:",
        "",
    ]

    for slot in slots:
        lines.append(
            f"{slot['number']}. {slot_display(slot, visitor_timezone)}"
        )

    lines.extend(
        [
            "",
            "Reply with the **slot number** you want, or say **cancel**.",
        ]
    )
    return "\n".join(lines)


def _persist_slot_snapshot(
    meeting_state: MeetingFlowState,
    slots: list[dict],
) -> None:
    meeting_state.slots_json = json.dumps(slots)


def _load_slot_snapshot(meeting_state: MeetingFlowState) -> list[dict]:
    try:
        value = json.loads(meeting_state.slots_json or "[]")
        return value if isinstance(value, list) else []
    except json.JSONDecodeError:
        return []


def make_process_meeting_node(db: Session, conversation_id: str):
    def process_meeting(state: ChatState) -> dict:
        text = _latest_user_text(state)
        lowered = text.strip().lower()

        flow = _get_flow(db, conversation_id)
        meeting_state = _get_meeting_state(db, conversation_id)

        if flow.active_flow != "meeting":
            _reset_meeting_state(meeting_state)
            request = _new_meeting_request(db, conversation_id)
            flow.active_flow = "meeting"
            flow.pending_field = "name"
            db.commit()
            return {"response": FIELD_PROMPTS["name"]}

        request = _current_meeting_request(db, conversation_id)
        if not request:
            request = _new_meeting_request(db, conversation_id)

        pending = flow.pending_field or "name"

        if lowered in CANCEL_WORDS:
            request.status = "cancelled"
            flow.active_flow = None
            flow.pending_field = None
            _reset_meeting_state(meeting_state)
            db.commit()
            return {
                "response": (
                    "Your meeting booking flow has been cancelled. "
                    "No calendar event was created."
                )
            }

        if pending == "name":
            if len(text.split()) < 2 or not NAME_RE.match(text):
                return {
                    "response": (
                        "Please enter your **full name** "
                        "(for example, `Ali Khan`)."
                    )
                }
            request.name = text.strip()
            flow.pending_field = "email"
            db.commit()
            return {"response": FIELD_PROMPTS["email"]}

        if pending == "email":
            email = text.strip().lower()
            if not EMAIL_RE.match(email):
                return {"response": "Please enter a **valid email address**."}
            request.email = email
            flow.pending_field = "timezone"
            db.commit()
            return {"response": FIELD_PROMPTS["timezone"]}

        if pending == "timezone":
            timezone_value = text.strip()
            if not _valid_timezone(timezone_value):
                return {
                    "response": (
                        "I couldn't recognize that timezone. "
                        "Please use an IANA timezone such as "
                        "`Asia/Karachi`, `Europe/London`, or `America/New_York`."
                    )
                }
            request.timezone = timezone_value
            flow.pending_field = "purpose"
            db.commit()
            return {"response": FIELD_PROMPTS["purpose"]}

        if pending == "purpose":
            if len(text.strip()) < 5:
                return {
                    "response": (
                        "Please give a short description of what you want "
                        "to discuss in the meeting."
                    )
                }

            meeting_state.purpose = text.strip()
            request.notes = text.strip()

            if is_google_calendar_configured():
                try:
                    slots = generate_available_slots()
                except Exception as error:
                    # Calendar credentials may exist but still be invalid/revoked.
                    flow.pending_field = "preferred_date"
                    db.commit()
                    return {
                        "response": (
                            "Google Calendar is configured but availability "
                            "could not be loaded right now. I can still save "
                            "a meeting request for the team.\n\n"
                            + FIELD_PROMPTS["preferred_date"]
                        )
                    }

                _persist_slot_snapshot(meeting_state, slots)

                if not slots:
                    request.status = "requested"
                    flow.active_flow = None
                    flow.pending_field = None
                    db.commit()
                    return {
                        "response": (
                            "I couldn't find an open Datamart slot in the next "
                            "14 days, so your meeting request has been saved for "
                            "manual follow-up."
                        )
                    }

                flow.pending_field = "slot"
                db.commit()
                return {
                    "response": _slot_message(
                        slots,
                        request.timezone or "Asia/Karachi",
                    )
                }

            flow.pending_field = "preferred_date"
            db.commit()
            return {"response": FIELD_PROMPTS["preferred_date"]}

        if pending == "preferred_date":
            if len(text.strip()) < 3:
                return {"response": FIELD_PROMPTS["preferred_date"]}
            request.preferred_date = text.strip()
            flow.pending_field = "preferred_time"
            db.commit()
            return {"response": FIELD_PROMPTS["preferred_time"]}

        if pending == "preferred_time":
            if len(text.strip()) < 2:
                return {"response": FIELD_PROMPTS["preferred_time"]}
            request.preferred_time = text.strip()
            request.status = "requested"
            flow.active_flow = None
            flow.pending_field = None
            db.commit()

            return {
                "response": (
                    "Thanks — your meeting request has been saved.\n\n"
                    f"**Name:** {request.name}\n"
                    f"**Email:** {request.email}\n"
                    f"**Preferred date:** {request.preferred_date}\n"
                    f"**Preferred time:** {request.preferred_time}\n"
                    f"**Timezone:** {request.timezone}\n"
                    f"**Purpose:** {request.notes}\n\n"
                    "Google Calendar is not connected to this environment yet, "
                    "so the Datamart team will confirm the final slot manually."
                )
            }

        if pending == "slot":
            slots = _load_slot_snapshot(meeting_state)

            try:
                selected_number = int(text.strip())
            except ValueError:
                return {
                    "response": (
                        "Please reply with one of the **slot numbers** shown "
                        "above, or say **cancel**."
                    )
                }

            selected = next(
                (
                    slot
                    for slot in slots
                    if int(slot.get("number", -1)) == selected_number
                ),
                None,
            )

            if not selected:
                return {
                    "response": (
                        "That slot number is not in the list. "
                        "Please choose one of the displayed numbers."
                    )
                }

            display = slot_display(
                selected,
                request.timezone or "Asia/Karachi",
            )

            meeting_state.selected_start_utc = selected["start_utc"]
            meeting_state.selected_end_utc = selected["end_utc"]
            meeting_state.selected_display = display

            start = parse_rfc3339(selected["start_utc"])
            local_start = start.astimezone(
                ZoneInfo(request.timezone or "Asia/Karachi")
            )

            request.preferred_date = local_start.strftime("%Y-%m-%d")
            request.preferred_time = local_start.strftime("%I:%M %p")
            flow.pending_field = "confirm"
            db.commit()

            return {
                "response": (
                    f"You selected **{display}**.\n\n"
                    "Should I book this slot and create the Google Meet event? "
                    "Reply **yes** to confirm, **no** to choose another slot, "
                    "or **cancel**."
                )
            }

        if pending == "confirm":
            if lowered in NO_WORDS:
                slots = _load_slot_snapshot(meeting_state)
                meeting_state.selected_start_utc = None
                meeting_state.selected_end_utc = None
                meeting_state.selected_display = None
                flow.pending_field = "slot"
                db.commit()
                return {
                    "response": _slot_message(
                        slots,
                        request.timezone or "Asia/Karachi",
                    )
                }

            if lowered not in YES_WORDS:
                return {
                    "response": (
                        "Please reply **yes** to book the selected slot, "
                        "**no** to choose another, or **cancel**."
                    )
                }

            if not (
                meeting_state.selected_start_utc
                and meeting_state.selected_end_utc
            ):
                flow.pending_field = "slot"
                db.commit()
                return {
                    "response": (
                        "The selected slot was lost. Please choose a slot again."
                    )
                }

            try:
                start_utc = parse_rfc3339(
                    meeting_state.selected_start_utc
                )
                end_utc = parse_rfc3339(
                    meeting_state.selected_end_utc
                )

                result = create_google_meeting(
                    visitor_name=request.name or "Visitor",
                    visitor_email=request.email or "",
                    meeting_purpose=meeting_state.purpose or request.notes or "",
                    start_utc=start_utc,
                    end_utc=end_utc,
                )
            except SlotUnavailableError:
                try:
                    slots = generate_available_slots()
                except Exception:
                    slots = []

                if slots:
                    _persist_slot_snapshot(meeting_state, slots)
                    flow.pending_field = "slot"
                    db.commit()
                    return {
                        "response": (
                            "That slot was taken before confirmation. "
                            "Here are the latest available times:\n\n"
                            + _slot_message(
                                slots,
                                request.timezone or "Asia/Karachi",
                            )
                        )
                    }

                request.status = "requested"
                flow.active_flow = None
                flow.pending_field = None
                db.commit()
                return {
                    "response": (
                        "The selected slot is no longer available. "
                        "Your request has been saved for manual follow-up."
                    )
                }
            except (
                GoogleCalendarConfigurationError,
                Exception,
            ) as error:
                request.status = "requested"
                flow.active_flow = None
                flow.pending_field = None
                db.commit()
                return {
                    "response": (
                        "I couldn't create the Google Calendar event right now, "
                        "but your meeting request has been saved for manual "
                        "follow-up."
                    )
                }

            booking = MeetingBooking(
                conversation_id=conversation_id,
                meeting_request_id=request.id,
                google_event_id=result.get("google_event_id"),
                google_meet_link=result.get("google_meet_link"),
                html_link=result.get("html_link"),
                start_utc=meeting_state.selected_start_utc,
                end_utc=meeting_state.selected_end_utc,
                status="booked",
            )
            db.add(booking)

            request.status = "booked"
            flow.active_flow = None
            flow.pending_field = None

            display = meeting_state.selected_display or "your selected time"
            meet_link = result.get("google_meet_link")
            db.commit()

            if meet_link:
                link_text = f"\n\n**Google Meet:** {meet_link}"
            else:
                link_text = ""

            return {
                "response": (
                    "Your meeting is **confirmed and booked**. ✅\n\n"
                    f"**Time:** {display}\n"
                    f"**Purpose:** {meeting_state.purpose or request.notes}"
                    f"{link_text}\n\n"
                    "A calendar invitation has also been sent to your email."
                )
            }

        flow.pending_field = "name"
        db.commit()
        return {"response": FIELD_PROMPTS["name"]}

    return process_meeting


def build_meeting_subgraph(db: Session, conversation_id: str):
    builder = StateGraph(ChatState)
    builder.add_node(
        "process_meeting",
        make_process_meeting_node(db, conversation_id),
    )
    builder.add_edge(START, "process_meeting")
    builder.add_edge("process_meeting", END)
    return builder.compile()
