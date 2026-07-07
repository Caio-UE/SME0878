"""Primeiro nivel do scraping: as competicoes.

Recebe o arquivo semente com os enderecos das competicoes e visita a pagina inicial
de cada uma para completar os metadados: nome da liga, pais e temporada corrente.
A saida alimenta o spider de clubes.
"""
from __future__ import annotations

from tfscrap.spiders.base import BaseSpider
from tfscrap.utils import normalize_href


class CompetitionsSpider(BaseSpider):
    """Completa cada competicao da semente com nome, pais e temporada."""

    name = "competitions"

    def parse(self, response, **kwargs):
        parent = response.meta.get("parent") or {}
        name = response.css("h1::text").get(default="").strip()
        # O pais aparece como o primeiro link da trilha de navegacao (breadcrumb),
        # com a bandeira como alternativa quando o link nao esta presente.
        country = (
            response.css(".data-header__club a::text").get()
            or response.css("img.data-header__box__flag::attr(alt)").get()
            or ""
        ).strip()
        season = response.css("select[name=saison_id] option[selected]::attr(value)").get()
        href = normalize_href(parent.get("href")) or normalize_href(response.url)
        yield {
            "type": "competition",
            "name": name or None,
            "country": country or None,
            "season": season,
            "href": href,
        }
