import logging
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.graph.state import GameAssistantState
from app.agents.orchestrator import orchestrator_node
from app.agents.research_agent import research_agent_node
from app.agents.recommendation_agent import recommendation_agent_node
from app.agents.purchase_agent import purchase_agent_node
from app.graph.nodes import execute_purchase_node

logger = logging.getLogger(__name__)

def route_orchestrator(state: GameAssistantState) -> str:
    """Conditional routing from Orchestrator based on classified intent."""
    intent = state.get("intent", "RECOMMEND")
    logger.info(f"Routing orchestrator intent: {intent}")
    if intent == "PURCHASE":
        return "purchase_validation"
    return "research"

def route_after_purchase_validation(state: GameAssistantState) -> str:
    """Conditional edge: Only route to execute_purchase if purchase was actually requested and validated."""
    if state.get("purchase_requested") and state.get("purchase_summary"):
        return "execute_purchase"
    return END

def build_game_assistant_graph():
    """
    Constructs the LangGraph StateGraph with conditional edges,
    specialized specialist agent nodes, and human-in-the-loop checkpointed approval.
    """
    workflow = StateGraph(GameAssistantState)

    # 1. Add Nodes
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("research", research_agent_node)
    workflow.add_node("recommendation", recommendation_agent_node)
    workflow.add_node("purchase_validation", purchase_agent_node)
    workflow.add_node("execute_purchase", execute_purchase_node)

    # 2. Add Edges
    workflow.add_edge(START, "orchestrator")

    # Routing from Orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        route_orchestrator,
        {
            "research": "research",
            "purchase_validation": "purchase_validation",
        },
    )

    # Research -> Recommendation -> END
    workflow.add_edge("research", "recommendation")
    workflow.add_edge("recommendation", END)

    # Purchase Validation -> (Human Approval Interrupt) -> Execute Purchase -> END
    workflow.add_conditional_edges(
        "purchase_validation",
        route_after_purchase_validation,
        {
            "execute_purchase": "execute_purchase",
            END: END,
        },
    )
    workflow.add_edge("execute_purchase", END)

    # 3. Checkpointer & Interrupt Before execution for strict HITL approval
    checkpointer = MemorySaver()
    compiled_app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["execute_purchase"]
    )

    return compiled_app

# Singleton instance of compiled graph
assistant_graph = build_game_assistant_graph()
