from typing import List, Optional
from sqlalchemy.orm import Session
from app.repositories.game_repo import GameRepository
from app.repositories.library_repo import LibraryRepository
from app.repositories.cart_repo import CartRepository
from app.schemas.game import GameRead, GameFilterParams

class GameService:
    def __init__(self, db: Session):
        self.db = db
        self.game_repo = GameRepository(db)
        self.library_repo = LibraryRepository(db)
        self.cart_repo = CartRepository(db)

    def get_game(self, game_id: int, user_id: Optional[int] = None) -> Optional[GameRead]:
        game = self.game_repo.get_by_id(game_id)
        if not game:
            return None

        is_owned = False
        is_in_cart = False
        if user_id:
            is_owned = self.library_repo.is_game_owned(user_id, game_id)
            is_in_cart = self.cart_repo.get_item(user_id, game_id) is not None

        game_read = GameRead.model_validate(game)
        game_read.is_owned = is_owned
        game_read.is_in_cart = is_in_cart
        return game_read

    def search_games(self, params: GameFilterParams, user_id: Optional[int] = None) -> List[GameRead]:
        games = self.game_repo.search_games(
            genre=params.genre,
            min_price=params.min_price,
            max_price=params.max_price,
            max_duration=params.max_duration,
            min_rating=params.min_rating,
            search=params.search,
            sort_by=params.sort_by,
            limit=params.limit,
            offset=params.offset,
        )

        owned_ids = set(self.library_repo.get_owned_game_ids(user_id)) if user_id else set()
        cart_ids = {item.game_id for item in self.cart_repo.get_by_user_id(user_id)} if user_id else set()

        result = []
        for g in games:
            gr = GameRead.model_validate(g)
            gr.is_owned = g.id in owned_ids
            gr.is_in_cart = g.id in cart_ids
            result.append(gr)

        return result

    def get_genres(self) -> List[str]:
        return self.game_repo.get_genres()
