# ============================================================
# MedFlow Referral Agent - Graph Definition
# Connects all nodes into a complete LangGraph workflow
# Defines the flow between nodes and conditional edges
# This is the orchestration layer of the entire agent
# ============================================================

import logging
from langgraph.graph import StateGraph, END
from src.agent.state import ReferralState
from src.agent.nodes.extraction import extraction_node
from src.agent.nodes.routing import routing_node
from src.agent.nodes.urgency import urgency_node
from src.agent.nodes.escalation import escalation_node
from src.agent.nodes.summary import summary_node

logger = logging.getLogger(__name__)


def should_continue_after_extraction(state: ReferralState) -> str:
    """
    Conditional edge after extraction node.
    If extraction failed completely — go to end.
    Otherwise continue to routing.
    """
    if state.get("error") and state.get("error_node") == "extraction":
        if not state.get("document_text"):
            logger.error(
                f"Extraction failed completely for {state['document_id']} "
                f"— ending workflow"
            )
            return "end"
    return "routing"


def should_continue_after_urgency(state: ReferralState) -> str:
    """
    Conditional edge after urgency node.
    Always continues to escalation check.
    Escalation node handles errors gracefully.
    """
    return "escalation"


def build_agent_graph() -> StateGraph:
    """
    Builds and compiles the complete LangGraph agent.

    Graph structure:
    extraction → routing → urgency → escalation → summary → END

    Conditional edges:
    - After extraction: if complete failure → END
                        otherwise → routing
    - After urgency: always → escalation

    Returns compiled graph ready for execution.
    """

    # ── Create graph with state type ─────────────────────────
    graph = StateGraph(ReferralState)

    # ── Add all nodes ─────────────────────────────────────────
    graph.add_node("extraction", extraction_node)
    graph.add_node("routing", routing_node)
    graph.add_node("urgency", urgency_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("summary", summary_node)

    # ── Set entry point ───────────────────────────────────────
    # Every document starts at extraction
    graph.set_entry_point("extraction")

    # ── Add conditional edge after extraction ─────────────────
    # If extraction completely fails — end workflow
    # Otherwise continue to routing
    graph.add_conditional_edges(
        "extraction",
        should_continue_after_extraction,
        {
            "routing": "routing",
            "end": END
        }
    )

    # ── Add normal edges ──────────────────────────────────────
    # routing always goes to urgency
    graph.add_edge("routing", "urgency")

    # urgency always goes to escalation
    graph.add_edge("urgency", "escalation")

    # escalation always goes to summary
    graph.add_edge("escalation", "summary")

    # summary always ends the workflow
    graph.add_edge("summary", END)

    # ── Compile the graph ─────────────────────────────────────
    compiled_graph = graph.compile()

    logger.info("Agent graph compiled successfully")

    return compiled_graph


# ── Create graph instance ─────────────────────────────────────
# Created once when module is imported
# Reused for every document processed
agent_graph = build_agent_graph()


async def process_referral(
    document_id: str,
    document_location: str,
    session_id: str
) -> ReferralState:
    """
    Main entry point for processing a referral document.
    Called by FastAPI when a new document arrives.

    Args:
        document_id: unique identifier for the referral
        document_location: GCS path to the PDF
        session_id: unique identifier for this processing run

    Returns:
        Final state after all nodes have executed
    """
    from datetime import datetime, timezone
    from src.agent.state import create_initial_state

    logger.info(f"Starting referral processing: {document_id}")

    # Create initial state
    initial_state = create_initial_state(
        document_id=document_id,
        document_location=document_location,
        session_id=session_id,
        processing_start_time=datetime.now(timezone.utc).isoformat()
    )

    # Run the graph
    final_state = await agent_graph.ainvoke(initial_state)

    # Record processing end time
    final_state["processing_end_time"] = datetime.now(
        timezone.utc
    ).isoformat()

    # Calculate processing time
    start = datetime.fromisoformat(final_state["processing_start_time"])
    end = datetime.fromisoformat(final_state["processing_end_time"])
    final_state["processing_time_seconds"] = (end - start).total_seconds()

    logger.info(
        f"Referral processing complete: {document_id} "
        f"in {final_state['processing_time_seconds']:.2f}s"
    )

    return final_state