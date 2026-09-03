from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def create(self, name: str, email: str, wallet_balance: float = 0.0) -> User:
        user = User(name=name, email=email, wallet_balance=wallet_balance)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_wallet(self, user_id: int, new_balance: float) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.wallet_balance = round(new_balance, 2)
            self.db.flush()
        return user
