from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.cart_service import CartService
from app.schemas.cart import CartSummary, AddToCartRequest

router = APIRouter(prefix="/users/{user_id}/cart", tags=["Cart"])

@router.get("", response_model=CartSummary)
def get_user_cart(user_id: int, db: Session = Depends(get_db)):
    """Retrieve shopping cart contents and price calculations for a user."""
    service = CartService(db)
    return service.get_cart_summary(user_id)

@router.post("", response_model=CartSummary)
def add_to_cart(user_id: int, payload: AddToCartRequest, db: Session = Depends(get_db)):
    """Add a game to the user's cart. Prevents duplicate ownership."""
    service = CartService(db)
    try:
        service.add_to_cart(user_id, payload.game_id)
        return service.get_cart_summary(user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{game_id}", response_model=CartSummary)
def remove_from_cart(user_id: int, game_id: int, db: Session = Depends(get_db)):
    """Remove a specific game from the user's cart."""
    service = CartService(db)
    service.remove_from_cart(user_id, game_id)
    return service.get_cart_summary(user_id)

@router.delete("", response_model=CartSummary)
def clear_cart(user_id: int, db: Session = Depends(get_db)):
    """Clear all items from the user's cart."""
    service = CartService(db)
    service.clear_cart(user_id)
    return service.get_cart_summary(user_id)
