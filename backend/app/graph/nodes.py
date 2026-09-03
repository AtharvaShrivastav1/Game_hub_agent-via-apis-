import logging
from typing import Dict, Any
from app.graph.state import GameAssistantState
from app.agents.orchestrator import orchestrator_node
from app.agents.research_agent import research_agent_node
from app.agents.recommendation_agent import recommendation_agent_node
from app.agents.purchase_agent import purchase_agent_node
from app.tools.game_tools import purchase_game, get_user_wallet

logger = logging.getLogger(__name__)

def execute_purchase_node(state: GameAssistantState) -> Dict[str, Any]:
    """
    LangGraph node: Executes the atomic purchase transaction in MySQL
    ONLY after human approval has been verified in the state.
    """
    user_id = state.get("user_id", 1)
    approved = state.get("purchase_approved", False)
    summary = state.get("purchase_summary") or {}
    game_ids = summary.get("game_ids", [])
    steps = list(state.get("agent_steps", []))

    if not approved:
        steps.append({
            "agent_name": "Purchase Execution Agent",
            "action": "Purchase transaction aborted",
            "details": "User rejected the purchase confirmation."
        })
        return {
            "final_response": "Purchase cancelled. No changes have been made to your wallet or cart.",
            "transaction_result": {"success": False, "cancelled": True},
            "agent_steps": steps,
        }

    # Execute purchase using atomic tool
    result = purchase_game(user_id, game_ids)
    new_wallet = get_user_wallet(user_id)

    if result.get("success"):
        titles_str = ", ".join(summary.get("game_titles", []))
        final_msg = (
            f"🎉 **Purchase Complete!**\n\n"
            f"Successfully purchased **{titles_str}**.\n"
            f"- **Amount Deducted:** ₹{summary.get('total_price', 0):.2f}\n"
            f"- **New Wallet Balance:** ₹{new_wallet.get('wallet_balance', 0):.2f}\n\n"
            f"The game(s) have been added to your **My Library** and removed from your cart. Enjoy your playtime!"
        )
        steps.append({
            "agent_name": "Purchase Execution Agent",
            "action": "Committed atomic MySQL purchase transaction",
            "details": f"Deducted ₹{summary.get('total_price', 0):.2f}, Added to user {user_id}'s library."
        })
    else:
        final_msg = f"❌ **Transaction Failed:** {result.get('error', 'An unexpected database error occurred.')}"
        steps.append({
            "agent_name": "Purchase Execution Agent",
            "action": "Purchase transaction failed and rolled back",
            "details": result.get("error", "Unknown error")
        })

    return {
        "transaction_result": result,
        "wallet_info": new_wallet,
        "final_response": final_msg,
        "agent_steps": steps,
    }
