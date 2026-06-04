import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import MagicMock, patch
from worker.dispatcher import _build_message


# --- _build_message tests (pure function, no mocking needed) ---

def test_build_message_nba():
    state = {
        "home_name": "LAL", "away_name": "BOS",
        "home_score": 98, "away_score": 101,
        "clock": "PT02M30.00S",
    }
    title, body = _build_message("nba", state)
    assert "4th" in title.lower() or "close" in title.lower()
    assert "BOS" in body and "LAL" in body
    assert "101" in body and "98" in body


def test_build_message_mlb():
    state = {
        "currentInning": 9,
        "inningHalf": "Bottom",
        "teams": {"home": {"runs": 3}, "away": {"runs": 2}},
    }
    title, body = _build_message("mlb", state)
    assert "inning" in title.lower() or "tension" in title.lower()
    assert "9" in body


# --- notify() integration tests (mocked DB + Redis + push) ---

def _make_fake_user(user_id=1, email="test@example.com", sub='{"endpoint":"https://example.com"}'):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.push_subscription_json = sub
    return user


def _make_fake_pref(user_id=1, sport="nba"):
    pref = MagicMock()
    pref.user_id = user_id
    return pref


@patch("worker.dispatcher.send_push", return_value=True)
@patch("worker.dispatcher._redis")
@patch("worker.dispatcher.SessionLocal")
def test_notify_sends_push_and_sets_dedup(MockSession, mock_redis, mock_send_push):
    fake_user = _make_fake_user()
    db = MagicMock()
    MockSession.return_value = db

    # UserPreference query returns one user_id
    db.query.return_value.filter.return_value.all.side_effect = [
        [(1,)],          # UserPreference query
        [fake_user],     # User query
    ]
    mock_redis.get.return_value = None  # No dedup key → send

    from worker.dispatcher import notify
    notify("game123", "nba", "tense_game", {"home_name": "LAL", "away_name": "BOS",
                                             "home_score": 98, "away_score": 101,
                                             "clock": "PT02M30.00S"})

    mock_send_push.assert_called_once()
    mock_redis.setex.assert_called_once_with("dedup:1:game123:tense_game", 7200, "1")
    db.commit.assert_called_once()


@patch("worker.dispatcher.send_push", return_value=True)
@patch("worker.dispatcher._redis")
@patch("worker.dispatcher.SessionLocal")
def test_notify_skips_if_dedup_key_exists(MockSession, mock_redis, mock_send_push):
    fake_user = _make_fake_user()
    db = MagicMock()
    MockSession.return_value = db

    db.query.return_value.filter.return_value.all.side_effect = [
        [(1,)],
        [fake_user],
    ]
    mock_redis.get.return_value = "1"  # Dedup key already set → skip

    from worker.dispatcher import notify
    notify("game123", "nba", "tense_game", {})

    mock_send_push.assert_not_called()
    mock_redis.setex.assert_not_called()


@patch("worker.dispatcher.send_push", return_value=True)
@patch("worker.dispatcher._redis")
@patch("worker.dispatcher.SessionLocal")
def test_notify_skips_user_with_no_subscription(MockSession, mock_redis, mock_send_push):
    fake_user = _make_fake_user(sub=None)  # No push subscription
    fake_user.push_subscription_json = None
    db = MagicMock()
    MockSession.return_value = db

    db.query.return_value.filter.return_value.all.side_effect = [
        [(1,)],
        [fake_user],
    ]

    from worker.dispatcher import notify
    notify("game123", "nba", "tense_game", {})

    mock_send_push.assert_not_called()
