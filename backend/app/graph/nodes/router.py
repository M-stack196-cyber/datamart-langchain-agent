import re

from langchain_groq import ChatGroq
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ConversationFlowState
from app.graph.state import ChatState, Intent


HANDOFF_RE = re.compile(
    r"\b("
    r"human|person|representative|employee|staff|"
    r"talk to someone|speak to someone|live agent|"
    r"connect me|human agent|handoff"
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


def make_classify_intent_node(db: Session, conversation_id: str):
    def classify_intent(state: ChatState) -> dict:
        """
        Explicit handoff/meeting intent is handled first.

        Then unfinished lead/meeting flows stay sticky so short replies such as a
        name, timezone or slot number continue through the correct subgraph.
        """
        text = _latest_user_text(state)

        if HANDOFF_RE.search(text):
            return {"intent": "handoff"}

        if MEETING_RE.search(text):
            return {"intent": "meeting"}

        flow_state = (
            db.query(ConversationFlowState)
            .filter(ConversationFlowState.conversation_id == conversation_id)
            .first()
        )

        if flow_state and flow_state.active_flow in {"lead", "meeting"}:
            return {"intent": flow_state.active_flow}

        if LEAD_RE.search(text):
            return {"intent": "lead"}

        settings = get_settings()

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

    return classify_intent


def route_by_intent(state: ChatState) -> str:
    return state.get("intent", "knowledge")
