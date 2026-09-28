"""Testes para o módulo whatsapp."""

from unittest.mock import Mock, patch

import pytest

from afiliados.whatsapp import (
    ErroCredenciaisWhatsApp,
    ErroRedeWhatsApp,
    ErroRespostaWhatsApp,
    enviar_mensagem_texto,
    enviar_oferta,
)


class TestEnviarMensagemTexto:
    """Testes para enviar_mensagem_texto."""

    @patch("afiliados.whatsapp._enviar_requisicao")
    @patch("afiliados.whatsapp._validar_credenciais")
    @patch.dict(
        "os.environ",
        {
            "EVOLUTION_API_URL": "https://evo.example.com",
            "EVOLUTION_API_KEY": "test_key",
            "EVOLUTION_INSTANCE_NAME": "test_instance",
            "WHATSAPP_GROUP_ID": "123456789@g.us",
        },
    )
    def test_enviar_mensagem_texto_sucesso(self, mock_validar: Mock, mock_enviar: Mock) -> None:
        """Testa envio de mensagem com sucesso."""
        mock_enviar.return_value = {"key": {"id": "msg_123"}}

        resultado = enviar_mensagem_texto("Olá, mundo!")

        assert resultado == {"key": {"id": "msg_123"}}
        mock_enviar.assert_called_once_with(
            "message/sendText/test_instance",
            {"number": "123456789@g.us", "text": "Olá, mundo!"},
        )

    @patch("afiliados.whatsapp._validar_credenciais")
    @patch.dict("os.environ", {}, clear=True)
    def test_enviar_mensagem_texto_sem_credenciais(self, mock_validar: Mock) -> None:
        """Testa erro quando credenciais não estão configuradas."""
        mock_validar.side_effect = ErroCredenciaisWhatsApp("credenciais")

        with pytest.raises(ErroCredenciaisWhatsApp, match="credenciais"):
            enviar_mensagem_texto("teste")

    @patch("afiliados.whatsapp._enviar_requisicao")
    @patch("afiliados.whatsapp._validar_credenciais")
    @patch.dict(
        "os.environ",
        {
            "EVOLUTION_API_URL": "https://evo.example.com",
            "EVOLUTION_API_KEY": "test_key",
            "EVOLUTION_INSTANCE_NAME": "test_instance",
            "WHATSAPP_GROUP_ID": "123456789@g.us",
        },
    )
    def test_enviar_mensagem_texto_timeout(self, mock_validar: Mock, mock_enviar: Mock) -> None:
        """Testa erro de timeout."""

        mock_enviar.side_effect = ErroRedeWhatsApp("Timeout")

        with pytest.raises(ErroRedeWhatsApp, match="Timeout"):
            enviar_mensagem_texto("teste")

    @patch("afiliados.whatsapp._enviar_requisicao")
    @patch("afiliados.whatsapp._validar_credenciais")
    @patch.dict(
        "os.environ",
        {
            "EVOLUTION_API_URL": "https://evo.example.com",
            "EVOLUTION_API_KEY": "test_key",
            "EVOLUTION_INSTANCE_NAME": "test_instance",
            "WHATSAPP_GROUP_ID": "123456789@g.us",
        },
    )
    def test_enviar_mensagem_texto_erro_http(self, mock_validar: Mock, mock_enviar: Mock) -> None:
        """Testa erro HTTP da API."""
        mock_enviar.side_effect = ErroRespostaWhatsApp("Erro HTTP: 400")

        with pytest.raises(ErroRespostaWhatsApp, match="Erro HTTP"):
            enviar_mensagem_texto("teste")


class TestEnviarOferta:
    """Testes para enviar_oferta."""

    @patch("afiliados.whatsapp.enviar_mensagem_texto")
    @patch.dict(
        "os.environ",
        {
            "EVOLUTION_API_URL": "https://evo.example.com",
            "EVOLUTION_API_KEY": "test_key",
            "EVOLUTION_INSTANCE_NAME": "test_instance",
            "WHATSAPP_GROUP_ID": "123456789@g.us",
        },
    )
    def test_enviar_oferta_sucesso(self, mock_enviar: Mock) -> None:
        """Testa envio de oferta com sucesso."""
        mock_enviar.return_value = {"key": {"id": "msg_123"}}

        oferta = {
            "titulo": "Produto Teste",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
            "link": "https://exemplo.com/produto",
            "plataforma": "mercado_livre",
        }

        resultado = enviar_oferta(oferta)

        assert resultado == {"key": {"id": "msg_123"}}
        mock_enviar.assert_called_once()
        texto_enviado = mock_enviar.call_args[0][0]
        assert "Produto Teste" in texto_enviado
        assert "R$ 100.00" in texto_enviado
        assert "R$ 80.00" in texto_enviado
        assert "20.0%" in texto_enviado
        assert "https://exemplo.com/produto" in texto_enviado

    @patch.dict("os.environ", {}, clear=True)
    def test_enviar_oferta_sem_credenciais(self) -> None:
        """Testa que retorna None quando credenciais não configuradas."""
        oferta = {
            "titulo": "Produto",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
            "link": "https://link",
            "plataforma": "mercado_livre",
        }

        resultado = enviar_oferta(oferta)

        assert resultado is None
