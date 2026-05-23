from nba_api.live.nba.endpoints import scoreboard, boxscore


def get_live_games() -> list[dict]:
    """Return a list of live game summaries from today's scoreboard."""
    board = scoreboard.ScoreBoard()
    games = board.games.get_dict()

    live = []
    for game in games:
        # gameStatusText is "Q4 2:34" for live, "Final" for done, future tip time if not started
        status = game.get("gameStatus")  # 1=scheduled, 2=live, 3=final
        if status == 2:
            live.append(game)
    return live


def get_game_state(game_id: str) -> dict | None:
    """Fetch the live box score for a game and return a simplified state dict."""
    try:
        box = boxscore.BoxScore(game_id=game_id)
        game = box.game.get_dict()
        period = game.get("period", 0)
        clock = game.get("gameClock", "PT00M00.00S")  # ISO 8601 duration e.g. "PT03M45.00S"
        home_score = game["homeTeam"]["score"]
        away_score = game["awayTeam"]["score"]
        home_name = game["homeTeam"]["teamTricode"]
        away_name = game["awayTeam"]["teamTricode"]
        return {
            "game_id": game_id,
            "period": period,
            "clock": clock,
            "home_score": home_score,
            "away_score": away_score,
            "home_name": home_name,
            "away_name": away_name,
        }
    except Exception:
        return None


def parse_clock_seconds(clock: str) -> float:
    """Convert ISO 8601 game clock string like 'PT03M45.00S' to total seconds."""
    # Strip PT prefix, split on M
    clock = clock.replace("PT", "")
    if "M" in clock:
        minutes, seconds = clock.split("M")
        seconds = seconds.rstrip("S")
        return float(minutes) * 60 + float(seconds)
    return 0.0
