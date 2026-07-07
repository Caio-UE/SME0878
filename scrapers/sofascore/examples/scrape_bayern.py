"""Exemplo: coleta as estatisticas do elenco inteiro do Bayern na Bundesliga 25/26.

Recorta o scraper para um unico time e uma unica temporada, com os identificadores fixos no
inicio do arquivo. Serve de receita para obter uma visao comparativa dos jogadores de um
mesmo clube sem rodar a liga inteira.
"""
import json
import time
from pathlib import Path
from curl_cffi import requests

TEAM_ID = 2672
UT_ID = 35          # Bundesliga
SEASON_ID = 77333   # Bundesliga 25/26
BASE = "https://api.sofascore.com/api/v1"
OUT = Path("data/output/bayern_bundesliga_25_26.json")


def get(url):
    r = requests.get(url, impersonate="chrome")
    r.raise_for_status()
    return r.json()


def main():
    t0 = time.time()
    team_info = get(f"{BASE}/team/{TEAM_ID}")["team"]
    squad = get(f"{BASE}/team/{TEAM_ID}/players").get("players", [])
    print(f"Elenco: {len(squad)} jogadores")

    result = {
        "team": {"id": team_info["id"], "name": team_info["name"]},
        "tournament": "Bundesliga",
        "season": "25/26",
        "seasonId": SEASON_ID,
        "players": [],
    }

    for i, entry in enumerate(squad, 1):
        p = entry["player"]
        pid = p["id"]
        url = f"{BASE}/player/{pid}/unique-tournament/{UT_ID}/season/{SEASON_ID}/statistics/overall"
        try:
            stats = get(url).get("statistics")
        except Exception as e:
            stats = {"error": str(e)}
        result["players"].append({
            "id": pid,
            "name": p["name"],
            "position": p.get("position"),
            "shirtNumber": p.get("shirtNumber"),
            "statistics": stats,
        })
        print(f"  [{i}/{len(squad)}] {p['name']}")
        time.sleep(0.3)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\nSalvo {OUT} em {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
