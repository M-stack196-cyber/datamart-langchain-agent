from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy.orm import Session

from app.agent.service import build_datamart_agent
from app.config import get_settings
from app.db.models import ConversationMessage


MAX_HISTORY_MESSAGES = 20


def _extract_text(message) -> str:
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts: list[str] = []

        for block in content:
            if isinstance(block, str):
                text_parts.append(block)

            elif isinstance(block, dict) and block.get("type") in {
                "text",
                "output_text",
            }:
                text = block.get("text") or block.get("content")

                if text:
                    text_parts.append(str(text))

        return "\n".join(text_parts).strip()

    return str(content)


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

    lc_messages.append(
        HumanMessage(content=message)
    )

    agent = build_datamart_agent(
        db=db,
        conversation_id=conversation_id,
    )

    result = agent.invoke(
        {
            "messages": lc_messages
        }
    )

    final_message = result["messages"][-1]

    response_text = (
        _extract_text(final_message)
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