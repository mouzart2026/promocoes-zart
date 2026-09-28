"""Módulo para geração de links de afiliado."""

import logging
import os
import warnings
from typing import Any


class PlataformaNaoImplementada(Exception):
    """Exceção para plataformas não suportadas."""

    pass


logger = logging.getLogger(__name__)


def gerar_link_afiliado(item: dict[str, Any], plataforma: str) -> str:
    """
    Gera link de afiliado para o item na plataforma especificada.

    Args:
        item: Dicionário com dados do produto (deve conter 'link').
        plataforma: Nome da plataforma ("mercado_livre", "shopee" ou "amazon").

    Returns:
        Link formatado como afiliado.

    Raises:
        PlataformaNaoImplementada: Se a plataforma não for suportada.
    """
    link_original: str = item.get("link", "")

    if plataforma == "mercado_livre":
        return _gerar_link_mercado_livre(link_original)

    if plataforma == "shopee":
        # Shopee já retorna o link com tracking no campo offerLink da API
        return link_original

    if plataforma == "amazon":
        raise PlataformaNaoImplementada(
            "Geração de link de afiliado para Amazon ainda não implementada"
        )

    raise PlataformaNaoImplementada(f"Plataforma '{plataforma}' não suportada")


def _gerar_link_mercado_livre(link: str) -> str:
    """
    Formata link do Mercado Livre com tags de afiliado.

    Parâmetros:
    - matt_tool={ML_AFFILIATE_TAG} (obrigatório)
    - matt_word={ML_AFFILIATE_WORD} (opcional)
    """
    tag = os.getenv("ML_AFFILIATE_TAG", "").strip()
    word = os.getenv("ML_AFFILIATE_WORD", "").strip()

    if not tag:
        warnings.warn(
            "ML_AFFILIATE_TAG não configurada. Retornando link original sem tag de afiliado.",
            UserWarning,
            stacklevel=2,
        )
        return link

    params = [f"matt_tool={tag}"]
    if word:
        params.append(f"matt_word={word}")
    else:
        logger.warning("ML_AFFILIATE_WORD não configurada. Enviando apenas matt_tool.")

    separador = "&" if "?" in link else "?"
    return f"{link}{separador}{'&'.join(params)}"
