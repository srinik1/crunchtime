from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    push_subscription_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    preferences = relationship("UserPreference", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("AlertHistory", back_populates="user")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sport = Column(String, nullable=False)  # "nba" or "mlb"

    user = relationship("User", back_populates="preferences")


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    game_id = Column(String, nullable=False)
    sport = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)
    fired_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    game_state_snapshot = Column(Text, nullable=True)

    user = relationship("User", back_populates="alerts")
