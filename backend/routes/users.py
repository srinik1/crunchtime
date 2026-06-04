import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, UserPreference, AlertHistory
from backend.schemas import SignupRequest, UserResponse, AlertHistoryResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/signup", response_model=UserResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        existing.push_subscription_json = json.dumps(req.push_subscription)
        db.commit()
        db.refresh(existing)
        return existing

    user = User(
        email=req.email,
        push_subscription_json=json.dumps(req.push_subscription),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    for sport in ["nba", "mlb"]:
        db.add(UserPreference(user_id=user.id, sport=sport))
    db.commit()

    return user


@router.get("/{user_id}/alerts", response_model=list[AlertHistoryResponse])
def get_alert_history(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.alerts
