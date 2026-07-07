"""Exemplo: coleta o historico completo de estatisticas do Harry Kane.

Serve como receita minima do uso da API do SofaScore para um unico jogador. Busca o perfil
e, em seguida, percorre todas as competicoes e temporadas em que o jogador tem estatisticas,
salvando tudo em um JSON. E util como referencia para entender a estrutura dos dados antes
de rodar o scraper de liga inteiro.
"""
import json
import time
from pathlib import Path
from curl_cffi import requests

PLAYER_ID = 108579
BASE = "https://api.sofascore.com/api/v1"
OUT = Path("data/output/kane_stats.json")


def get(url):
    r = requests.get(url, impersonate="chrome")
    r.raise_for_status()
    return r.json()


def main():
    player = get(f"{BASE}/player/{PLAYER_ID}")["player"]
    seasons_data = get(f"{BASE}/player/{PLAYER_ID}/statistics/seasons")

    result = {
        "player": {
            "id": player["id"],
            "name": player["name"],
            "team": player.get("team", {}).get("name"),
            "position": player.get("position"),
            "shirtNumber": player.get("shirtNumber"),
            "dateOfBirthTimestamp": player.get("dateOfBirthTimestamp"),
        },
        "tournaments": [],
    }

    for entry in seasons_data.get("uniqueTournamentSeasons", []):
        ut = entry["uniqueTournament"]
        ut_id = ut["id"]
        tournament_block = {
            "uniqueTournamentId": ut_id,
            "name": ut["name"],
            "seasons": [],
        }
        for season in entry.get("seasons", []):
            s_id = season["id"]
            url = f"{BASE}/player/{PLAYER_ID}/unique-tournament/{ut_id}/season/{s_id}/statistics/overall"
            try:
                stats = get(url).get("statistics")
            except Exception as e:
                stats = {"error": str(e)}
            tournament_block["seasons"].append(
                {"id": s_id, "name": season["name"], "year": season["year"], "statistics": stats}
            )
            time.sleep(0.3)
        result["tournaments"].append(tournament_block)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved {OUT}")
    print(f"Competitions: {len(result['tournaments'])}")
    print(f"Seasons total: {sum(len(t['seasons']) for t in result['tournaments'])}")


if __name__ == "__main__":
    main()
