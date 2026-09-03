from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.cart import CartItem

class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> List[CartItem]:
        return (
            self.db.query(CartItem)
            .options(joinedload(CartItem.game))
            .filter(CartItem.user_id == user_id)
            .all()
        )

    def get_item(self, user_id: int, game_id: int) -> Optional[CartItem]:
        return (
            self.db.query(CartItem)
            .filter(CartItem.user_id == user_id, CartItem.game_id == game_id)
            .first()
        )

    def add(self, user_id: int, game_id: int) -> CartItem:
        existing = self.get_item(user_id, game_id)
        if existing:
            return existing
        item = CartItem(user_id=user_id, game_id=game_id, quantity=1)
        self.db.add(item)
        self.db.flush()
        return item

    def remove(self, user_id: int, game_id: int) -> bool:
        item = self.get_item(user_id, game_id)
        if item:
            self.db.delete(item)
            self.db.flush()
            return True
        return False

    def clear(self, user_id: int) -> int:
        count = self.db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        self.db.flush()
        return count
