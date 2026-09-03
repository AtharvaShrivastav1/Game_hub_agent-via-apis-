from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models.library import UserGameLibrary

class LibraryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_user_id(self, user_id: int) -> List[UserGameLibrary]:
        return (
            self.db.query(UserGameLibrary)
            .options(joinedload(UserGameLibrary.game))
            .filter(UserGameLibrary.user_id == user_id)
            .all()
        )

    def is_game_owned(self, user_id: int, game_id: int) -> bool:
        return (
            self.db.query(UserGameLibrary)
            .filter(UserGameLibrary.user_id == user_id, UserGameLibrary.game_id == game_id)
            .first()
            is not None
        )

    def get_owned_game_ids(self, user_id: int) -> List[int]:
        rows = (
            self.db.query(UserGameLibrary.game_id)
            .filter(UserGameLibrary.user_id == user_id)
            .all()
        )
        return [r[0] for r in rows]

    def add_to_library(self, user_id: int, game_id: int, purchase_id: Optional[int] = None) -> UserGameLibrary:
        record = UserGameLibrary(user_id=user_id, game_id=game_id, purchase_id=purchase_id)
        self.db.add(record)
        self.db.flush()
        return record
