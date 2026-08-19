from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from app.agent.service import build_datamart_agent
from app.graph.state import ChatState


BRANCH_GUIDANCE = {
    "knowledge": (
        "Handle this as a Datamart knowledge question. Use the verified knowledge "
        "search tool whenever company-specific facts are required. Do not invent facts."
    ),
    "lead": (
        "Handle this as a project/lead enquiry. Preserve any details the visitor "
        "already provided, save useful lead details with the lead tool, and ask only "
        "for genuinely missing information needed to continue."
    ),
    "meeting": (
        "Handle this as a meeting request. Use the meeting-request tool only when "
        "its required information is available. Never claim a calendar slot is "
        "confirmed because the current Phase 1 tool only stores a request."
    ),
    "handoff": (
        "Handle this as a request for human assistance. Use the handoff tool and "
        "clearly tell the visitor that the request has been registered."
    ),
}


def _extract_text(message) -> str:
    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                text = block.get("text") or block.get("content")
                if text:
                    text_parts.append(str(text))
        return "\n".join(text_parts).strip()

    return str(content).strip()


def make_branch_node(db: Session, conversation_id: str, branch: str):
    def run_branch(state: ChatState) -> dict:
        agent = build_datamart_agent(
            db=db,
            conversation_id=conversation_id,
        )

        messages = list(state.get("messages", []))
        guidance = BRANCH_GUIDANCE[branch]

        # The graph decides the business branch. The existing LangChain agent
        # performs tool-calling inside that branch.
        messages_for_agent = [
            HumanMessage(
                content=(
                    f"[Internal workflow instruction: {guidance}]\n\n"
                    "Respond to the visitor based on the conversation below."
                )
            ),
            *messages,
        ]

        result = agent.invoke({"messages": messages_for_agent})
        final_message = result["messages"][-1]

        response = (
            _extract_text(final_message)
            or "I couldn't generate a response. Please try again."
        )

        return {"response": response}

    return run_branch
