import pytest
from app.clients.api_client import BackendApiClient, backend_api_client
from app.database.session import SessionLocal
from app.services.chroma_service import chroma_service

@pytest.fixture(scope="module", autouse=True)
def setup_chroma():
    db = SessionLocal()
    try:
        chroma_service.index_games_from_db(db)
    finally:
        db.close()

def test_api_client_get_games():
    """Verify BackendApiClient retrieves catalog games over HTTP."""
    games = backend_api_client.get_games(limit=5)
    assert isinstance(games, list)
    assert len(games) > 0
    assert "id" in games[0]
    assert "title" in games[0]

def test_api_client_get_single_game():
    """Verify BackendApiClient retrieves a single game by ID."""
    games = backend_api_client.get_games(limit=1)
    assert len(games) > 0
    game_id = games[0]["id"]

    game = backend_api_client.get_game(game_id)
    assert game is not None
    assert game["id"] == game_id
    assert game["title"] == games[0]["title"]

def test_api_client_get_nonexistent_game():
    """Verify BackendApiClient returns None for 404 game ID."""
    game = backend_api_client.get_game(999999)
    assert game is None

def test_api_client_semantic_search():
    """Verify BackendApiClient calls semantic search endpoint."""
    results = backend_api_client.semantic_search(query="cozy relaxing farm", limit=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("Meadowvale" in g["title"] for g in results)

def test_api_client_user_and_wallet():
    """Verify BackendApiClient retrieves user profile and wallet."""
    user = backend_api_client.get_user(1)
    assert user.get("found") is True
    assert "wallet_balance" in user
    assert user["id"] == 1

def test_api_client_user_cart_and_library():
    """Verify BackendApiClient retrieves cart and library summaries."""
    cart = backend_api_client.get_user_cart(1)
    assert "items" in cart
    assert "total_price" in cart

    lib = backend_api_client.get_user_library(1)
    assert isinstance(lib, list)

def test_api_client_validate_purchase():
    """Verify BackendApiClient validates purchases via REST API."""
    res = backend_api_client.validate_purchase(1, [1])
    assert "valid" in res
    assert "requires_approval" in res

def test_api_client_cart_operations():
    """Verify add to cart and remove from cart via BackendApiClient."""
    # Find an unowned game for user 1
    lib = backend_api_client.get_user_library(1)
    owned_ids = {g["id"] for g in lib}
    all_games = backend_api_client.get_games(limit=20)
    unowned = next((g for g in all_games if g["id"] not in owned_ids), None)
    assert unowned is not None

    # Add to cart
    add_res = backend_api_client.add_to_cart(1, unowned["id"])
    assert add_res["success"] is True

    # Check cart contains it
    cart = backend_api_client.get_user_cart(1)
    cart_game_ids = [item["game_id"] for item in cart["items"]]
    assert unowned["id"] in cart_game_ids

    # Remove from cart
    rem_res = backend_api_client.remove_from_cart(1, unowned["id"])
    assert rem_res["success"] is True

    # Check cart no longer contains it
    cart_after = backend_api_client.get_user_cart(1)
    cart_after_ids = [item["game_id"] for item in cart_after["items"]]
    assert unowned["id"] not in cart_after_ids
