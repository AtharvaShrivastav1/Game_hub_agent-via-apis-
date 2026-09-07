import logging
from typing import Dict, Any, List
from app.graph.state import GameAssistantState
from app.tools.game_tools import (
    search_games,
    get_game,
    get_user_library,
    get_user_cart,
    get_user_wallet,
    semantic_search_games,
)

logger = logging.getLogger(__name__)

def research_agent_node(state: GameAssistantState) -> Dict[str, Any]:
    """LangGraph node: Research Agent executing controlled tools to gather factual game data.

    Uses dual retrieval strategy:
    1. SQL structured search (precise genre/price/rating/duration filters)
    2. ChromaDB semantic search (captures meaning and conceptual similarity)
    Results are merged and deduplicated for a richer candidate pool.
    """
    user_id = state.get("user_id", 1)
    reqs = state.get("requirements", {})
    current_game_id = state.get("current_game_id")
    message = state.get("message", "")
    steps = list(state.get("agent_steps", []))

    # 1. Retrieve user's existing library and wallet
    user_library = get_user_library(user_id)
    wallet_info = get_user_wallet(user_id)
    cart_info = get_user_cart(user_id)
    owned_ids = {item["game_id"] for item in user_library}

    # 2. Retrieve candidates based on structured criteria (SQL)
    genre = reqs.get("genre")
    genres = reqs.get("genres", [])
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

    # --- SQL Structured Search (precise filters with multi-genre & float tolerance support) ---
    genres_to_search = genres if genres else ([genre] if genre else [None])
    # Database single-precision 32-bit float tolerance (e.g. 4.6 stored as 4.5999999)
    adjusted_min_rating = max(0.0, min_rating - 0.05) if min_rating is not None else None

    search_results = []
    for g_filter in genres_to_search:
        results = search_games(
            genre=g_filter,
            max_price=max_price,
            max_duration=max_duration,
            min_rating=adjusted_min_rating,
            search=query,
            limit=12,
        )
        search_results.extend(results)

    # Add SQL search results (avoid duplicates)
    seen_ids = {c["id"] for c in candidates}
    sql_count = 0
    for g in search_results:
        if g["id"] not in seen_ids:
            g["is_owned"] = g["id"] in owned_ids
            g["source"] = "sql"
            candidates.append(g)
            seen_ids.add(g["id"])
            sql_count += 1

    # --- ChromaDB Semantic Search (captures meaning without rigid genre restrictions) ---
    semantic_query = message or query or ""
    semantic_count = 0
    if semantic_query:
        semantic_results = semantic_search_games(
            query=semantic_query,
            limit=8,
            genre=None,  # Do not restrict semantic search by rigid genre string
            max_price=max_price,
        )
        for g in semantic_results:
            if g["id"] not in seen_ids:
                g["is_owned"] = g["id"] in owned_ids
                candidates.append(g)
                seen_ids.add(g["id"])
                semantic_count += 1

    steps.append({
        "agent_name": "Research Agent",
        "action": f"Retrieved {len(candidates)} candidate games (SQL: {sql_count}, Semantic: {semantic_count})",
        "details": f"Wallet: ₹{wallet_info.get('wallet_balance', 0):.2f}, Owned Games: {len(owned_ids)}"
    })

    return {
        "candidate_games": candidates,
        "user_library": user_library,
        "wallet_info": wallet_info,
        "cart_items": cart_info.get("items", []),
        "agent_steps": steps,
    }

