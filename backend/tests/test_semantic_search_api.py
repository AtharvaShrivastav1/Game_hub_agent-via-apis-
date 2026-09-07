import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.services.chroma_service import chroma_service

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_chroma():
    db = SessionLocal()
    try:
        chroma_service.index_games_from_db(db)
    finally:
        db.close()

def test_semantic_search_endpoint_query():
    """Test GET /api/games/semantic-search with natural language query."""
    response = client.get(
        "/api/games/semantic-search",
        params={"query": "cozy relaxing farm homestead life", "limit": 4}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Meadowvale should be present for cozy relaxing farm query
    titles = [g["title"] for g in data]
    assert any("Meadowvale" in t for t in titles), f"Expected 'Meadowvale' in {titles}"

    # Verify schema fields
    item = data[0]
    assert "id" in item
    assert "title" in item
    assert "price" in item
    assert "semantic_score" in item
    assert item["source"] == "semantic"

def test_semantic_search_with_price_filter():
    """Test GET /api/games/semantic-search with max_price constraint."""
    response = client.get(
        "/api/games/semantic-search",
        params={"query": "action combat parrying", "max_price": 1000.0, "limit": 5}
    )
    assert response.status_code == 200
    data = response.json()
    for g in data:
        assert g["price"] <= 1000.0

def test_semantic_search_empty_query():
    """Test GET /api/games/semantic-search requires query parameter."""
    response = client.get("/api/games/semantic-search")
    assert response.status_code == 422  # FastAPI validation error
