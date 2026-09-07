"""
ChromaDB Semantic Search Service for GameHub.

Provides a vector embedding layer over the game catalog to enable
semantic similarity search (e.g. "something like Dark Souls but in space").
Runs alongside the existing SQL database — NOT a replacement.
"""

import logging
from typing import List, Dict, Any, Optional

import chromadb
from sqlalchemy.orm import Session

from app.models.game import Game
from app.config import settings

logger = logging.getLogger(__name__)


class ChromaService:
    """
    Manages a ChromaDB collection of game catalog embeddings.

    Uses ChromaDB's built-in default embedding function (all-MiniLM-L6-v2)
    which runs locally with zero API cost. The collection is ephemeral
    (rebuilt on each server start) to stay consistent with the SQL seed.
    """

    def __init__(self):
        self._client: Optional[chromadb.ClientAPI] = None
        self._collection: Optional[chromadb.Collection] = None
        self._initialized = False

    def _ensure_client(self):
        """Lazily initialize the ChromaDB client and collection."""
        if self._client is None:
            self._client = chromadb.Client()  # Ephemeral in-memory client
            self._collection = self._client.get_or_create_collection(
                name="game_catalog",
                metadata={"hnsw:space": "cosine"},  # Cosine similarity
            )
            logger.info("ChromaDB ephemeral client initialized with 'game_catalog' collection.")

    def index_games_from_db(self, db: Session) -> int:
        """
        Read all games from the SQL database and upsert them into ChromaDB.

        Each game is embedded using a combined text of:
            title + genre + description + developer

        Metadata (id, title, genre, price, rating, duration_hours) is stored
        alongside the embedding for zero-join retrieval.

        Returns the number of games indexed.
        """
        if not settings.CHROMA_ENABLED:
            logger.info("ChromaDB is disabled (CHROMA_ENABLED=false). Skipping indexing.")
            return 0

        self._ensure_client()

        games = db.query(Game).all()
        if not games:
            logger.warning("No games found in SQL database. ChromaDB collection will be empty.")
            return 0

        # Prepare batch data for upsert
        ids = []
        documents = []
        metadatas = []

        for game in games:
            # Combined text for richer semantic matching
            combined_text = (
                f"{game.title}. "
                f"Genre: {game.genre}. "
                f"Developer: {game.developer}. "
                f"{game.description}"
            )

            ids.append(str(game.id))
            documents.append(combined_text)
            metadatas.append({
                "game_id": game.id,
                "title": game.title,
                "genre": game.genre,
                "price": float(game.price),
                "rating": float(game.rating),
                "duration_hours": float(game.duration_hours),
                "developer": game.developer,
            })

        # Upsert into ChromaDB (idempotent — safe to call on every startup)
        self._collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )

        logger.info(f"ChromaDB: Indexed {len(games)} games into 'game_catalog' collection.")
        return len(games)

    def semantic_search(
        self,
        query: str,
        n_results: int = 8,
        genre_filter: Optional[str] = None,
        max_price: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic similarity search over the game catalog.

        Args:
            query: Natural language search query (e.g. "cozy relaxing game")
            n_results: Maximum number of results to return
            genre_filter: Optional genre to filter results (applied as ChromaDB where clause)
            max_price: Optional max price filter

        Returns:
            List of game dicts with metadata and similarity distance score.
        """
        if not settings.CHROMA_ENABLED or self._collection is None:
            return []

        try:
            # Build optional where filters
            where_filters = {}
            if genre_filter and genre_filter.lower() != "all":
                where_filters["genre"] = {"$eq": genre_filter}
            if max_price is not None:
                where_filters["price"] = {"$lte": max_price}

            # ChromaDB requires $and for multiple conditions
            where_clause = None
            if len(where_filters) > 1:
                where_clause = {"$and": [
                    {k: v} for k, v in where_filters.items()
                ]}
            elif len(where_filters) == 1:
                key, val = next(iter(where_filters.items()))
                where_clause = {key: val}

            results = self._collection.query(
                query_texts=[query],
                n_results=min(n_results, self._collection.count() or n_results),
                where=where_clause if where_clause else None,
            )

            # Parse results into a clean list of dicts
            games = []
            if results and results["metadatas"] and results["metadatas"][0]:
                for i, metadata in enumerate(results["metadatas"][0]):
                    distance = results["distances"][0][i] if results.get("distances") else None
                    games.append({
                        "id": metadata["game_id"],
                        "title": metadata["title"],
                        "genre": metadata["genre"],
                        "price": metadata["price"],
                        "rating": metadata["rating"],
                        "duration_hours": metadata["duration_hours"],
                        "developer": metadata["developer"],
                        "semantic_score": round(1.0 - distance, 4) if distance is not None else None,
                        "source": "semantic",
                    })

            logger.info(
                f"ChromaDB semantic search for '{query[:50]}...' returned {len(games)} results."
            )
            return games

        except Exception as e:
            logger.error(f"ChromaDB semantic search failed: {e}. Returning empty results.")
            return []

    def reset(self):
        """Clear the collection (used during session reset)."""
        if self._collection is not None:
            try:
                self._client.delete_collection("game_catalog")
                self._collection = self._client.get_or_create_collection(
                    name="game_catalog",
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("ChromaDB collection reset successfully.")
            except Exception as e:
                logger.error(f"ChromaDB reset failed: {e}")


# Singleton instance — similar pattern to assistant_graph in workflow.py
chroma_service = ChromaService()
