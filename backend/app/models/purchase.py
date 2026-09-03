from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    game_id = Column(Integer, ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    status = Column(String(50), default="COMPLETED", nullable=False)  # COMPLETED, REFUNDED, PENDING
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="purchases")
    game = relationship("Game", back_populates="purchases")
    library_item = relationship("UserGameLibrary", back_populates="purchase", uselist=False)

    def __repr__(self):
        return f"<Purchase(id={self.id}, user_id={self.user_id}, game_id={self.game_id}, price={self.price})>"
