from datetime import datetime
from pydantic import BaseModel, ConfigDict

class UserBase(BaseModel):
    name: str
    email: str
    wallet_balance: float

class UserCreate(UserBase):
    pass

class UserRead(UserBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class WalletTopupRequest(BaseModel):
    amount: float
