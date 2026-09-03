from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import relationship
from app.database.base import Base

class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=False)
    genre = Column(String(50), index=True, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    rating = Column(Float, nullable=False, default=0.0)
    duration_hours = Column(Float, nullable=False, default=0.0)
    developer = Column(String(150), nullable=False)
    release_date = Column(String(50), nullable=False)
    image_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    cart_items = relationship("CartItem", back_populates="game", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="game")
    library_items = relationship("UserGameLibrary", back_populates="game")

    def __repr__(self):
        return f"<Game(id={self.id}, title='{self.title}', price={self.price})>"
