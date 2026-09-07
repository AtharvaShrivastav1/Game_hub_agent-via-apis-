import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.user import User
from app.models.game import Game
from app.models.library import UserGameLibrary
from app.models.cart import CartItem

client = TestClient(app)

@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()

def test_purchase_validation_success(db):
    """Test POST /api/purchases/validate with an unowned game and sufficient balance."""
    user = db.query(User).filter(User.id == 1).first()
    assert user is not None
    user.wallet_balance = 5000.0
    db.commit()

    # Find unowned game
    owned_ids = {item.game_id for item in db.query(UserGameLibrary).filter(UserGameLibrary.user_id == 1).all()}
    game = db.query(Game).filter(~Game.id.in_(owned_ids), Game.price < 3000).first()
    assert game is not None

    response = client.post(
        "/api/purchases/validate",
        json={"user_id": 1, "game_ids": [game.id]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["can_afford"] is True
    assert data["total_price"] == game.price
    assert data["remaining_balance"] == round(5000.0 - game.price, 2)
    assert game.id in data["game_ids"]
    assert game.title in data["game_titles"]

def test_purchase_validation_duplicate_ownership(db):
    """Test POST /api/purchases/validate rejects already owned games with 400 Bad Request."""
    game = db.query(Game).first()
    assert game is not None

    # Ensure user 1 owns this game
    existing = db.query(UserGameLibrary).filter(UserGameLibrary.user_id == 1, UserGameLibrary.game_id == game.id).first()
    if not existing:
        db.add(UserGameLibrary(user_id=1, game_id=game.id))
        db.commit()

    response = client.post(
        "/api/purchases/validate",
        json={"user_id": 1, "game_ids": [game.id]}
    )
    assert response.status_code == 400
    assert "already own" in response.json()["detail"].lower()

    # Clean up
    db.query(UserGameLibrary).filter(UserGameLibrary.user_id == 1, UserGameLibrary.game_id == game.id).delete()
    db.commit()

def test_purchase_validation_nonexistent_game():
    """Test POST /api/purchases/validate with non-existent game ID returns 400."""
    response = client.post(
        "/api/purchases/validate",
        json={"user_id": 1, "game_ids": [999999]}
    )
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"].lower()

def test_purchase_execution_success(db):
    """Test POST /api/purchases/execute commits atomic purchase and updates wallet & library."""
    import uuid
    unique_email = f"exec_{uuid.uuid4().hex[:8]}@test.io"
    temp_user = User(name="Execute Test User", email=unique_email, wallet_balance=3000.0)
    db.add(temp_user)
    db.commit()
    db.refresh(temp_user)

    try:
        game = db.query(Game).filter(Game.price < 2000).first()
        assert game is not None

        # Add to cart first
        db.add(CartItem(user_id=temp_user.id, game_id=game.id))
        db.commit()

        response = client.post(
            "/api/purchases/execute",
            json={"user_id": temp_user.id, "game_ids": [game.id]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["new_wallet_balance"] == round(3000.0 - game.price, 2)

        # Verify database state
        db.commit()
        db.refresh(temp_user)
        assert temp_user.wallet_balance == round(3000.0 - game.price, 2)
        lib_entry = db.query(UserGameLibrary).filter(
            UserGameLibrary.user_id == temp_user.id,
            UserGameLibrary.game_id == game.id
        ).first()
        assert lib_entry is not None

        # Cart item must be cleared
        cart_entry = db.query(CartItem).filter(
            CartItem.user_id == temp_user.id,
            CartItem.game_id == game.id
        ).first()
        assert cart_entry is None
    finally:
        db.query(UserGameLibrary).filter(UserGameLibrary.user_id == temp_user.id).delete()
        db.query(CartItem).filter(CartItem.user_id == temp_user.id).delete()
        db.delete(temp_user)
        db.commit()

def test_purchase_execution_insufficient_funds(db):
    """Test POST /api/purchases/execute fails and rolls back when funds are insufficient."""
    import uuid
    unique_email = f"broke_{uuid.uuid4().hex[:8]}@test.io"
    temp_user = User(name="Broke User", email=unique_email, wallet_balance=10.0)
    db.add(temp_user)
    db.commit()
    db.refresh(temp_user)

    try:
        game = db.query(Game).filter(Game.price > 500).first()
        assert game is not None

        response = client.post(
            "/api/purchases/execute",
            json={"user_id": temp_user.id, "game_ids": [game.id]}
        )
        assert response.status_code == 400
        assert "insufficient funds" in response.json()["detail"].lower()

        # Verify wallet untouched
        db.commit()
        db.refresh(temp_user)
        assert temp_user.wallet_balance == 10.0
    finally:
        db.delete(temp_user)
        db.commit()
