"""Módulo para integração com a API do Mercado Livre."""

import logging
import os
import time
from typing import Any

import requests

from afiliados.http_utils import retry_com_backoff

logger = logging.getLogger(__name__)


class MercadoLivreError(Exception):
    """Exceção base para erros do módulo Mercado Livre."""

    pass


class ErroRedeMercadoLivre(MercadoLivreError):
    """Erro de rede ao consultar a API do Mercado Livre."""

    pass


class ErroRespostaMercadoLivre(MercadoLivreError):
    """Erro na resposta da API do Mercado Livre."""

    pass


class ErroCredenciaisMercadoLivre(MercadoLivreError):
    """Credenciais do Mercado Livre não configuradas."""

    pass


_TOKEN_CACHE: dict[str, Any] = {}


@retry_com_backoff(max_tentativas=3, backoff_base=1.0)
def _requisicao_token() -> dict[str, Any]:
    """
    Faz requisição para obter token OAuth com retry.

    Returns:
        Dicionário com access_token e expires_in.

    Raises:
        ErroCredenciaisMercadoLivre: Se credenciais não configuradas.
        ErroRedeMercadoLivre: Falha de conexão.
        ErroRespostaMercadoLivre: Erro HTTP ou resposta inválida.
    """
    client_id = os.getenv("ML_CLIENT_ID", "").strip()
    client_secret = os.getenv("ML_CLIENT_SECRET", "").strip()

    if not client_id or not client_secret:
        raise ErroCredenciaisMercadoLivre(
            "ML_CLIENT_ID e ML_CLIENT_SECRET devem estar definidos no ambiente"
        )

    url = "https://api.mercadolibre.com/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    try:
        resposta = requests.post(url, data=data, headers=headers, timeout=10)
        resposta.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ErroRedeMercadoLivre("Timeout ao obter token OAuth") from exc
    except requests.exceptions.ConnectionError as exc:
        raise ErroRedeMercadoLivre("Erro de conexão ao obter token OAuth") from exc
    except requests.exceptions.HTTPError as exc:
        # Loga corpo da resposta sem expor o secret
        corpo = exc.response.text if exc.response is not None else "sem resposta"
        logger.error(
            "Erro HTTP ao obter token OAuth: status=%d, resposta=%s",
            exc.response.status_code if exc.response is not None else -1,
            corpo,
        )
        raise ErroRespostaMercadoLivre(
            f"Erro HTTP ao obter token: {exc.response.status_code} - {corpo}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ErroRedeMercadoLivre(f"Erro na requisição de token: {exc}") from exc

    try:
        dados: dict[str, Any] = resposta.json()
    except ValueError as exc:
        logger.error("Resposta de token não é JSON válido: %s", resposta.text)
        raise ErroRespostaMercadoLivre("Resposta de token não é JSON válido") from exc

    access_token: str | None = dados.get("access_token")
    expires_in: int = dados.get("expires_in", 0)

    if not access_token:
        raise ErroRespostaMercadoLivre("Token de acesso não retornado pela API")

    return {"access_token": access_token, "expires_in": expires_in}


def _obter_token() -> str:
    """
    Obtém access token via OAuth client_credentials com cache em memória.

    Returns:
        Access token válido.

    Raises:
        ErroCredenciaisMercadoLivre: Se ML_CLIENT_ID ou ML_CLIENT_SECRET não estiverem definidos.
        ErroRedeMercadoLivre: Em caso de falha de conexão.
        ErroRespostaMercadoLivre: Se a API retornar erro.
    """
    agora = time.time()

    if _TOKEN_CACHE.get("access_token") and _TOKEN_CACHE.get("expires_at", 0) > agora + 60:
        logger.debug("Usando token OAuth em cache")
        return str(_TOKEN_CACHE["access_token"])

    logger.info("Obtendo novo token OAuth do Mercado Livre")
    dados = _requisicao_token()

    _TOKEN_CACHE["access_token"] = dados["access_token"]
    _TOKEN_CACHE["expires_at"] = agora + dados["expires_in"]

    return str(_TOKEN_CACHE["access_token"])


@retry_com_backoff(max_tentativas=3, backoff_base=1.0)
def _requisicao_busca(token: str, termo: str, limite: int) -> dict[str, Any]:
    """
    Faz requisição de busca com retry.

    Args:
        token: Access token válido.
        termo: Termo de busca.
        limite: Limite de resultados.

    Returns:
        JSON da resposta.

    Raises:
        ErroRedeMercadoLivre: Falha de conexão.
        ErroRespostaMercadoLivre: Erro HTTP ou resposta inválida.
    """
    url = "https://api.mercadolibre.com/sites/MLB/search"
    params: dict[str, str | int] = {"q": termo, "limit": limite}
    headers = {"Authorization": f"Bearer {token}"}

    try:
        resposta = requests.get(url, params=params, headers=headers, timeout=10)
        resposta.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ErroRedeMercadoLivre("Timeout ao consultar API do Mercado Livre") from exc
    except requests.exceptions.ConnectionError as exc:
        raise ErroRedeMercadoLivre("Erro de conexão com a API do Mercado Livre") from exc
    except requests.exceptions.HTTPError as exc:
        if exc.response.status_code == 401:
            _TOKEN_CACHE.clear()
            raise ErroRespostaMercadoLivre("Token expirado ou inválido, cache limpo") from exc
        # Loga corpo da resposta 403/outros erros sem expor token
        corpo = exc.response.text if exc.response is not None else "sem resposta"
        logger.error(
            "Erro HTTP na busca: status=%d, url=%s, resposta=%s",
            exc.response.status_code if exc.response is not None else -1,
            exc.response.url if exc.response is not None else "desconhecida",
            corpo,
        )
        raise ErroRespostaMercadoLivre(
            f"Erro HTTP da API: {exc.response.status_code} - {corpo}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ErroRedeMercadoLivre(f"Erro na requisição: {exc}") from exc

    try:
        dados: dict[str, Any] = resposta.json()
    except ValueError as exc:
        raise ErroRespostaMercadoLivre("Resposta não é JSON válido") from exc

    return dados


def buscar_produtos(termo: str, limite: int = 20) -> list[dict]:
    """
    Busca produtos na API pública do Mercado Livre.

    Args:
        termo: Termo de busca.
        limite: Número máximo de resultados (padrão: 20).

    Returns:
        Lista de dicionários com id, titulo, preco e link.

    Raises:
        ErroCredenciaisMercadoLivre: Se credenciais não configuradas.
        ErroRedeMercadoLivre: Em caso de falha de conexão ou timeout.
        ErroRespostaMercadoLivre: Se a API retornar erro ou formato inesperado.
    """
    logger.info("Buscando produtos no Mercado Livre: termo='%s', limite=%d", termo, limite)

    token = _obter_token()
    dados = _requisicao_busca(token, termo, limite)

    resultados = dados.get("results", [])
    if not isinstance(resultados, list):
        raise ErroRespostaMercadoLivre("Campo 'results' não é uma lista")

    produtos = []
    for item in resultados:
        produto = {
            "id": item.get("id"),
            "titulo": item.get("title"),
            "preco": item.get("price"),
            "link": item.get("permalink"),
        }
        if all(produto.values()):
            produtos.append(produto)

    logger.info("Encontrados %d produtos válidos no Mercado Livre", len(produtos))
    return produtos
