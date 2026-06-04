import json
import os
import redis
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import User, UserPreference, AlertHistory
from backend.push import send_push

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEDUP_TTL_SECONDS = 7200  # 2 hours — one alert per user per game per tense window

_redis = redis.from_url(REDIS_URL, decode_responses=True)


def notify(game_id: str, sport: str, alert_type: str, game_state: dict):
    """
    Called when a game transitions into a tense state.
    Finds subscribed users, deduplicates via Redis, fires push notifications,
    and writes a record to alert_history.
    """
    db: Session = SessionLocal()
    try:
        user_ids = [
            row[0]
            for row in db.query(UserPreference.user_id)
            .filter(UserPreference.sport == sport)
            .all()
        ]

        if not user_ids:
            return

        users = db.query(User).filter(User.id.in_(user_ids)).all()

        for user in users:
            if not user.push_subscription_json:
                continue

            dedup_key = f"dedup:{user.id}:{game_id}:{alert_type}"
            if _redis.get(dedup_key):
                continue  # Already alerted this user about this game

            title, body = _build_message(sport, game_state)
            success = send_push(user.push_subscription_json, title, body)

            if success:
                _redis.setex(dedup_key, DEDUP_TTL_SECONDS, "1")
                db.add(AlertHistory(
                    user_id=user.id,
                    game_id=game_id,
                    sport=sport,
                    alert_type=alert_type,
                    game_state_snapshot=json.dumps(game_state),
                ))

        db.commit()
    finally:
        db.close()


def _build_message(sport: str, game_state: dict) -> tuple[str, str]:
    if sport == "nba":
        home = game_state.get("home_name", "?")
        away = game_state.get("away_name", "?")
        hs = game_state.get("home_score", 0)
        as_ = game_state.get("away_score", 0)
        clock = game_state.get("clock", "").replace("PT", "").replace("M", ":").rstrip("S")
        return (
            "Close game in the 4th!",
            f"{away} {as_} - {hs} {home} | Q4 {clock} remaining",
        )
    else:
        inning = game_state.get("currentInning", "?")
        half = game_state.get("inningHalf", "")
        home_runs = game_state.get("teams", {}).get("home", {}).get("runs", 0)
        away_runs = game_state.get("teams", {}).get("away", {}).get("runs", 0)
        return (
            "Late-inning tension!",
            f"{half} {inning} | Score: {away_runs}–{home_runs}",
        )
