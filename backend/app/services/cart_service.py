from typing import List
from sqlalchemy.orm import Session
from app.repositories.cart_repo import CartRepository
from app.repositories.game_repo import GameRepository
from app.repositories.library_repo import LibraryRepository
from app.repositories.user_repo import UserRepository
from app.schemas.cart import CartSummary, CartItemRead
from app.schemas.game import GameRead

class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.game_repo = GameRepository(db)
        self.library_repo = LibraryRepository(db)
        self.user_repo = UserRepository(db)

    def get_cart_summary(self, user_id: int) -> CartSummary:
        user = self.user_repo.get_by_id(user_id)
        wallet_balance = user.wallet_balance if user else 0.0

        items = self.cart_repo.get_by_user_id(user_id)
        total_price = sum(item.game.price for item in items if item.game)

        item_reads = []
        for item in items:
            gr = GameRead.model_validate(item.game)
            gr.is_in_cart = True
            gr.is_owned = False
            item_reads.append(
                CartItemRead(
                    id=item.id,
                    user_id=item.user_id,
                    game_id=item.game_id,
                    quantity=item.quantity,
                    created_at=item.created_at,
                    game=gr,
                )
            )

        return CartSummary(
            items=item_reads,
            item_count=len(item_reads),
            total_price=round(total_price, 2),
            user_wallet_balance=round(wallet_balance, 2),
            is_affordable=wallet_balance >= total_price,
        )

    def add_to_cart(self, user_id: int, game_id: int):
        game = self.game_repo.get_by_id(game_id)
        if not game:
            raise ValueError(f"Game with ID {game_id} not found in store catalog.")

        if self.library_repo.is_game_owned(user_id, game_id):
            raise ValueError(f"You already own '{game.title}'. You cannot add an owned game to your cart.")

        item = self.cart_repo.add(user_id, game_id)
        self.db.commit()
        return item

    def remove_from_cart(self, user_id: int, game_id: int) -> bool:
        removed = self.cart_repo.remove(user_id, game_id)
        self.db.commit()
        return removed

    def clear_cart(self, user_id: int) -> int:
        count = self.cart_repo.clear(user_id)
        self.db.commit()
        return count
