from worker.nba_client import parse_clock_seconds


def is_tense_nba(state: dict) -> bool:
    """4th quarter, ≤5:00 remaining, score differential ≤6."""
    if state["period"] != 4:
        return False
    seconds_left = parse_clock_seconds(state["clock"])
    diff = abs(state["home_score"] - state["away_score"])
    return seconds_left <= 300 and diff <= 6


def is_tense_mlb(linescore: dict) -> bool:
    """8th inning or later, run differential ≤2."""
    inning = linescore.get("currentInning", 0)
    home_runs = linescore.get("teams", {}).get("home", {}).get("runs", 0)
    away_runs = linescore.get("teams", {}).get("away", {}).get("runs", 0)
    diff = abs(home_runs - away_runs)
    return inning >= 8 and diff <= 2
