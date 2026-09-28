"""Módulo para envio de notificações via WhatsApp (Evolution API)."""

import logging
import os
from typing import Any

import requests

from afiliados.http_utils import retry_com_backoff

logger = logging.getLogger(__name__)


class WhatsAppError(Exception):
    """Exceção base para erros do módulo WhatsApp."""

    pass


class ErroCredenciaisWhatsApp(WhatsAppError):
    """Credenciais da Evolution API não configuradas."""

    pass


class ErroRedeWhatsApp(WhatsAppError):
    """Erro de rede ao enviar mensagem."""

    pass


class ErroRespostaWhatsApp(WhatsAppError):
    """Erro na resposta da Evolution API."""

    pass


def _get_evolution_url() -> str:
    """Retorna EVOLUTION_API_URL do ambiente."""
    return os.getenv("EVOLUTION_API_URL", "")


def _get_evolution_key() -> str:
    """Retorna EVOLUTION_API_KEY do ambiente."""
    return os.getenv("EVOLUTION_API_KEY", "")


def _get_instance_name() -> str:
    """Retorna EVOLUTION_INSTANCE_NAME do ambiente."""
    return os.getenv("EVOLUTION_INSTANCE_NAME", "")


def _get_group_id() -> str:
    """Retorna WHATSAPP_GROUP_ID do ambiente."""
    return os.getenv("WHATSAPP_GROUP_ID", "")


def _validar_credenciais() -> None:
    """Valida se as credenciais da Evolution API estão configuradas."""
    if not _get_evolution_url() or not _get_evolution_key() or not _get_instance_name():
        raise ErroCredenciaisWhatsApp(
            "EVOLUTION_API_URL, EVOLUTION_API_KEY e EVOLUTION_INSTANCE_NAME devem estar configurados no .env"
        )


def _headers() -> dict:
    """Retorna headers padrão para requisições à Evolution API."""
    return {
        "Content-Type": "application/json",
        "apikey": _get_evolution_key(),
    }


@retry_com_backoff(max_tentativas=3, backoff_base=1.0)
def _enviar_requisicao(endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Faz requisição à Evolution API com retry.

    Args:
        endpoint: Endpoint da API (ex: "message/sendText/instance").
        payload: Corpo da requisição.

    Returns:
        JSON da resposta.

    Raises:
        ErroRedeWhatsApp: Falha de conexão ou timeout.
        ErroRespostaWhatsApp: Erro HTTP ou resposta inválida.
    """
    url = f"{_get_evolution_url().rstrip('/')}/{endpoint}"

    try:
        resposta = requests.post(url, json=payload, headers=_headers(), timeout=15)
        resposta.raise_for_status()
    except requests.exceptions.Timeout as exc:
        raise ErroRedeWhatsApp("Timeout ao enviar mensagem via Evolution API") from exc
    except requests.exceptions.ConnectionError as exc:
        raise ErroRedeWhatsApp("Erro de conexão com Evolution API") from exc
    except requests.exceptions.HTTPError as exc:
        raise ErroRespostaWhatsApp(
            f"Erro HTTP da Evolution API: {exc.response.status_code} - {exc.response.text}"
        ) from exc
    except requests.exceptions.RequestException as exc:
        raise ErroRedeWhatsApp(f"Erro na requisição: {exc}") from exc

    try:
        return dict(resposta.json())
    except ValueError as exc:
        raise ErroRespostaWhatsApp("Resposta não é JSON válido") from exc


def enviar_mensagem_texto(texto: str, numero: str | None = None) -> dict:
    """
    Envia mensagem de texto via Evolution API.

    Args:
        texto: Texto da mensagem.
        numero: Número/ID do destinatário (usa WHATSAPP_GROUP_ID se não informado).

    Returns:
        Resposta da API.

    Raises:
        ErroCredenciaisWhatsApp: Credenciais não configuradas.
        ErroRedeWhatsApp: Falha de conexão.
        ErroRespostaWhatsApp: Erro da API.
    """
    _validar_credenciais()

    destino = numero or _get_group_id()
    if not destino:
        raise ErroCredenciaisWhatsApp("WHATSAPP_GROUP_ID não configurado e nenhum número informado")

    instance = _get_instance_name()
    endpoint = f"message/sendText/{instance}"
    payload = {"number": destino, "text": texto}

    logger.info("Enviando mensagem WhatsApp para %s (instance: %s)", destino, instance)
    resultado: dict[str, Any] = _enviar_requisicao(endpoint, payload)
    logger.debug("Mensagem enviada com sucesso: %s", resultado)
    return resultado


def enviar_oferta(oferta: dict) -> dict | None:
    """
    Envia notificação de oferta via WhatsApp.

    Args:
        oferta: Dicionário com chaves:
            - titulo (str)
            - preco_anterior (float)
            - preco_novo (float)
            - queda_pct (float)
            - link (str)
            - plataforma (str, opcional)

    Returns:
        Resposta da API ou None se credenciais não configuradas.
    """
    from afiliados.mensagens import formatar_oferta_whatsapp

    try:
        _validar_credenciais()
    except ErroCredenciaisWhatsApp:
        logger.debug("Credenciais WhatsApp não configuradas, pulando envio")
        return None

    texto = formatar_oferta_whatsapp(oferta)
    return enviar_mensagem_texto(texto)
