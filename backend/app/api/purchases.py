import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.purchase_service import (
    PurchaseService,
    InsufficientWalletError,
    GameAlreadyOwnedError,
)
from app.schemas.purchase import (
    PurchaseValidationRequest,
    PurchaseExecutionRequest,
    PurchaseSummary,
    PurchaseExecutionResult,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/purchases", tags=["Purchases"])

@router.post("/validate", response_model=PurchaseSummary)
def validate_purchase(
    payload: PurchaseValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate pre-purchase conditions:
    1. Game existence
    2. Duplicate ownership checks
    3. Total price & wallet sufficiency calculation
    """
    service = PurchaseService(db)
    try:
        summary = service.validate_purchase(
            user_id=payload.user_id,
            game_ids=payload.game_ids,
        )
        return summary
    except GameAlreadyOwnedError as e:
        logger.warning(f"Purchase validation rejected: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.warning(f"Purchase validation bad input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Purchase validation error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Validation failed: {str(e)}")

@router.post("/execute", response_model=PurchaseExecutionResult)
def execute_purchase(
    payload: PurchaseExecutionRequest,
    db: Session = Depends(get_db),
):
    """
    Execute an atomic ACID purchase transaction:
    1. Verifies wallet funds under database row lock
    2. Deducts user wallet
    3. Creates purchase records
    4. Adds games to user's library
    5. Clears items from user's cart
    6. Commits transaction atomically or rolls back completely
    """
    service = PurchaseService(db)
    try:
        result = service.execute_purchase(
            user_id=payload.user_id,
            game_ids=payload.game_ids,
        )
        return result
    except InsufficientWalletError as e:
        logger.warning(f"Purchase failed due to insufficient funds: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except GameAlreadyOwnedError as e:
        logger.warning(f"Purchase failed due to duplicate ownership: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        logger.warning(f"Purchase execution bad input: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Purchase execution transaction error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Transaction failed: {str(e)}")
