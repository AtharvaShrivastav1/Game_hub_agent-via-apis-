from typing import Optional, List, Dict, Any
from app.database.session import SessionLocal
from app.repositories.game_repo import GameRepository
from app.repositories.library_repo import LibraryRepository
from app.repositories.cart_repo import CartRepository
from app.repositories.user_repo import UserRepository
from app.services.cart_service import CartService
from app.services.purchase_service import PurchaseService

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
    """Search and filter games in the GameHub catalog using controlled database queries."""
    with SessionLocal() as db:
        repo = GameRepository(db)
        games = repo.search_games(
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
                "id": g.id,
                "title": g.title,
                "genre": g.genre,
                "price": g.price,
                "rating": g.rating,
                "duration_hours": g.duration_hours,
                "developer": g.developer,
                "description": g.description[:180] + "..." if len(g.description) > 180 else g.description,
            }
            for g in games
        ]

def get_game(game_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve full details for a specific game by ID."""
    with SessionLocal() as db:
        repo = GameRepository(db)
        g = repo.get_by_id(game_id)
        if not g:
            return None
        return {
            "id": g.id,
            "title": g.title,
            "genre": g.genre,
            "price": g.price,
            "rating": g.rating,
            "duration_hours": g.duration_hours,
            "developer": g.developer,
            "release_date": g.release_date,
            "description": g.description,
            "image_url": g.image_url,
        }

def get_user_library(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all games owned by the user in their library."""
    with SessionLocal() as db:
        repo = LibraryRepository(db)
        items = repo.get_by_user_id(user_id)
        return [
            {
                "game_id": item.game_id,
                "title": item.game.title,
                "genre": item.game.genre,
                "price": item.game.price,
                "added_at": item.added_at.isoformat() if item.added_at else None,
            }
            for item in items if item.game
        ]

def get_user_cart(user_id: int) -> Dict[str, Any]:
    """Retrieve items currently in the user's cart along with subtotal."""
    with SessionLocal() as db:
        service = CartService(db)
        summary = service.get_cart_summary(user_id)
        return {
            "items": [
                {
                    "game_id": item.game_id,
                    "title": item.game.title,
                    "genre": item.game.genre,
                    "price": item.game.price,
                }
                for item in summary.items
            ],
            "item_count": summary.item_count,
            "total_price": summary.total_price,
            "wallet_balance": summary.user_wallet_balance,
            "is_affordable": summary.is_affordable,
        }

def get_user_wallet(user_id: int) -> Dict[str, Any]:
    """Retrieve the current user's wallet balance."""
    with SessionLocal() as db:
        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        if not user:
            return {"user_id": user_id, "wallet_balance": 0.0, "found": False}
        return {
            "user_id": user.id,
            "name": user.name,
            "wallet_balance": user.wallet_balance,
            "found": True,
        }

def add_to_cart(user_id: int, game_id: int) -> Dict[str, Any]:
    """Add a game to the user's shopping cart."""
    with SessionLocal() as db:
        service = CartService(db)
        try:
            item = service.add_to_cart(user_id, game_id)
            return {"success": True, "game_id": game_id, "message": "Added to cart successfully."}
        except Exception as e:
            return {"success": False, "error": str(e)}

def remove_from_cart(user_id: int, game_id: int) -> Dict[str, Any]:
    """Remove a game from the user's shopping cart."""
    with SessionLocal() as db:
        service = CartService(db)
        success = service.remove_from_cart(user_id, game_id)
        return {"success": success, "game_id": game_id}

def validate_purchase(user_id: int, game_ids: List[int]) -> Dict[str, Any]:
    """Validate purchase conditions for one or more games before requesting approval."""
    with SessionLocal() as db:
        service = PurchaseService(db)
        try:
            summary = service.validate_purchase(user_id, game_ids)
            return {
                "valid": True,
                "game_ids": summary.game_ids,
                "game_titles": summary.game_titles,
                "total_price": summary.total_price,
                "current_wallet_balance": summary.current_wallet_balance,
                "remaining_balance": summary.remaining_balance,
                "can_afford": summary.can_afford,
                "requires_approval": True,
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "requires_approval": False,
            }

def purchase_game(user_id: int, game_ids: List[int]) -> Dict[str, Any]:
    """Execute purchase transaction after human approval has been granted."""
    with SessionLocal() as db:
        service = PurchaseService(db)
        try:
            res = service.execute_purchase(user_id, game_ids)
            return {
                "success": res.success,
                "message": res.message,
                "new_wallet_balance": res.new_wallet_balance,
                "purchased_games": [p.game.title for p in res.purchases if p.game],
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
