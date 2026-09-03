import logging
from typing import Dict, Any, List
from app.graph.state import GameAssistantState
from app.tools.game_tools import (
    search_games,
    get_game,
    get_user_library,
    get_user_cart,
    get_user_wallet,
)

logger = logging.getLogger(__name__)

def research_agent_node(state: GameAssistantState) -> Dict[str, Any]:
    """LangGraph node: Research Agent executing controlled tools to gather factual game data."""
    user_id = state.get("user_id", 1)
    reqs = state.get("requirements", {})
    current_game_id = state.get("current_game_id")
    steps = list(state.get("agent_steps", []))

    # 1. Retrieve user's existing library and wallet
    user_library = get_user_library(user_id)
    wallet_info = get_user_wallet(user_id)
    cart_info = get_user_cart(user_id)
    owned_ids = {item["game_id"] for item in user_library}

    # 2. Retrieve candidates based on criteria
    genre = reqs.get("genre")
    max_price = reqs.get("max_price")
    max_duration = reqs.get("max_duration")
    min_rating = reqs.get("min_rating")
    query = reqs.get("search_query")

    candidates: List[Dict[str, Any]] = []

    # If user asks about a specific currently viewed game
    current_game_data = None
    if current_game_id:
        current_game_data = get_game(current_game_id)
        if current_game_data:
            current_game_data["is_owned"] = current_game_id in owned_ids
            candidates.append(current_game_data)

    # Perform catalog search
    search_results = search_games(
        genre=genre,
        max_price=max_price,
        max_duration=max_duration,
        min_rating=min_rating,
        search=query,
        limit=12,
    )

    # Add search results (avoid duplicates)
    seen_ids = {c["id"] for c in candidates}
    for g in search_results:
        if g["id"] not in seen_ids:
            g["is_owned"] = g["id"] in owned_ids
            candidates.append(g)
            seen_ids.add(g["id"])

    steps.append({
        "agent_name": "Research Agent",
        "action": f"Retrieved {len(candidates)} candidate games from MySQL catalog",
        "details": f"Wallet: ₹{wallet_info.get('wallet_balance', 0):.2f}, Owned Games: {len(owned_ids)}"
    })

    return {
        "candidate_games": candidates,
        "user_library": user_library,
        "wallet_info": wallet_info,
        "cart_items": cart_info.get("items", []),
        "agent_steps": steps,
    }
