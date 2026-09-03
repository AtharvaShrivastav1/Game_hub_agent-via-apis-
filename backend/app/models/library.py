from datetime import datetime
from sqlalchemy import Column, Integer, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database.base import Base

class UserGameLibrary(Base):
    __tablename__ = "user_game_library"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id", ondelete="SET NULL"), nullable=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "game_id", name="uq_user_library_game"),
    )

    user = relationship("User", back_populates="library_items")
    game = relationship("Game", back_populates="library_items")
    purchase = relationship("Purchase", back_populates="library_item")

    def __repr__(self):
        return f"<UserGameLibrary(id={self.id}, user_id={self.user_id}, game_id={self.game_id})>"
