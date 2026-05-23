import asyncio
import datetime

from worker.mlb_client import get_live_game_ids, get_linescore
from worker.nba_client import get_live_games, get_game_state
from worker.rules import is_tense_mlb, is_tense_nba

NORMAL_INTERVAL = 60   # seconds between polls when nothing is tense
TENSE_INTERVAL = 15    # seconds between polls when at least one game is tense


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


async def check_mlb(tense_games: set) -> bool:
    """Poll all live MLB games. Returns True if any game is currently tense."""
    any_tense = False
    try:
        game_ids = get_live_game_ids()
    except Exception as e:
        log(f"MLB schedule fetch failed: {e}")
        return False

    for game_pk in game_ids:
        try:
            linescore = get_linescore(game_pk)
        except Exception as e:
            log(f"MLB linescore fetch failed for {game_pk}: {e}")
            continue

        if linescore is None:
            continue

        key = f"mlb:{game_pk}"
        tense = is_tense_mlb(linescore)
        inning = linescore.get("currentInning", "?")
        inning_half = linescore.get("inningHalf", "")
        home = linescore.get("teams", {}).get("home", {})
        away = linescore.get("teams", {}).get("away", {})
        score_str = f"{away.get('runs', 0)}-{home.get('runs', 0)}"

        if tense and key not in tense_games:
            log(f"TENSE MLB {game_pk} | Inning: {inning_half} {inning} | Score: {score_str}")
            tense_games.add(key)
        elif not tense and key in tense_games:
            log(f"CALM  MLB {game_pk} | Inning: {inning_half} {inning} | Score: {score_str}")
            tense_games.discard(key)

        if tense:
            any_tense = True

    return any_tense


async def check_nba(tense_games: set) -> bool:
    """Poll all live NBA games. Returns True if any game is currently tense."""
    any_tense = False
    try:
        live_games = get_live_games()
    except Exception as e:
        log(f"NBA scoreboard fetch failed: {e}")
        return False

    for game_summary in live_games:
        game_id = game_summary["gameId"]
        state = get_game_state(game_id)
        if state is None:
            continue

        key = f"nba:{game_id}"
        tense = is_tense_nba(state)
        score_str = f"{state['away_name']} {state['away_score']}-{state['home_score']} {state['home_name']}"
        clock = state["clock"].replace("PT", "").replace("M", ":").rstrip("S")

        if tense and key not in tense_games:
            log(f"TENSE NBA {game_id} | Q{state['period']} {clock} | {score_str}")
            tense_games.add(key)
        elif not tense and key in tense_games:
            log(f"CALM  NBA {game_id} | Q{state['period']} {clock} | {score_str}")
            tense_games.discard(key)

        if tense:
            any_tense = True

    return any_tense


async def polling_loop():
    tense_games: set = set()
    log("CrunchTime worker started. Polling for live games...")

    while True:
        mlb_tense, nba_tense = await asyncio.gather(
            check_mlb(tense_games),
            check_nba(tense_games),
        )

        any_tense = mlb_tense or nba_tense
        interval = TENSE_INTERVAL if any_tense else NORMAL_INTERVAL
        log(f"Poll complete. Next poll in {interval}s. Tense games: {tense_games or 'none'}")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(polling_loop())
