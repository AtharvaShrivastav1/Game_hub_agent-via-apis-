import logging
from typing import Dict, Any, List
from app.graph.state import GameAssistantState
from app.tools.game_tools import (
    search_games,
    get_game,
    get_user_cart,
    get_user_library,
    get_user_wallet,
    validate_purchase,
)

logger = logging.getLogger(__name__)

def purchase_agent_node(state: GameAssistantState) -> Dict[str, Any]:
    """
    LangGraph node: Purchase / Validation Agent.
    Identifies target games (from cart, current_game_id, or title query),
    validates pre-conditions, and prepares the purchase summary for the human-in-the-loop gate.
    """
    user_id = state.get("user_id", 1)
    message = state.get("message", "").lower()
    current_game_id = state.get("current_game_id")
    steps = list(state.get("agent_steps", []))

    game_ids_to_buy: List[int] = []

    # Case 1: User wants to buy cart items ("buy everything in my cart", "checkout cart", "buy cart")
    if "cart" in message or "everything" in message or "all" in message:
        cart_info = get_user_cart(user_id)
        game_ids_to_buy = [item["game_id"] for item in cart_info.get("items", [])]
        if not game_ids_to_buy:
            return {
                "final_response": "Your cart is currently empty. Add some games to your cart before proceeding to purchase!",
                "purchase_requested": False,
                "agent_steps": steps + [{
                    "agent_name": "Purchase Agent",
                    "action": "Validated purchase request",
                    "details": "Cart was empty, aborted purchase workflow."
                }],
            }

    # Case 2: User says "buy this" while viewing a game
    elif ("this" in message or not state.get("requirements", {}).get("search_query")) and current_game_id:
        game_ids_to_buy = [current_game_id]

    # Case 3: User mentions a game title explicitly (e.g. "Buy Witcher 3", "Buy Hades")
    else:
        import re
        # Extract title from message or requirements
        query = state.get("requirements", {}).get("search_query") or state.get("message", "")
        # Case-insensitive removal of action prefixes
        clean_query = re.sub(r'(?i)\b(?:buy|purchase|get|order|checkout)\b', '', query).strip()
        # Also strip leading punctuation or whitespace
        clean_query = re.sub(r'^[^\w]+', '', clean_query).strip()

        matched = []
        if clean_query:
            matched = search_games(search=clean_query, limit=3)
            # If no direct match with full phrase, try first 2 significant words
            if not matched:
                words = [w for w in clean_query.split() if len(w) > 2]
                if words:
                    matched = search_games(search=" ".join(words[:2]), limit=3)

        if matched:
            game_ids_to_buy = [matched[0]["id"]]
        elif current_game_id:
            game_ids_to_buy = [current_game_id]

    if not game_ids_to_buy:
        return {
            "final_response": "I could not identify which game you would like to purchase. Please specify a game title or say 'Buy everything in my cart'.",
            "purchase_requested": False,
            "agent_steps": steps + [{
                "agent_name": "Purchase Agent",
                "action": "Game identification failed",
                "details": "No matching game could be resolved from request."
            }],
        }

    # Validate purchase via controlled tool
    val = validate_purchase(user_id, game_ids_to_buy)

    if not val.get("valid"):
        error_msg = val.get("error", "Purchase validation failed.")
        return {
            "final_response": f"Purchase Validation Notice: {error_msg}",
            "purchase_requested": False,
            "error": error_msg,
            "agent_steps": steps + [{
                "agent_name": "Purchase Agent",
                "action": "Purchase pre-validation failed",
                "details": error_msg
            }],
        }

    # Validation succeeded: Prepare purchase summary for human confirmation
    summary = {
        "game_ids": val["game_ids"],
        "game_titles": val["game_titles"],
        "total_price": val["total_price"],
        "current_wallet_balance": val["current_wallet_balance"],
        "remaining_balance": val["remaining_balance"],
        "can_afford": val["can_afford"],
        "requires_approval": True,
    }

    titles_str = ", ".join(val["game_titles"])
    response_msg = (
        f"### 🛒 Purchase Confirmation Required\n\n"
        f"You are about to purchase: **{titles_str}**\n\n"
        f"- **Total Price:** ₹{val['total_price']:.2f}\n"
        f"- **Current Wallet Balance:** ₹{val['current_wallet_balance']:.2f}\n"
        f"- **Remaining Balance:** ₹{val['remaining_balance']:.2f}\n\n"
        f"Do you want to proceed with this purchase? Please review and confirm below."
    )

    steps.append({
        "agent_name": "Purchase Agent",
        "action": "Validated purchase conditions and prepared approval summary",
        "details": f"Games: {titles_str} | Total: ₹{val['total_price']:.2f} | Affordable: {val['can_afford']}"
    })

    return {
        "purchase_requested": True,
        "purchase_approved": False,
        "purchase_summary": summary,
        "final_response": response_msg,
        "agent_steps": steps,
    }
