from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    push_subscription: dict[str, Any]  # The subscription object from the browser


class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PreferenceRequest(BaseModel):
    sports: list[str]  # e.g. ["nba", "mlb"]


class AlertHistoryResponse(BaseModel):
    id: int
    game_id: str
    sport: str
    alert_type: str
    fired_at: datetime

    model_config = {"from_attributes": True}
