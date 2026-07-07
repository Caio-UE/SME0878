"""Enriquece o dataset final com posicao e idade dos jogadores, a partir do SofaScore.

O dataset de estatisticas gerado pelo scrape_league nao trazia, em formato de coluna, a
posicao e a data de nascimento de cada atleta. Como essas duas variaveis tem forte impacto
no valor de mercado, este script as recupera do endpoint de perfil do SofaScore, o /player/{id},
usando o identificador que ja existe no dataset. Para cada jogador ele obtem a posicao e a
data de nascimento, calcula a idade na abertura da temporada e grava tudo de volta no CSV.

As requisicoes sao guardadas em um cache local, entao rodar o script de novo nao refaz o
trabalho ja concluido e permite retomar de onde parou caso a coleta seja interrompida. Um
backup do CSV original e criado antes da primeira gravacao.

Uso:
    python enrich_players.py                       # usa o caminho padrao do dataset
    python enrich_players.py -c caminho/base.csv   # aponta para outro CSV
"""
import argparse
import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from curl_cffi import requests

BASE = "https://api.sofascore.com/api/v1"
# Caminho padrao do dataset final, relativo a raiz do projeto.
DEFAULT_CSV = Path("dataset_bundesliga_5seasons.csv")
# Arquivo de cache das respostas, guardado ao lado deste script.
CACHE_FILE = Path(__file__).parent / "player_meta_cache.json"
DELAY = 0.15                       # pausa entre requisicoes, em segundos

# Mapeia o codigo de posicao do SofaScore para um rotulo legivel em portugues.
POSITION_LABEL = {"F": "Atacante", "M": "Meio-campo", "D": "Defensor", "G": "Goleiro"}


def fetch_player(pid, retries=3):
    """Busca posicao e data de nascimento de um jogador pelo seu id no SofaScore.

    Retorna um dicionario com a posicao e o dateOfBirthTimestamp (um instante em segundos).
    Em caso de jogador inexistente ou falha repetida, os campos voltam como None.
    """
    for attempt in range(retries):
        try:
            r = requests.get(f"{BASE}/player/{pid}", impersonate="chrome", timeout=20)
            if r.status_code == 404:
                return {"position": None, "dobTS": None}
            r.raise_for_status()
            p = r.json()["player"]
            return {"position": p.get("position"), "dobTS": p.get("dateOfBirthTimestamp")}
        except Exception:
            if attempt == retries - 1:
                return {"position": None, "dobTS": None}
            time.sleep(1.0)


def load_cache():
    """Le o cache de respostas ja coletadas, se existir."""
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache):
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


def collect_meta(ids, cache):
    """Garante que o cache tenha posicao e nascimento de todos os ids informados.

    Salva o progresso a cada 25 novos jogadores, o que torna a coleta retomavel.
    """
    novos = 0
    for i, pid in enumerate(ids, 1):
        key = str(int(pid))
        if key in cache:
            continue
        cache[key] = fetch_player(pid)
        novos += 1
        time.sleep(DELAY)
        if novos % 25 == 0:
            save_cache(cache)
            print(f"  {i}/{len(ids)} coletados (novos nesta execucao: {novos})", flush=True)
    save_cache(cache)
    return cache


def age_at_season_start(birth_iso, season_start_year):
    """Calcula a idade do jogador na abertura da temporada, tipicamente em 1 de agosto."""
    if not birth_iso or pd.isna(season_start_year):
        return np.nan
    nascimento = date.fromisoformat(birth_iso)
    referencia = date(int(season_start_year), 8, 1)
    return round((referencia - nascimento).days / 365.25, 1)


def main():
    ap = argparse.ArgumentParser(description="Adiciona posicao e idade ao dataset final.")
    ap.add_argument("-c", "--csv", type=Path, default=DEFAULT_CSV, help="caminho do CSV a enriquecer")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    ids = sorted(df["player_sofa_id"].dropna().astype(int).unique().tolist())
    print(f"Jogadores unicos no dataset: {len(ids)}")

    cache = load_cache()
    print(f"Ja presentes no cache: {len(cache)}")
    cache = collect_meta(ids, cache)

    # Converte cada resposta do cache em posicao e data de nascimento por jogador.
    def pos_of(pid):
        v = cache.get(str(int(pid))) if pd.notna(pid) else None
        return v.get("position") if v else None

    def dob_of(pid):
        v = cache.get(str(int(pid))) if pd.notna(pid) else None
        if not v or not v.get("dobTS"):
            return None
        # O timestamp esta em UTC; convertemos para uma data no formato ISO.
        return datetime.fromtimestamp(v["dobTS"], tz=timezone.utc).date().isoformat()

    df["position"] = df["player_sofa_id"].map(pos_of)
    df["position_label"] = df["position"].map(POSITION_LABEL)
    df["birth_date"] = df["player_sofa_id"].map(dob_of)

    # Extrai o ano inicial da temporada do texto "Bundesliga 22/23" e calcula a idade.
    ano_inicial = df["season"].str.extract(r"(\d{2})/\d{2}")[0].astype(float) + 2000
    df["age"] = [age_at_season_start(bd, ano) for bd, ano in zip(df["birth_date"], ano_inicial)]

    # Cria um backup do CSV original apenas na primeira vez.
    backup = args.csv.with_name(args.csv.stem + "_backup.csv")
    if not backup.exists():
        backup.write_bytes(args.csv.read_bytes())
        print(f"Backup criado: {backup.name}")

    df.to_csv(args.csv, index=False, encoding="utf-8")
    print(f"Dataset atualizado: {args.csv.name} | linhas: {len(df)}")
    print(f"Posicao preenchida: {df['position'].notna().mean() * 100:.0f} por cento")
    print(f"Idade preenchida:   {df['age'].notna().mean() * 100:.0f} por cento")


if __name__ == "__main__":
    main()
