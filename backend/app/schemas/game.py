from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class GameBase(BaseModel):
    title: str
    description: str
    genre: str
    price: float
    rating: float
    duration_hours: float
    developer: str
    release_date: str
    image_url: str

class GameCreate(GameBase):
    pass

class GameRead(GameBase):
    id: int
    created_at: datetime
    is_owned: Optional[bool] = False
    is_in_cart: Optional[bool] = False
    semantic_score: Optional[float] = None
    source: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class GameFilterParams(BaseModel):
    genre: Optional[str] = None
    max_price: Optional[float] = None
    min_price: Optional[float] = None
    max_duration: Optional[float] = None
    min_rating: Optional[float] = None
    search: Optional[str] = None
    sort_by: Optional[str] = None  # "price_asc", "price_desc", "rating_desc", "duration_asc"
    limit: int = 50
    offset: int = 0
