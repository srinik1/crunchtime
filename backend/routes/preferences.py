from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import User, UserPreference
from backend.schemas import PreferenceRequest

router = APIRouter(prefix="/users", tags=["preferences"])


@router.get("/{user_id}/preferences")
def get_preferences(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user_id, "sports": [p.sport for p in user.preferences]}


@router.put("/{user_id}/preferences")
def update_preferences(user_id: int, req: PreferenceRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(UserPreference).filter(UserPreference.user_id == user_id).delete()
    for sport in req.sports:
        db.add(UserPreference(user_id=user_id, sport=sport))
    db.commit()

    return {"user_id": user_id, "sports": req.sports}
