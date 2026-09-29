"""Pacote afiliados - Automação de marketing de afiliados."""

from afiliados import (
    armazenamento,
    http_utils,
    links,
    mensagens,
    mercado_livre,
    mercado_livre_parser,
    orquestrador,
    shopee,
    whatsapp,
)

__all__ = [
    "mercado_livre",
    "mercado_livre_parser",
    "shopee",
    "links",
    "armazenamento",
    "orquestrador",
    "http_utils",
    "whatsapp",
    "mensagens",
]
