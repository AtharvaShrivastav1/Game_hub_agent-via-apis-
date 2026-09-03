import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.game import Game
from app.models.user import User
from app.models.purchase import Purchase
from app.models.library import UserGameLibrary
from app.models.cart import CartItem
from app.repositories.user_repo import UserRepository
from app.repositories.game_repo import GameRepository
from app.repositories.library_repo import LibraryRepository
from app.repositories.cart_repo import CartRepository
from app.schemas.purchase import PurchaseSummary, PurchaseExecutionResult, PurchaseRead
from app.schemas.game import GameRead

logger = logging.getLogger(__name__)

class InsufficientWalletError(Exception):
    pass

class GameAlreadyOwnedError(Exception):
    pass

class PurchaseService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.game_repo = GameRepository(db)
        self.library_repo = LibraryRepository(db)
        self.cart_repo = CartRepository(db)

    def validate_purchase(self, user_id: int, game_ids: List[int]) -> PurchaseSummary:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} does not exist.")

        if not game_ids:
            raise ValueError("No games selected for purchase.")

        games: List[Game] = []
        titles = []
        total_price = 0.0

        for gid in game_ids:
            game = self.game_repo.get_by_id(gid)
            if not game:
                raise ValueError(f"Game with ID {gid} does not exist in catalog.")

            if self.library_repo.is_game_owned(user_id, gid):
                raise GameAlreadyOwnedError(f"You already own '{game.title}'. Cannot repurchase.")

            games.append(game)
            titles.append(game.title)
            total_price += game.price

        total_price = round(total_price, 2)
        wallet = round(user.wallet_balance, 2)
        remaining = round(wallet - total_price, 2)
        can_afford = wallet >= total_price

        return PurchaseSummary(
            game_ids=game_ids,
            game_titles=titles,
            total_price=total_price,
            current_wallet_balance=wallet,
            remaining_balance=remaining,
            can_afford=can_afford,
            requires_approval=True
        )

    def execute_purchase(self, user_id: int, game_ids: List[int]) -> PurchaseExecutionResult:
        """
        Executes an atomic ACID transaction for game purchases:
        1. Validates user and games.
        2. Checks for duplicate ownership.
        3. Checks wallet sufficiency.
        4. Deducts wallet balance.
        5. Creates Purchase entries.
        6. Adds games to user's library.
        7. Clears purchased games from cart.
        8. Commits atomically or rolls back completely on any error.
        """
        try:
            # Step 1: Pre-validation
            summary = self.validate_purchase(user_id, game_ids)
            if not summary.can_afford:
                shortfall = round(summary.total_price - summary.current_wallet_balance, 2)
                raise InsufficientWalletError(
                    f"Insufficient funds: You have ₹{summary.current_wallet_balance:.2f} available, but the total is ₹{summary.total_price:.2f}. Need ₹{shortfall:.2f} more."
                )

            # Step 2: Fetch user record
            user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
            if not user:
                raise ValueError("User not found during transaction.")

            # Double check balance under lock
            if user.wallet_balance < summary.total_price:
                raise InsufficientWalletError("Insufficient funds during transaction execution.")

            # Step 3: Deduct wallet
            user.wallet_balance = round(user.wallet_balance - summary.total_price, 2)
            self.db.flush()

            purchases_out: List[PurchaseRead] = []

            # Step 4: For each game, create purchase, add to library, remove from cart
            for gid in game_ids:
                game = self.db.query(Game).filter(Game.id == gid).first()
                purchase = Purchase(
                    user_id=user_id,
                    game_id=gid,
                    price=game.price,
                    status="COMPLETED"
                )
                self.db.add(purchase)
                self.db.flush()

                # Add to library
                lib_item = UserGameLibrary(
                    user_id=user_id,
                    game_id=gid,
                    purchase_id=purchase.id
                )
                self.db.add(lib_item)
                self.db.flush()

                # Remove from cart if present
                self.db.query(CartItem).filter(
                    CartItem.user_id == user_id,
                    CartItem.game_id == gid
                ).delete()

                purchases_out.append(
                    PurchaseRead(
                        id=purchase.id,
                        user_id=purchase.user_id,
                        game_id=purchase.game_id,
                        price=purchase.price,
                        status=purchase.status,
                        purchased_at=purchase.purchased_at,
                        game=GameRead.model_validate(game)
                    )
                )

            # Commit the entire transaction atomically
            self.db.commit()
            logger.info(f"Successfully processed purchase for user {user_id}: {summary.game_titles}")

            return PurchaseExecutionResult(
                success=True,
                message=f"Purchase successful! Added {len(game_ids)} game(s) to your library.",
                purchases=purchases_out,
                new_wallet_balance=user.wallet_balance
            )

        except Exception as e:
            self.db.rollback()
            logger.error(f"Purchase transaction failed and was rolled back: {e}")
            raise
