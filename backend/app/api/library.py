from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.library_repo import LibraryRepository
from app.schemas.game import GameRead

router = APIRouter(prefix="/users/{user_id}/library", tags=["Library"])

@router.get("", response_model=List[GameRead])
def get_user_library(user_id: int, db: Session = Depends(get_db)):
    """Retrieve all purchased games owned by the user."""
    repo = LibraryRepository(db)
    items = repo.get_by_user_id(user_id)
    result = []
    for item in items:
        if item.game:
            gr = GameRead.model_validate(item.game)
            gr.is_owned = True
            gr.is_in_cart = False
            result.append(gr)
    return result
