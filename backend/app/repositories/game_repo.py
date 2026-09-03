from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from app.models.game import Game

class GameRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, game_id: int) -> Optional[Game]:
        return self.db.query(Game).filter(Game.id == game_id).first()

    def get_by_title(self, title: str) -> Optional[Game]:
        return self.db.query(Game).filter(Game.title.ilike(f"%{title}%")).first()

    def get_by_titles(self, titles: List[str]) -> List[Game]:
        return self.db.query(Game).filter(
            or_(*[Game.title.ilike(f"%{t}%") for t in titles])
        ).all()

    def get_genres(self) -> List[str]:
        results = self.db.query(Game.genre).distinct().all()
        return sorted([r[0] for r in results if r[0]])

    def search_games(
        self,
        genre: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        max_duration: Optional[float] = None,
        min_rating: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Game]:
        query = self.db.query(Game)

        if genre and genre.lower() != "all":
            query = query.filter(Game.genre.ilike(f"%{genre}%"))

        if min_price is not None:
            query = query.filter(Game.price >= min_price)

        if max_price is not None:
            query = query.filter(Game.price <= max_price)

        if max_duration is not None:
            query = query.filter(Game.duration_hours <= max_duration)

        if min_rating is not None:
            query = query.filter(Game.rating >= min_rating)

        if search:
            search_pattern = f"%{search}%"
            query = query.filter(
                or_(
                    Game.title.ilike(search_pattern),
                    Game.description.ilike(search_pattern),
                    Game.developer.ilike(search_pattern),
                    Game.genre.ilike(search_pattern),
                )
            )

        if sort_by == "price_asc":
            query = query.order_by(asc(Game.price))
        elif sort_by == "price_desc":
            query = query.order_by(desc(Game.price))
        elif sort_by == "rating_desc":
            query = query.order_by(desc(Game.rating))
        elif sort_by == "duration_asc":
            query = query.order_by(asc(Game.duration_hours))
        else:
            query = query.order_by(desc(Game.rating))

        return query.offset(offset).limit(limit).all()
