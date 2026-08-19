from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import ConversationMessage
from app.graph import build_chat_graph


MAX_HISTORY_MESSAGES = 20


def process_chat(
    db: Session,
    message: str,
    conversation_id: str | None = None,
) -> tuple[str, str]:

    settings = get_settings()

    if not settings.groq_api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured in backend/.env"
        )

    conversation_id = conversation_id or str(uuid4())

    history_rows = (
        db.query(ConversationMessage)
        .filter(
            ConversationMessage.conversation_id
            == conversation_id
        )
        .order_by(ConversationMessage.id.desc())
        .limit(MAX_HISTORY_MESSAGES)
        .all()
    )

    history_rows.reverse()

    lc_messages = []

    for row in history_rows:
        if row.role == "user":
            lc_messages.append(
                HumanMessage(content=row.content)
            )
        elif row.role == "assistant":
            lc_messages.append(
                AIMessage(content=row.content)
            )

    db.add(
        ConversationMessage(
            conversation_id=conversation_id,
            role="user",
            content=message,
        )
    )
    db.commit()

    lc_messages.append(HumanMessage(content=message))

    graph = build_chat_graph(
        db=db,
        conversation_id=conversation_id,
    )

    result = graph.invoke(
        {
            "messages": lc_messages,
            "conversation_id": conversation_id,
        }
    )

    response_text = (
        result.get("response")
        or "I couldn't generate a response. Please try again."
    )

    db.add(
        ConversationMessage(
            conversation_id=conversation_id,
            role="assistant",
            content=response_text,
        )
    )
    db.commit()

    return response_text, conversation_id
