from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserRead, WalletTopupRequest

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve profile and current wallet balance for a user."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

@router.post("/{user_id}/wallet/topup", response_model=UserRead)
def topup_wallet(user_id: int, payload: WalletTopupRequest, db: Session = Depends(get_db)):
    """Add funds to the user's wallet (useful for demonstration)."""
    if payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Topup amount must be positive.")
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    new_balance = round(user.wallet_balance + payload.amount, 2)
    user = repo.update_wallet(user_id, new_balance)
    db.commit()
    db.refresh(user)
    return user

@router.post("/{user_id}/reset", response_model=UserRead)
def reset_user(user_id: int, db: Session = Depends(get_db)):
    """Reset user state: clear library, cart, purchases, and reset wallet balance to initial ₹3,500."""
    from app.database.seed_data import reset_and_seed_database
    reset_and_seed_database(db, reset_user_data=True)
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user

