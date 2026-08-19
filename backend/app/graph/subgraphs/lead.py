import re
from decimal import Decimal, InvalidOperation

from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ConversationFlowState, Lead
from app.graph.state import ChatState
from app.rag.vectorstore import get_retriever


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'\-]{1,148}$")

OPTIONAL_FIELDS = {"phone", "budget", "timeline", "company"}

FIELD_ORDER = [
    "name",
    "email",
    "phone",
    "project_description",
    "budget",
    "timeline",
    "company",
]

FIELD_PROMPTS = {
    "name": "What is your **full name**?",
    "email": "What is your **email address**?",
    "phone": (
        "What is your **phone number**? This is optional — you can say **skip**."
    ),
    "project_description": (
        "Please briefly describe the **project or automation you want to build**."
    ),
    "budget": (
        "What **budget range** do you have in mind? "
        "This is optional — you can say **skip**."
    ),
    "timeline": (
        "What is your preferred **timeline**? "
        "This is optional — you can say **skip**."
    ),
    "company": (
        "What is your **company name**? "
        "This is optional — you can say **skip**."
    ),
}

SKIP_WORDS = {
    "skip",
    "pass",
    "no",
    "none",
    "not now",
    "not sure",
    "dont know",
    "don't know",
    "not decided",
    "flexible",
    "later",
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
            active_flow="lead",
            mode="bot",
        )
        db.add(flow)
        db.flush()
    return flow


def _get_lead(db: Session, conversation_id: str) -> Lead:
    lead = (
        db.query(Lead)
        .filter(Lead.conversation_id == conversation_id)
        .order_by(Lead.id.desc())
        .first()
    )
    if not lead:
        lead = Lead(conversation_id=conversation_id)
        db.add(lead)
        db.flush()
    return lead


def _skipped(flow: ConversationFlowState) -> set[str]:
    return {x for x in (flow.skipped_fields or "").split(",") if x}


def _mark_skipped(flow: ConversationFlowState, field: str) -> None:
    values = _skipped(flow)
    values.add(field)
    flow.skipped_fields = ",".join(sorted(values))


def _next_field(lead: Lead, flow: ConversationFlowState) -> str | None:
    skipped = _skipped(flow)

    for field in FIELD_ORDER:
        if field in skipped:
            continue

        value = getattr(lead, field, None)

        if value is None or not str(value).strip():
            return field

    return None


def _looks_like_question(text: str) -> bool:
    lowered = text.strip().lower()

    if lowered.endswith("?"):
        return True

    starters = (
        "what ",
        "why ",
        "how ",
        "which ",
        "who ",
        "where ",
        "when ",
        "can ",
        "could ",
        "do ",
        "does ",
        "is ",
        "are ",
        "tell me ",
        "explain ",
    )
    return lowered.startswith(starters)


