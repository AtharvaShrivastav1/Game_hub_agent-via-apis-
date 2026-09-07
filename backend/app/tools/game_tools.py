"""
GameHub Agent Grounding Tools (API-First Client Layer).

All tools in this module interact with the GameHub backend exclusively through
HTTP REST APIs via BackendApiClient. Direct imports of SessionLocal, SQLAlchemy
models, repositories, domain services, or ChromaDB are strictly prohibited here.
"""

import logging
from typing import Optional, List, Dict, Any
from app.clients.api_client import backend_api_client

logger = logging.getLogger("gamehub.tools")


def search_games(
    genre: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    max_duration: Optional[float] = None,
    min_rating: Optional[float] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Search and filter games in the GameHub catalog using backend REST API."""
    games = backend_api_client.get_games(
        genre=genre,
        min_price=min_price,
        max_price=max_price,
        max_duration=max_duration,
        min_rating=min_rating,
        search=search,
        sort_by=sort_by,
        limit=limit,
    )
    return [
        {
            "id": g["id"],
            "title": g["title"],
            "genre": g["genre"],
            "price": g["price"],
            "rating": g["rating"],
            "duration_hours": g["duration_hours"],
            "developer": g["developer"],
            "description": (
                g["description"][:180] + "..."
                if len(g.get("description", "")) > 180
                else g.get("description", "")
            ),
        }
        for g in games
    ]


def get_game(game_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full details for a specific game by ID via backend REST API."""
    g = backend_api_client.get_game(game_id)
    if not g:
        return None
    return {
        "id": g["id"],
        "title": g["title"],
        "genre": g["genre"],
        "price": g["price"],
        "rating": g["rating"],
        "duration_hours": g["duration_hours"],
        "developer": g["developer"],
        "release_date": g.get("release_date", ""),
        "description": g.get("description", ""),
        "image_url": g.get("image_url", ""),
    }


def get_user_library(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all games owned by the user in their library via backend REST API."""
    items = backend_api_client.get_user_library(user_id)
    return [
        {
            "game_id": item["id"],
            "title": item["title"],
            "genre": item["genre"],
            "price": item["price"],
            "added_at": item.get("created_at"),
        }
        for item in items
    ]


def get_user_cart(user_id: int) -> Dict[str, Any]:
    """Retrieve items currently in the user's cart along with subtotal via backend REST API."""
    summary = backend_api_client.get_user_cart(user_id)
    items_out = []
    for item in summary.get("items", []):
        game_data = item.get("game", {})
        if isinstance(game_data, dict) and game_data:
            items_out.append({
                "game_id": item.get("game_id", game_data.get("id")),
                "title": game_data.get("title", ""),
                "genre": game_data.get("genre", ""),
                "price": game_data.get("price", 0.0),
            })
        else:
            items_out.append({
                "game_id": item.get("game_id"),
                "title": item.get("title", ""),
                "genre": item.get("genre", ""),
                "price": item.get("price", 0.0),
            })

    return {
        "items": items_out,
        "item_count": summary.get("item_count", len(items_out)),
        "total_price": summary.get("total_price", 0.0),
        "wallet_balance": summary.get("user_wallet_balance", 0.0),
        "is_affordable": summary.get("is_affordable", True),
    }


def get_user_wallet(user_id: int) -> Dict[str, Any]:
    """Retrieve the current user's wallet balance via backend REST API."""
    user = backend_api_client.get_user(user_id)
    if not user.get("found", True):
        return {"user_id": user_id, "wallet_balance": 0.0, "found": False}
    return {
        "user_id": user.get("id", user_id),
        "name": user.get("name", f"User {user_id}"),
        "wallet_balance": user.get("wallet_balance", 0.0),
        "found": True,
    }


def add_to_cart(user_id: int, game_id: int) -> Dict[str, Any]:
    """Add a game to the user's shopping cart via backend REST API."""
    return backend_api_client.add_to_cart(user_id, game_id)


def remove_from_cart(user_id: int, game_id: int) -> Dict[str, Any]:
    """Remove a game from the user's shopping cart via backend REST API."""
    return backend_api_client.remove_from_cart(user_id, game_id)


def validate_purchase(user_id: int, game_ids: List[int]) -> Dict[str, Any]:
    """Validate purchase conditions via backend REST API before requesting approval."""
    res = backend_api_client.validate_purchase(user_id, game_ids)
    if res.get("valid"):
        return {
            "valid": True,
            "game_ids": res.get("game_ids", game_ids),
            "game_titles": res.get("game_titles", []),
            "total_price": res.get("total_price", 0.0),
            "current_wallet_balance": res.get("current_wallet_balance", 0.0),
            "remaining_balance": res.get("remaining_balance", 0.0),
            "can_afford": res.get("can_afford", False),
            "requires_approval": True,
        }
    return {
        "valid": False,
        "error": res.get("error", "Purchase validation failed."),
        "requires_approval": False,
    }


def purchase_game(user_id: int, game_ids: List[int]) -> Dict[str, Any]:
    """Execute atomic purchase transaction via backend REST API after human approval."""
    return backend_api_client.execute_purchase(user_id, game_ids)


def semantic_search_games(
    query: str,
    limit: int = 8,
    genre: Optional[str] = None,
    max_price: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic similarity search over game catalog embeddings via backend REST API.

    ChromaDB vector retrieval is strictly encapsulated inside the backend API
    (/api/games/semantic-search). This client tool consumes the endpoint over HTTP.
    """
    results = backend_api_client.semantic_search(
        query=query,
        limit=limit,
        genre=genre,
        max_price=max_price,
    )

    enriched = []
    for g in results:
        desc = g.get("description", "")
        formatted_desc = desc[:180] + "..." if len(desc) > 180 else desc
        enriched.append({
            "id": g["id"],
            "title": g["title"],
            "genre": g["genre"],
            "price": g["price"],
            "rating": g["rating"],
            "duration_hours": g["duration_hours"],
            "developer": g["developer"],
            "description": formatted_desc,
            "semantic_score": g.get("semantic_score"),
            "source": g.get("source", "semantic"),
        })

    return enriched
