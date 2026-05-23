import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from worker.rules import is_tense_mlb, is_tense_nba


# --- MLB tests ---

def test_mlb_tense_8th_close():
    linescore = {"currentInning": 8, "teams": {"home": {"runs": 3}, "away": {"runs": 2}}}
    assert is_tense_mlb(linescore) is True

def test_mlb_tense_9th_tied():
    linescore = {"currentInning": 9, "teams": {"home": {"runs": 5}, "away": {"runs": 5}}}
    assert is_tense_mlb(linescore) is True

def test_mlb_not_tense_early_inning():
    linescore = {"currentInning": 5, "teams": {"home": {"runs": 2}, "away": {"runs": 1}}}
    assert is_tense_mlb(linescore) is False

def test_mlb_not_tense_blowout_8th():
    linescore = {"currentInning": 8, "teams": {"home": {"runs": 8}, "away": {"runs": 1}}}
    assert is_tense_mlb(linescore) is False

def test_mlb_tense_exact_2_run_diff():
    linescore = {"currentInning": 8, "teams": {"home": {"runs": 4}, "away": {"runs": 2}}}
    assert is_tense_mlb(linescore) is True

def test_mlb_not_tense_3_run_diff():
    linescore = {"currentInning": 9, "teams": {"home": {"runs": 6}, "away": {"runs": 3}}}
    assert is_tense_mlb(linescore) is False


# --- NBA tests ---

def make_nba_state(period, clock, home_score, away_score):
    return {
        "game_id": "test",
        "period": period,
        "clock": clock,
        "home_score": home_score,
        "away_score": away_score,
        "home_name": "LAL",
        "away_name": "BOS",
    }

def test_nba_tense_q4_close_late():
    state = make_nba_state(4, "PT03M00.00S", 98, 95)
    assert is_tense_nba(state) is True

def test_nba_tense_q4_tied():
    state = make_nba_state(4, "PT01M30.00S", 102, 102)
    assert is_tense_nba(state) is True

def test_nba_not_tense_q3():
    state = make_nba_state(3, "PT02M00.00S", 80, 77)
    assert is_tense_nba(state) is False

def test_nba_not_tense_q4_blowout():
    state = make_nba_state(4, "PT02M00.00S", 110, 90)
    assert is_tense_nba(state) is False

def test_nba_not_tense_q4_too_early():
    # 6:00 left in Q4, close game — not tense yet (>5:00 remaining)
    state = make_nba_state(4, "PT06M00.00S", 88, 85)
    assert is_tense_nba(state) is False

def test_nba_tense_q4_exactly_5min():
    state = make_nba_state(4, "PT05M00.00S", 90, 87)
    assert is_tense_nba(state) is True

def test_nba_not_tense_q4_diff_exactly_7():
    state = make_nba_state(4, "PT02M00.00S", 100, 93)
    assert is_tense_nba(state) is False
