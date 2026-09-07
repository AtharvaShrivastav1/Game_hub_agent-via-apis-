from typing import TypedDict, Optional, List, Dict, Any

class GameAssistantState(TypedDict, total=False):
    # User context
    user_id: int
    message: str
    current_game_id: Optional[int]
    thread_id: Optional[str]

    # Orchestrator outputs
    intent: str  # SEARCH, RECOMMEND, COMPARE, CART_QUERY, CART_MODIFICATION, PURCHASE, GENERAL_GAME_QUERY
    requirements: Dict[str, Any]  # genre, budget, max_duration, min_rating, query, target_game_titles

    # Specialist Agent data
    candidate_games: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]]
    cart_items: List[Dict[str, Any]]
    user_library: List[Dict[str, Any]]
    wallet_info: Optional[Dict[str, Any]]

    # Purchase workflow & HITL
    selected_games: List[Dict[str, Any]]
    purchase_requested: bool
    purchase_approved: bool
    purchase_summary: Optional[Dict[str, Any]]
    transaction_result: Optional[Dict[str, Any]]

    # Context Bucket & Memory
    context_bucket: List[Dict[str, Any]]  # Stores multi-turn history, recommended games, and entity references

    # Execution telemetry and output
    agent_steps: List[Dict[str, str]]
    final_response: str
    error: Optional[str]
