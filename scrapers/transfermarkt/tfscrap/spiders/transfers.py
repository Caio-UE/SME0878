"""Historico de transferencias de cada jogador.

Diferente dos spiders que leem HTML, este consome uma API interna em JSON do proprio
Transfermarkt (ceapi). Para cada jogador, gera uma linha por transferencia com a data,
a temporada, os clubes de origem e destino, o valor de mercado na epoca e a taxa paga
na negociacao. A comparacao entre valor de mercado e taxa paga e o que permite calcular
o agio de uma transferencia.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator

import scrapy

from tfscrap.spiders.base import DEFAULT_HEADERS, BaseSpider
from tfscrap.utils import normalize_href, parse_market_value, parse_tm_date

_PLAYER_ID_RE = re.compile(r"/spieler/(\d+)")


class TransfersSpider(BaseSpider):
    """Le o historico de transferencias da API interna e gera uma linha por transferencia."""

    name = "transfers"

    def api_url_for(self, parent: dict) -> str | None:
        href = parent.get("href") or ""
        m = _PLAYER_ID_RE.search(href)
        if not m:
            return None
        return f"{self.base_url}/ceapi/transferHistory/list/{m.group(1)}"

    def start_requests(self) -> Iterator[scrapy.Request]:
        for parent in self.read_parents():
            url = self.api_url_for(parent)
            if not url:
                continue
            yield scrapy.Request(
                url=url,
                headers={**DEFAULT_HEADERS, "Accept": "application/json"},
                meta={"parent": parent},
                callback=self.parse,
            )

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        player_href = normalize_href(parent.get("href"))
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return
        for t in data.get("transfers", []):
            yield {
                "type": "transfer",
                "player_href": player_href,
                "date": parse_tm_date(t.get("dateUnformatted") or t.get("date")),
                "season": t.get("season"),
                "from_club": (t.get("from") or {}).get("clubName"),
                "to_club": (t.get("to") or {}).get("clubName"),
                "market_value": parse_market_value(t.get("marketValue")),
                "fee": parse_market_value(t.get("fee")),
            }
