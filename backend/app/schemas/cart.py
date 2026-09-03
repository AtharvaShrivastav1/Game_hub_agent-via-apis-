from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict
from app.schemas.game import GameRead

class AddToCartRequest(BaseModel):
    game_id: int

class CartItemRead(BaseModel):
    id: int
    user_id: int
    game_id: int
    quantity: int
    created_at: datetime
    game: GameRead
    model_config = ConfigDict(from_attributes=True)

class CartSummary(BaseModel):
    items: List[CartItemRead]
    item_count: int
    total_price: float
    user_wallet_balance: float
    is_affordable: bool
