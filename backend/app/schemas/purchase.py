from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.game import GameRead

class PurchaseRead(BaseModel):
    id: int
    user_id: int
    game_id: int
    price: float
    status: str
    purchased_at: datetime
    game: Optional[GameRead] = None
    model_config = ConfigDict(from_attributes=True)

class PurchaseSummary(BaseModel):
    game_ids: List[int]
    game_titles: List[str]
    total_price: float
    current_wallet_balance: float
    remaining_balance: float
    can_afford: bool
    requires_approval: bool = True

class PurchaseApprovalRequest(BaseModel):
    thread_id: str
    approved: bool

class PurchaseExecutionResult(BaseModel):
    success: bool
    message: str
    purchases: List[PurchaseRead] = []
    new_wallet_balance: float
