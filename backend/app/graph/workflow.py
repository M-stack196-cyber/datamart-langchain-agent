from sqlalchemy.orm import Session
from langgraph.graph import END, START, StateGraph

from app.graph.nodes.branches import make_branch_node
from app.graph.nodes.router import classify_intent, route_by_intent
from app.graph.state import ChatState


def build_chat_graph(db: Session, conversation_id: str):
    """
    Phase 1 central LangGraph orchestrator.

    START
      -> classify_intent
      -> knowledge | lead | meeting | handoff
      -> END

    Later phases can replace each branch node with a full subgraph without
    changing the public /api/chat contract.
    """
    builder = StateGraph(ChatState)

    builder.add_node("classify_intent", classify_intent)
    builder.add_node(
        "knowledge",
        make_branch_node(db, conversation_id, "knowledge"),
    )
    builder.add_node(
        "lead",
        make_branch_node(db, conversation_id, "lead"),
    )
    builder.add_node(
        "meeting",
        make_branch_node(db, conversation_id, "meeting"),
    )
    builder.add_node(
        "handoff",
        make_branch_node(db, conversation_id, "handoff"),
    )

    builder.add_edge(START, "classify_intent")

    builder.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "knowledge": "knowledge",
            "lead": "lead",
            "meeting": "meeting",
            "handoff": "handoff",
        },
    )

    builder.add_edge("knowledge", END)
    builder.add_edge("lead", END)
    builder.add_edge("meeting", END)
    builder.add_edge("handoff", END)

    return builder.compile()
