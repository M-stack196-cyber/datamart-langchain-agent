import re

from langchain_groq import ChatGroq
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.graph.state import ChatState, Intent


HANDOFF_RE = re.compile(
    r"\b("
    r"human|person|representative|agent|employee|staff|"
    r"talk to someone|speak to someone|live agent|"
    r"connect me|handoff"
    r")\b",
    re.IGNORECASE,
)

MEETING_RE = re.compile(
    r"\b("
    r"meeting|appointment|schedule|book a call|"
    r"book call|call with|available slot|availability"
    r")\b",
    re.IGNORECASE,
)

LEAD_RE = re.compile(
    r"\b("
    r"build|develop|create|project|website|app|software|"
    r"crm|automation|ai solution|hire|staff augmentation|"
    r"mvp|quote|proposal|budget|need a developer|"
    r"need an engineer|work with datamart"
    r")\b",
    re.IGNORECASE,
)


class IntentResult(BaseModel):
    intent: Intent


def _latest_user_text(state: ChatState) -> str:
    for message in reversed(state.get("messages", [])):
        if getattr(message, "type", "") == "human":
            return str(getattr(message, "content", "")).strip()
    return ""


def classify_intent(state: ChatState) -> dict:
    """
    Fast deterministic routing first, then LLM classification for ambiguous input.
    Keeping explicit routing in LangGraph makes the workflow inspectable and
    prevents every request from becoming an uncontrolled tool-selection loop.
    """
    text = _latest_user_text(state)

    if HANDOFF_RE.search(text):
        return {"intent": "handoff"}

    if MEETING_RE.search(text):
        return {"intent": "meeting"}

    if LEAD_RE.search(text):
        return {"intent": "lead"}

    settings = get_settings()

    # Safe fallback when no model key is present: knowledge/RAG is least destructive.
    if not settings.groq_api_key:
        return {"intent": "knowledge"}

    model = ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=0,
        timeout=30,
        max_retries=1,
    ).with_structured_output(IntentResult)

    result = model.invoke(
        [
            (
                "system",
                "Classify the visitor's latest Datamart chatbot message into exactly "
                "one intent: knowledge, lead, meeting, or handoff. "
                "Use lead for genuine project/service-buying enquiries. "
                "Use meeting for scheduling calls/appointments. "
                "Use handoff only for requests to speak with a human. "
                "Use knowledge for Datamart questions and general conversation.",
            ),
            ("human", text),
        ]
    )

    return {"intent": result.intent}


def route_by_intent(state: ChatState) -> str:
    return state.get("intent", "knowledge")
