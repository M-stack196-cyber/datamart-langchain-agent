from sqlalchemy.orm import Session
from langgraph.graph import END, START, StateGraph

from app.graph.nodes.branches import make_branch_node
from app.graph.nodes.router import make_classify_intent_node, route_by_intent
from app.graph.state import ChatState
from app.graph.subgraphs.handoff import build_handoff_subgraph
from app.graph.subgraphs.lead import build_lead_subgraph
from app.graph.subgraphs.meeting import build_meeting_subgraph


def build_chat_graph(db: Session, conversation_id: str):
    """
    Central LangGraph orchestrator.

    START
      -> classify_intent
      -> knowledge | lead | meeting | handoff
      -> END
    """
    builder = StateGraph(ChatState)

    builder.add_node(
        "classify_intent",
        make_classify_intent_node(db, conversation_id),
    )
    builder.add_node(
        "knowledge",
        make_branch_node(db, conversation_id, "knowledge"),
    )
    builder.add_node(
        "lead",
        build_lead_subgraph(db, conversation_id),
    )
    builder.add_node(
        "meeting",
        build_meeting_subgraph(db, conversation_id),
    )
    builder.add_node(
        "handoff",
        build_handoff_subgraph(db, conversation_id),
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
