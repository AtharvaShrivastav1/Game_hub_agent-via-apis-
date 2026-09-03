from typing import List
from sqlalchemy.orm import Session, joinedload
from app.models.purchase import Purchase

class PurchaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> List[Purchase]:
        return (
            self.db.query(Purchase)
            .options(joinedload(Purchase.game))
            .filter(Purchase.user_id == user_id)
            .order_by(Purchase.purchased_at.desc())
            .all()
        )

    def create(self, user_id: int, game_id: int, price: float, status: str = "COMPLETED") -> Purchase:
        purchase = Purchase(user_id=user_id, game_id=game_id, price=price, status=status)
        self.db.add(purchase)
        self.db.flush()
        return purchase
