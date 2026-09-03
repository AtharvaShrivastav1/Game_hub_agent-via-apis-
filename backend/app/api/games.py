from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.game_service import GameService
from app.schemas.game import GameRead, GameFilterParams

router = APIRouter(prefix="/games", tags=["Games"])

@router.get("/genres", response_model=List[str])
def get_genres(db: Session = Depends(get_db)):
    """Retrieve all distinct game genres in the store."""
    service = GameService(db)
    return service.get_genres()

@router.get("", response_model=List[GameRead])
def get_games(
    genre: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    max_duration: Optional[float] = Query(None),
    min_rating: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Search and filter games in the catalog."""
    service = GameService(db)
    params = GameFilterParams(
        genre=genre,
        min_price=min_price,
        max_price=max_price,
        max_duration=max_duration,
        min_rating=min_rating,
        search=search,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )
    return service.search_games(params, user_id=user_id)

@router.get("/{game_id}", response_model=GameRead)
def get_game(
    game_id: int,
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """Retrieve full details of a single game."""
    service = GameService(db)
    game = service.get_game(game_id, user_id=user_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")
    return game
