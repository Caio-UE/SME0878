"""Exemplo: filtra as estatisticas do Kane para manter apenas a Bundesliga.

Mostra um passo simples de pos-processamento sobre o JSON gerado pelo scrape_kane, isolando
uma unica competicao. Serve de modelo para recortar os dados por liga antes de analisar.
"""
import argparse
import json
from pathlib import Path

DEFAULT_INPUT = Path("data/reference/kane_stats.json")
DEFAULT_OUTPUT = Path("data/output/kane_bundesliga.json")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Input Kane stats JSON (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output Bundesliga-only JSON (default: {DEFAULT_OUTPUT})",
    )
    return parser.parse_args()


def filter_bundesliga(src):
    bundesliga = next(t for t in src["tournaments"] if t["name"] == "Bundesliga")
    return {
        "player": src["player"],
        "tournament": "Bundesliga",
        "uniqueTournamentId": bundesliga["uniqueTournamentId"],
        "seasons": bundesliga["seasons"],
    }


def main():
    args = parse_args()
    src = json.loads(args.input.read_text(encoding="utf-8"))
    out = filter_bundesliga(src)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"Salvo {args.output}")
    print(f"Temporadas: {len(out['seasons'])}")
    for s in out["seasons"]:
        st = s["statistics"]
        print(
            f"  {s['name']}: {st['appearances']} jogos, "
            f"{st['goals']}G {st['assists']}A, rating {st['rating']}"
        )


if __name__ == "__main__":
    main()
