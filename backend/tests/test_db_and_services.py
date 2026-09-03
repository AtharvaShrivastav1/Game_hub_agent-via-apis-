import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.models.user import User
from app.models.game import Game
from app.models.cart import CartItem
from app.models.library import UserGameLibrary
from app.services.game_service import GameService
from app.services.cart_service import CartService
from app.services.purchase_service import PurchaseService, InsufficientWalletError, GameAlreadyOwnedError
from app.schemas.game import GameFilterParams

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_game_search_and_retrieval(db):
    service = GameService(db)
    # Search all RPG games
    params = GameFilterParams(genre="RPG")
    rpg_games = service.search_games(params, user_id=1)
    assert len(rpg_games) > 0
    for g in rpg_games:
        assert "RPG" in g.genre.upper()

    # Search with budget filter
    params = GameFilterParams(max_price=1000.0)
    budget_games = service.search_games(params, user_id=1)
    for g in budget_games:
        assert g.price <= 1000.0

def test_cart_operations(db):
    cart_service = CartService(db)
    user_id = 1

    # Clear cart first
    cart_service.clear_cart(user_id)

    # Find unowned game
    owned_ids = {item.game_id for item in db.query(UserGameLibrary).filter(UserGameLibrary.user_id == user_id).all()}
    unowned_game = db.query(Game).filter(~Game.id.in_(owned_ids)).first()
    assert unowned_game is not None

    # Add to cart
    cart_service.add_to_cart(user_id, unowned_game.id)
    summary = cart_service.get_cart_summary(user_id)
    assert summary.item_count >= 1
    assert any(item.game_id == unowned_game.id for item in summary.items)

    # Remove from cart
    cart_service.remove_from_cart(user_id, unowned_game.id)
    summary_after = cart_service.get_cart_summary(user_id)
    assert not any(item.game_id == unowned_game.id for item in summary_after.items)

def test_duplicate_ownership_prevention(db):
    cart_service = CartService(db)
    purchase_service = PurchaseService(db)
    user_id = 1

    # Ensure there is an owned game for user 1
    sample_game = db.query(Game).first()
    assert sample_game is not None
    
    owned_item = db.query(UserGameLibrary).filter(
        UserGameLibrary.user_id == user_id,
        UserGameLibrary.game_id == sample_game.id
    ).first()
    if not owned_item:
        owned_item = UserGameLibrary(user_id=user_id, game_id=sample_game.id)
        db.add(owned_item)
        db.commit()
        db.refresh(owned_item)

    # Adding owned game to cart must raise ValueError
    with pytest.raises(ValueError, match="already own"):
        cart_service.add_to_cart(user_id, owned_item.game_id)

    # Purchasing owned game must raise GameAlreadyOwnedError
    with pytest.raises(GameAlreadyOwnedError):
        purchase_service.validate_purchase(user_id, [owned_item.game_id])

    # Clean up test owned item
    db.delete(owned_item)
    db.commit()


def test_insufficient_wallet_rollback(db):
    purchase_service = PurchaseService(db)

    # Create temporary user with low balance
    temp_user = User(name="Poor Gamer", email="poor@gamer.io", wallet_balance=50.0)
    db.add(temp_user)
    db.commit()
    db.refresh(temp_user)

    expensive_game = db.query(Game).filter(Game.price > 1000).first()

    # Must raise InsufficientWalletError
    with pytest.raises(InsufficientWalletError):
        purchase_service.execute_purchase(temp_user.id, [expensive_game.id])

    # Ensure wallet was NOT deducted and game was NOT added to library
    db.refresh(temp_user)
    assert temp_user.wallet_balance == 50.0
    lib_count = db.query(UserGameLibrary).filter(UserGameLibrary.user_id == temp_user.id).count()
    assert lib_count == 0

    # Cleanup temp user
    db.delete(temp_user)
    db.commit()

def test_atomic_purchase_transaction_success(db):
    purchase_service = PurchaseService(db)
    cart_service = CartService(db)

    # Create test user with sufficient balance
    test_user = User(name="Buyer Test", email="buyer@test.io", wallet_balance=2500.0)
    db.add(test_user)
    db.commit()
    db.refresh(test_user)

    # Pick an unowned game
    game = db.query(Game).filter(Game.price < 1000).first()

    # Add to cart first
    cart_service.add_to_cart(test_user.id, game.id)
    cart_summary = cart_service.get_cart_summary(test_user.id)
    assert cart_summary.item_count == 1

    # Execute purchase
    initial_balance = test_user.wallet_balance
    result = purchase_service.execute_purchase(test_user.id, [game.id])

    assert result.success is True
    assert result.new_wallet_balance == round(initial_balance - game.price, 2)

    # Check game is in library
    in_lib = db.query(UserGameLibrary).filter(
        UserGameLibrary.user_id == test_user.id,
        UserGameLibrary.game_id == game.id
    ).first()
    assert in_lib is not None

    # Check cart is cleared
    cart_after = cart_service.get_cart_summary(test_user.id)
    assert cart_after.item_count == 0

    # Cleanup
    db.delete(test_user)
    db.commit()
