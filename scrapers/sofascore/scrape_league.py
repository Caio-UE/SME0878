"""Coleta estatisticas de jogadores no SofaScore ao longo do historico de uma liga.

Este e o scraper principal do lado do SofaScore. Ele foi usado para montar a base das
temporadas da Bundesliga que alimenta a analise exploratoria e a modelagem preditiva.
A partir do identificador da liga, o script percorre as temporadas escolhidas, lista os
times de cada temporada, o elenco de cada time e, para cada jogador, baixa o bloco de
estatisticas daquela competicao e temporada, junto com o valor de mercado proposto pela
plataforma.

Uso:
    python scrape_league.py <ut_id> [--seasons N | --all | --season SID] [-o saida.json]

Argumentos:
    ut_id          identificador da liga no SofaScore, o uniqueTournament id que aparece
                   na URL, por exemplo 35 em ".../bundesliga/35"
    --seasons N    coleta as N temporadas mais recentes (padrao 5)
    --all          coleta todas as temporadas disponiveis
    --season SID   coleta apenas uma temporada especifica pelo seu id
    -o             caminho de saida (padrao data/output/league_<ut>_history.json)

Exemplos:
    python scrape_league.py 35                  # ultimas 5 temporadas da Bundesliga
    python scrape_league.py 35 --seasons 3
    python scrape_league.py 35 --season 77333   # uma temporada especifica
    python scrape_league.py 17 --all -o data/output/pl_history.json

Observacao importante: o elenco vem da lista atual de jogadores de cada time. Atletas que
jogaram em temporadas passadas mas ja deixaram o clube podem nao aparecer. As estatisticas
retornadas continuam corretas, apenas ficam limitadas a quem esta no elenco de hoje.
"""
import argparse
import json
import sys
import time
from pathlib import Path
from curl_cffi import requests

# Endereco base da API interna do SofaScore. Nao e uma API oficial e pode mudar sem aviso.
BASE = "https://api.sofascore.com/api/v1"
DELAY = 0.25                       # pausa em segundos entre requisicoes, para nao sobrecarregar o site
OUTPUT_DIR = Path("data/output")


def default_output_path(ut_id):
    return OUTPUT_DIR / f"league_{ut_id}_history.json"


def get(url, retries=3):
    """Busca uma URL da API e devolve o JSON, com novas tentativas em caso de falha.

    Usa curl_cffi com impersonate=chrome para se passar por um navegador real, o que reduz
    bloqueios. Em erro temporario, espera um tempo crescente e tenta de novo. Retorna None
    quando o recurso nao existe (404) ou quando todas as tentativas falham.
    """
    for i in range(retries):
        try:
            r = requests.get(url, impersonate="chrome")
            if r.status_code == 200:
                return r.json()
            if r.status_code == 404:
                return None
        except Exception:
            pass
        time.sleep(1 + i)          # espera 1s, depois 2s, depois 3s antes de repetir
    return None


def pick_seasons(ut_id, args):
    """Lista as temporadas da liga e devolve apenas as que o usuario pediu."""
    data = get(f"{BASE}/unique-tournament/{ut_id}/seasons")
    if not data:
        sys.exit(f"Nao foi possivel listar as temporadas da liga ut={ut_id}")
    seasons = data["seasons"]  # a API devolve da mais recente para a mais antiga
    if args.season:
        return [s for s in seasons if s["id"] == args.season]
    if args.all:
        return seasons
    return seasons[: args.seasons]


def scrape_season(ut_id, season):
    """Coleta todos os times, elencos e estatisticas de jogador de uma temporada.

    Percorre tres niveis encadeados: os times da temporada, os jogadores de cada time e,
    para cada jogador, o bloco de estatisticas naquela competicao e temporada. Jogadores
    sem estatisticas registradas sao ignorados.
    """
    sid = season["id"]
    # Nivel 1: os times que disputaram a temporada.
    teams_resp = get(f"{BASE}/unique-tournament/{ut_id}/season/{sid}/teams")
    teams = teams_resp.get("teams", []) if teams_resp else []
    out_teams = []
    for ti, team in enumerate(teams, 1):
        tid = team["id"]
        print(f"    [{ti}/{len(teams)}] {team['name']}")
        # Nivel 2: o elenco atual do time.
        squad_resp = get(f"{BASE}/team/{tid}/players")
        squad = squad_resp.get("players", []) if squad_resp else []
        players = []
        for entry in squad:
            p = entry["player"]
            pid = p["id"]
            # Nivel 3: as estatisticas do jogador naquela liga e temporada.
            stats_resp = get(
                f"{BASE}/player/{pid}/unique-tournament/{ut_id}/season/{sid}/statistics/overall"
            )
            stats = stats_resp.get("statistics") if stats_resp else None
            if stats is None:
                time.sleep(DELAY)
                continue
            mv_raw = p.get("proposedMarketValueRaw") or {}
            players.append({
                "id": pid,
                "name": p["name"],
                "position": p.get("position"),
                "shirtNumber": p.get("shirtNumber"),
                "marketValue": mv_raw.get("value"),
                "marketValueCurrency": mv_raw.get("currency"),
                "statistics": stats,
            })
            time.sleep(DELAY)
        out_teams.append({"id": tid, "name": team["name"], "players": players})
    return out_teams


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ut_id", type=int)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--seasons", type=int, default=5)
    g.add_argument("--all", action="store_true")
    g.add_argument("--season", type=int)
    ap.add_argument("-o", "--output")
    args = ap.parse_args()

    tourn = get(f"{BASE}/unique-tournament/{args.ut_id}")
    tname = tourn["uniqueTournament"]["name"] if tourn else f"ut{args.ut_id}"
    seasons = pick_seasons(args.ut_id, args)
    print(f"{tname} | {len(seasons)} temporada(s): {[s['name'] for s in seasons]}")

    t0 = time.time()
    result = {
        "tournament": tname,
        "uniqueTournamentId": args.ut_id,
        "seasons": [],
    }
    for si, s in enumerate(seasons, 1):
        print(f"\n=== [{si}/{len(seasons)}] {s['name']} (id={s['id']}) ===")
        teams = scrape_season(args.ut_id, s)
        result["seasons"].append({
            "id": s["id"],
            "name": s["name"],
            "year": s.get("year"),
            "teams": teams,
        })

    out = Path(args.output) if args.output else default_output_path(args.ut_id)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    elapsed = time.time() - t0
    total_players = sum(len(t["players"]) for s in result["seasons"] for t in s["teams"])
    print(f"\nSalvo {out} | Temporadas: {len(result['seasons'])} | Registros jogador-temporada: {total_players} | Tempo: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
