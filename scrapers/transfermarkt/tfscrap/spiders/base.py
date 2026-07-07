"""Classe base compartilhada por todos os spiders do Transfermarkt.

O scraping do Transfermarkt e feito em camadas: primeiro as competicoes, depois
os clubes de cada competicao, depois os jogadores de cada clube e por fim os dados
de cada jogador. Para ligar essas camadas, cada spider recebe do anterior um arquivo
no formato JSONL, em que cada linha e uma entidade ja coletada. Esta base le esse
arquivo, ou a entrada padrao quando nenhum arquivo e informado, e dispara uma
requisicao para a pagina de cada item. Concentrar essa logica aqui evita repetir a
leitura da entrada e a montagem dos cabecalhos HTTP em todos os spiders.
"""
from __future__ import annotations

import json
import sys
from collections.abc import Iterator
from typing import Any

import scrapy

DEFAULT_BASE_URL = "https://www.transfermarkt.com"
DEFAULT_UA = (
    "Mozilla/5.0 (tfscrap/0.1 academic-project SME0829 ICMC-USP; +mailto:contact@example.com)"
)
DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_UA,
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


class BaseSpider(scrapy.Spider):
    """Le itens JSONL da entrada e transforma cada um em uma requisicao HTTP."""

    name = "base"

    def __init__(
        self,
        parents: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        season: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.parents_file = parents
        self.base_url = base_url.rstrip("/")
        self.season = season

    def read_parents(self) -> Iterator[dict]:
        stream = open(self.parents_file) if self.parents_file else sys.stdin
        try:
            for line in stream:
                line = line.strip()
                if not line:
                    continue
                yield json.loads(line)
        finally:
            if self.parents_file:
                stream.close()

    def start_requests(self) -> Iterator[scrapy.Request]:
        for parent in self.read_parents():
            href = parent.get("href")
            if not href:
                continue
            # href guardado no item costuma ser um caminho relativo (comeca com "/");
            # nesse caso completamos com o dominio base para formar a URL absoluta.
            url = self.base_url + href if href.startswith("/") else href
            yield scrapy.Request(
                url=url,
                headers=DEFAULT_HEADERS,
                meta={"parent": parent},
                callback=self.parse,
            )
