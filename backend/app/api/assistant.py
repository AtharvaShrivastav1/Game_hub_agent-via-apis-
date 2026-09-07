import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.schemas.assistant import ChatRequest, ChatResponse, AgentStepLog
from app.schemas.purchase import PurchaseApprovalRequest
from app.graph.workflow import assistant_graph
from app.services.llm_factory import stringify_content


logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["AI Assistant & HITL"])

@router.post("/assistant/chat", response_model=ChatResponse)
def chat_with_assistant(payload: ChatRequest):
    """
    Main AI Assistant endpoint orchestrating LangGraph multi-agent flow.
    Supports contextual game queries, recommendations, budget reasoning, and HITL purchase triggers.
    """
    thread_id = payload.thread_id or f"user_{payload.user_id}_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}

    # Retrieve previous conversation context from graph checkpointer or client payload
    existing_state = assistant_graph.get_state(config)
    context_bucket: List[Dict[str, Any]] = []
    if existing_state and existing_state.values and existing_state.values.get("context_bucket"):
        context_bucket = list(existing_state.values.get("context_bucket", []))
    elif payload.chat_history:
        for item in payload.chat_history:
            role = item.get("role") or item.get("sender") or "user"
            content = item.get("content") or item.get("text") or ""
            if content:
                context_bucket.append({
                    "role": role,
                    "content": content,
                    "recommended_games": item.get("recommended_games", []),
                    "recommended_titles": [g.get("title") for g in item.get("recommended_games", []) if isinstance(g, dict) and g.get("title")],
                })

    # Append current incoming user message
    context_bucket.append({"role": "user", "content": payload.message})

    initial_state = {
        "user_id": payload.user_id,
        "message": payload.message,
        "current_game_id": payload.current_game_id,
        "thread_id": thread_id,
        "purchase_approved": False,
        "purchase_requested": False,
        "context_bucket": context_bucket,
        "agent_steps": [],
    }

    try:
        # Run graph until completion or interrupt
        result = assistant_graph.invoke(initial_state, config=config)

        # Inspect if graph paused at the human approval gate (interrupt before execute_purchase)
        current_state = assistant_graph.get_state(config)
        is_interrupted = "execute_purchase" in (current_state.next or ())

        requires_approval = is_interrupted and bool(result.get("purchase_requested"))
        approval_data = result.get("purchase_summary") if requires_approval else None

        final_response_str = stringify_content(result.get("final_response", "I have processed your request."))
        recs = result.get("recommendations", [])

        # Update context bucket with assistant response and recommended entities
        context_bucket.append({
            "role": "assistant",
            "content": final_response_str,
            "recommended_games": recs,
            "recommended_titles": [g.get("title") for g in recs if isinstance(g, dict) and g.get("title")],
        })
        assistant_graph.update_state(config, {"context_bucket": context_bucket})

        steps = [
            AgentStepLog(agent_name=s.get("agent_name", "Agent"), action=s.get("action", ""), details=s.get("details"))
            for s in result.get("agent_steps", [])
        ]

        return ChatResponse(
            thread_id=thread_id,
            intent=result.get("intent"),
            response=final_response_str,
            requires_approval=requires_approval,
            approval_data=approval_data,
            agent_steps=steps,
            recommended_games=recs,
            cart_items=result.get("cart_items", []),
            transaction_result=result.get("transaction_result"),
            context_summary={
                "total_turns": len(context_bucket),
                "active_thread": thread_id,
                "cached_recommendations": len(recs),
            },
        )

    except Exception as e:
        logger.error(f"Error in assistant chat: {e}", exc_info=True)
        return ChatResponse(
            thread_id=thread_id,
            intent="ERROR",
            response=f"I encountered a temporary issue while processing your request: {str(e)}. Please try again.",
            requires_approval=False,
            agent_steps=[AgentStepLog(agent_name="System", action="Error Recovery", details=str(e))],
        )

@router.post("/purchase/approve", response_model=ChatResponse)
def approve_purchase(payload: PurchaseApprovalRequest):
    """
    Human-in-the-loop approval endpoint:
    Resumes the interrupted LangGraph thread with purchase_approved = True,
    triggering the atomic MySQL transaction tool.
    """
    config = {"configurable": {"thread_id": payload.thread_id}}

    # Verify thread exists in checkpointer
    current_state = assistant_graph.get_state(config)
    if not current_state.values:
        raise HTTPException(status_code=404, detail="No active purchase session found for this thread ID.")

    if not payload.approved:
        raise HTTPException(status_code=400, detail="Use /purchase/reject to reject a purchase.")

    try:
        # Update graph state with human approval
        assistant_graph.update_state(config, {"purchase_approved": True})

        # Resume graph execution to run execute_purchase_node
        result = assistant_graph.invoke(None, config=config)

        steps = [
            AgentStepLog(agent_name=s.get("agent_name", "Agent"), action=s.get("action", ""), details=s.get("details"))
            for s in result.get("agent_steps", [])
        ]

        return ChatResponse(
            thread_id=payload.thread_id,
            intent="PURCHASE",
            response=stringify_content(result.get("final_response", "Purchase executed successfully!")),
            requires_approval=False,
            approval_data=None,
            agent_steps=steps,
            transaction_result=result.get("transaction_result"),
        )
    except Exception as e:
        logger.error(f"Error in purchase approval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transaction failed: {str(e)}")

@router.post("/purchase/reject", response_model=ChatResponse)
def reject_purchase(payload: PurchaseApprovalRequest):
    """
    Human-in-the-loop rejection endpoint:
    Resumes or cancels the LangGraph thread with purchase_approved = False,
    aborting without touching the database.
    """
    config = {"configurable": {"thread_id": payload.thread_id}}

    current_state = assistant_graph.get_state(config)
    if not current_state.values:
        raise HTTPException(status_code=404, detail="No active purchase session found for this thread ID.")

    try:
        assistant_graph.update_state(config, {"purchase_approved": False})
        result = assistant_graph.invoke(None, config=config)

        steps = [
            AgentStepLog(agent_name=s.get("agent_name", "Agent"), action=s.get("action", ""), details=s.get("details"))
            for s in result.get("agent_steps", [])
        ]

        return ChatResponse(
            thread_id=payload.thread_id,
            intent="PURCHASE",
            response=stringify_content(result.get("final_response", "Purchase cancelled. No changes were made.")),
            requires_approval=False,
            approval_data=None,
            agent_steps=steps,
            transaction_result={"success": False, "cancelled": True},
        )

    except Exception as e:
        logger.error(f"Error in purchase rejection: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Rejection processing failed: {str(e)}")