def _normalize_phone(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    if 7 <= len(digits) <= 15:
        prefix = "+" if value.strip().startswith("+") else ""
        return prefix + digits
    return None


def _normalize_budget(value: str) -> str:
    raw = value.strip()
    lowered = raw.lower().replace(",", "")

    match = re.search(
        r"\$?\s*(\d+(?:\.\d+)?)\s*(k|thousand|m|million|b|billion)?",
        lowered,
    )
    if not match:
        return raw

    try:
        number = Decimal(match.group(1))
    except InvalidOperation:
        return raw

    suffix = match.group(2)
    multiplier = Decimal("1")

    if suffix in {"k", "thousand"}:
        multiplier = Decimal("1000")
    elif suffix in {"m", "million"}:
        multiplier = Decimal("1000000")
    elif suffix in {"b", "billion"}:
        multiplier = Decimal("1000000000")

    total = number * multiplier

    if total == total.to_integral_value():
        formatted = f"${int(total):,}"
    else:
        formatted = f"${total:,.2f}"

    if any(word in lowered for word in ("around", "about", "approx", "approximately")):
        return f"Approximately {formatted}"

    return formatted


def _normalize_timeline(value: str) -> str:
    text = value.strip()
    lowered = text.lower()

    replacements = {
        "asap": "As soon as possible",
        "as soon as possible": "As soon as possible",
        "next month": "Next month",
        "next quarter": "Next quarter",
        "this quarter": "This quarter",
        "this year": "This year",
    }

    if lowered in replacements:
        return replacements[lowered]

    return text


def _validate_and_store(
    lead: Lead,
    flow: ConversationFlowState,
    field: str,
    value: str,
) -> tuple[bool, str | None]:
    cleaned = value.strip()
    lowered = cleaned.lower()

    if lowered in SKIP_WORDS:
        if field in OPTIONAL_FIELDS:
            _mark_skipped(flow, field)
            return True, None

        return False, f"{FIELD_PROMPTS[field]} This field is required."

    if field == "name":
        if len(cleaned.split()) < 2 or not NAME_RE.match(cleaned):
            return False, (
                "Please enter your **full name** (for example, `John Smith`)."
            )
        lead.name = cleaned
        return True, None

    if field == "email":
        email = cleaned.lower()
        if not EMAIL_RE.match(email):
            return False, "Please enter a **valid email address**."
        lead.email = email
        return True, None

    if field == "phone":
        phone = _normalize_phone(cleaned)
        if not phone:
            return False, (
                "That phone number does not look valid. "
                "Please enter 7–15 digits, or say **skip**."
            )
        lead.phone = phone
        return True, None

    if field == "project_description":
        if len(cleaned) < 10:
            return False, (
                "Please give me a little more detail about the project "
                "(at least a short sentence)."
            )
        lead.project_description = cleaned
        return True, None

    if field == "budget":
        lead.budget = _normalize_budget(cleaned)
        return True, None

    if field == "timeline":
        lead.timeline = _normalize_timeline(cleaned)
        return True, None

    if field == "company":
        if len(cleaned) < 2:
            return False, "Please enter a company name, or say **skip**."
        lead.company = cleaned
        return True, None

    return False, "I couldn't process that field. Please try again."


def _answer_interruption(question: str) -> str:
    settings = get_settings()

    try:
        docs = get_retriever(k=4).invoke(question)
    except Exception:
        docs = []

    context = "\n\n".join(
        str(doc.page_content)
        for doc in docs
        if getattr(doc, "page_content", None)
    )

    if not settings.groq_api_key:
        return (
            "I can continue the project enquiry, but I couldn't answer that "
            "knowledge question right now."
        )

    model = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        timeout=30,
        max_retries=1,
    )

    response = model.invoke(
        [
            (
                "system",
                "You are Datamart's assistant. Answer only the visitor's question. "
                "Use the supplied verified Datamart context when it is relevant. "
                "Do not invent company facts. If the context does not contain the "
                "answer, say that you do not have verified information.",
            ),
            (
                "human",
                f"Question:\n{question}\n\nVerified Datamart context:\n{context}",
            ),
        ]
    )

    return str(getattr(response, "content", response)).strip()


def make_process_lead_node(db: Session, conversation_id: str):
    def process_lead(state: ChatState) -> dict:
        text = _latest_user_text(state)
        flow = _get_flow(db, conversation_id)
        lead = _get_lead(db, conversation_id)

        # First turn in a new lead flow: preserve the user's project enquiry as
        # project description when it is already meaningful, then ask one field.
        just_started = flow.active_flow != "lead" or not flow.pending_field

        flow.active_flow = "lead"

        if just_started and not lead.project_description and len(text) >= 10:
            lead.project_description = text

        pending = flow.pending_field

        if pending and _looks_like_question(text):
            answer = _answer_interruption(text)
            db.commit()
            return {
                "response": (
                    f"{answer}\n\n"
                    f"To continue your project enquiry: {FIELD_PROMPTS[pending]}"
                )
            }

        if pending:
            ok, error = _validate_and_store(
                lead=lead,
                flow=flow,
                field=pending,
                value=text,
            )

            if not ok:
                db.commit()
                return {"response": error or FIELD_PROMPTS[pending]}

        next_field = _next_field(lead, flow)

        if next_field:
            flow.pending_field = next_field
            db.commit()
            return {"response": FIELD_PROMPTS[next_field]}

        flow.pending_field = None
        flow.active_flow = None
        lead.status = lead.status or "new"
        db.commit()

        summary_parts = [
            f"**Name:** {lead.name}",
            f"**Email:** {lead.email}",
            f"**Project:** {lead.project_description}",
        ]

        if lead.phone:
            summary_parts.append(f"**Phone:** {lead.phone}")
        if lead.company:
            summary_parts.append(f"**Company:** {lead.company}")
        if lead.budget:
            summary_parts.append(f"**Budget:** {lead.budget}")
        if lead.timeline:
            summary_parts.append(f"**Timeline:** {lead.timeline}")

        return {
            "response": (
                "Thanks — your project enquiry has been saved successfully.\n\n"
                + "\n".join(summary_parts)
                + "\n\nA member of the Datamart team can now follow up with you."
            )
        }

    return process_lead


def build_lead_subgraph(db: Session, conversation_id: str):
    builder = StateGraph(ChatState)
    builder.add_node(
        "process_lead",
        make_process_lead_node(db, conversation_id),
    )
    builder.add_edge(START, "process_lead")
    builder.add_edge("process_lead", END)
    return builder.compile()
