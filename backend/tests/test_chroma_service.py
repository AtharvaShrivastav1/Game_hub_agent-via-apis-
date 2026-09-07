import pytest
from app.database.session import SessionLocal
from app.services.chroma_service import chroma_service
from app.tools.game_tools import semantic_search_games

def test_chroma_indexing_and_semantic_search():
    """Verify that games are indexed into ChromaDB and semantic similarity search works."""
    db = SessionLocal()
    try:
        # Index games into ChromaDB
        count = chroma_service.index_games_from_db(db)
        assert count > 0, "Expected at least 1 game to be indexed"

        # Test semantic search for cozy / farming themes
        results = chroma_service.semantic_search(query="cozy relaxing farm homestead life", n_results=3)
        assert len(results) > 0, "Expected semantic search results for cozy query"
        titles = [r["title"] for r in results]
        assert any("Meadowvale" in t for t in titles), f"Expected 'Meadowvale: Cozy Homestead' in results, got {titles}"

        # Test tool wrapper with description enrichment
        tool_results = semantic_search_games(query="dark fantasy souls combat parrying", limit=3)
        assert len(tool_results) > 0
        assert "description" in tool_results[0]
    finally:
        db.close()
