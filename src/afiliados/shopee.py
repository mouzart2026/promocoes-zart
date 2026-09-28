"""Módulo para integração com a Shopee Affiliate Open API (GraphQL)."""

import hashlib
import logging
import os
import time
from typing import Any

import requests

from afiliados.http_utils import retry_com_backoff

logger = logging.getLogger(__name__)


class ShopeeError(Exception):
    """Exceção base para erros do módulo Shopee."""

    pass


class ErroCredenciaisShopee(ShopeeError):
    """Erro: credenciais da Shopee não configuradas ou inválidas."""

    pass


class ErroRedeShopee(ShopeeError):
    """Erro de rede ao consultar a API da Shopee."""

    pass


class ErroRespostaShopee(ShopeeError):
    """Erro na resposta da API da Shopee."""

    pass


SHOPEE_GRAPHQL_URL = "https://open-api.affiliate.shopee.com.br/graphql"


def _get_app_id() -> str:
    """Retorna SHOPEE_APP_ID do ambiente."""
    return os.getenv("SHOPEE_APP_ID", "")


def _get_app_secret() -> str:
    """Retorna SHOPEE_APP_SECRET do ambiente."""
    return os.getenv("SHOPEE_APP_SECRET", "")


def _validar_credenciais() -> None:
    """Valida se as credenciais da Shopee estão configuradas."""
    if not _get_app_id() or not _get_app_secret():
        raise ErroCredenciaisShopee(
            "SHOPEE_APP_ID e SHOPEE_APP_SECRET devem estar configuradas no .env"
        )


def _gerar_signature(app_id: str, timestamp: int, payload: str, secret: str) -> str:
    """
    Gera assinatura HMAC-SHA256 para a Shopee Affiliate API.

    Conforme documentação: SHA256(AppId + Timestamp + Payload + Secret)
    """
    message = f"{app_id}{timestamp}{payload}{secret}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _montar_payload_graphql(termo: str, limite: int) -> str:
    """
    Monta o payload GraphQL compacto (sem espaços/quebras de linha)
    para assinatura e envio.
    """
    query = (
        '{"query":"{productOfferV2('
        f'keyword:\\"{termo}\\",'
        "listType:0,"
        "sortType:5,"
        "page:1,"
        f"limit:{limite}"
        "){nodes{"
        "itemId,"
        "productName,"
        "productLink,"
        "offerLink,"
        "imageUrl,"
        "priceMin,"
        "priceMax,"
        "priceDiscountRate,"
        "sales,"
        "ratingStar,"
        "commissionRate,"
        "shopId,"
        "shopName,"
        "periodStartTime,"
        "periodEndTime"
        '}pageInfo{page,limit,hasNextPage}}}","operationName":null,"variables":{}}'
    )
    return query


def _headers(app_id: str, timestamp: int, payload: str, signature: str) -> dict:
    """Monta headers para requisição à Shopee API."""
    return {
        "Content-Type": "application/json",
        "Authorization": (
            f"SHA256 Credential={app_id}, Timestamp={timestamp}, Signature={signature}"
        ),
    }


@retry_com_backoff(max_tentativas=3, backoff_base=1.5)
def _requisicao_shopee(payload_str: str, headers: dict[str, str]) -> dict[str, Any]:
    """
    Faz requisição à Shopee API com retry.

    Args:
        payload_str: Payload GraphQL já assinado.
        headers: Headers com autorização.

    Returns:
        JSON da resposta.

    Raises:
        ErroRedeShopee: Falha de conexão ou timeout.
        ErroRespostaShopee: Erro HTTP, JSON inválido ou erro GraphQL.
    """
    try:
        resposta = requests.post(
            SHOPEE_GRAPHQL_URL,
            data=payload_str,
            headers=headers,
            timeout=15,
        )
        resposta.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ErroRedeShopee("Timeout ao consultar API da Shopee") from exc
    except requests.exceptions.ConnectionError as exc:
        raise ErroRedeShopee("Erro de conexão com a API da Shopee") from exc
    except requests.exceptions.HTTPError as exc:
        raise ErroRespostaShopee(
            f"Erro HTTP da API Shopee: {exc.response.status_code} - {exc.response.text}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ErroRedeShopee(f"Erro na requisição: {exc}") from exc

    try:
        dados: dict[str, Any] = resposta.json()
    except ValueError as exc:
        raise ErroRespostaShopee("Resposta não é JSON válido") from exc

    if "errors" in dados:
        mensagens = [e.get("message", "Erro desconhecido") for e in dados["errors"]]
        raise ErroRespostaShopee(f"Erros GraphQL: {'; '.join(mensagens)}")

    return dados


def buscar_produtos(termo: str, limite: int = 20) -> list[dict]:
    """
    Busca produtos na Shopee Affiliate Open API via GraphQL.

    Args:
        termo: Termo de busca.
        limite: Número máximo de resultados (padrão: 20).

    Returns:
        Lista de dicionários com id, titulo, preco, link (offerLink já com tracking).

    Raises:
        ErroCredenciaisShopee: Credenciais não configuradas.
        ErroRedeShopee: Falha de conexão ou timeout.
        ErroRespostaShopee: Erro HTTP, JSON inválido ou erro da API.
    """
    logger.info("Buscando produtos na Shopee: termo='%s', limite=%d", termo, limite)

    _validar_credenciais()

    app_id = _get_app_id()
    app_secret = _get_app_secret()
    timestamp = int(time.time())
    payload_str = _montar_payload_graphql(termo, limite)
    signature = _gerar_signature(app_id, timestamp, payload_str, app_secret)

    dados = _requisicao_shopee(payload_str, _headers(app_id, timestamp, payload_str, signature))

    product_offer = dados.get("data", {}).get("productOfferV2")
    if not product_offer:
        raise ErroRespostaShopee("Campo 'productOfferV2' não encontrado na resposta")

    nodes = product_offer.get("nodes", [])
    if not isinstance(nodes, list):
        raise ErroRespostaShopee("Campo 'nodes' não é uma lista")

    produtos = []
    for item in nodes:
        link_afiliado = item.get("offerLink") or item.get("productLink")
        if not link_afiliado:
            continue

        produto = {
            "id": str(item.get("itemId")),
            "titulo": item.get("productName"),
            "preco": _parse_preco(item.get("priceMin"), item.get("priceMax")),
            "link": link_afiliado,
        }
        if all(produto.values()):
            produtos.append(produto)

    logger.info("Encontrados %d produtos válidos na Shopee", len(produtos))
    return produtos


def _parse_preco(
    price_min: str | int | float | None, price_max: str | int | float | None
) -> float | None:
    """Converte preço da Shopee (string em centavos) para float em reais."""
    try:
        if price_min is not None:
            return float(price_min) / 100
        if price_max is not None:
            return float(price_max) / 100
    except (ValueError, TypeError):
        pass
    return None
