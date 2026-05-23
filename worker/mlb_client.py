import datetime
import requests

SCHEDULE_URL = "https://statsapi.mlb.com/api/v1/schedule"
LIVE_FEED_URL = "https://statsapi.mlb.com/api/v1.1/game/{game_pk}/feed/live"


def get_live_game_ids() -> list[int]:
    today = datetime.date.today().isoformat()
    resp = requests.get(SCHEDULE_URL, params={"sportId": 1, "date": today}, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("dates"):
        return []

    live_ids = []
    for game in data["dates"][0]["games"]:
        if game["status"]["abstractGameState"] == "Live":
            live_ids.append(game["gamePk"])
    return live_ids


def get_linescore(game_pk: int) -> dict | None:
    url = LIVE_FEED_URL.format(game_pk=game_pk)
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("liveData", {}).get("linescore")
