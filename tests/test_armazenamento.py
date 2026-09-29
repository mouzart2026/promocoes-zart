"""Testes para o módulo armazenamento."""

import os
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from afiliados.armazenamento import (
    ErroCredenciaisSupabase,
    ErroRedeSupabase,
    ErroRespostaSupabase,
    buscar_preco_salvo,
    salvar_oferta,
    salvar_produto,
)


class TestBuscarPrecoSalvo:
    """Testes para buscar_preco_salvo."""

    @patch("afiliados.armazenamento.requests.request")
    def test_buscar_preco_salvo_encontrado(self, mock_request: Mock) -> None:
        """Testa busca quando produto existe."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = [{"preco_atual": "99.90"}]
        mock_request.return_value = mock_resposta

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            resultado = buscar_preco_salvo("MLB123", "mercado_livre")

        assert resultado == 99.90
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "GET"
        assert args[1] == "https://test.supabase.co/rest/v1/produtos_rastreados"
        assert kwargs["params"]["id"] == "eq.MLB123"
        assert kwargs["params"]["plataforma"] == "eq.mercado_livre"
        assert kwargs["params"]["select"] == "preco_atual"

    @patch("afiliados.armazenamento.requests.request")
    def test_buscar_preco_salvo_encontrado_shopee(self, mock_request: Mock) -> None:
        """Testa busca quando produto existe na Shopee."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = [{"preco_atual": "89.90"}]
        mock_request.return_value = mock_resposta

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            resultado = buscar_preco_salvo("1234567890", "shopee")

        assert resultado == 89.90
        args, kwargs = mock_request.call_args
        assert kwargs["params"]["id"] == "eq.1234567890"
        assert kwargs["params"]["plataforma"] == "eq.shopee"

    @patch("afiliados.armazenamento.requests.request")
    def test_buscar_preco_salvo_nao_existe(self, mock_request: Mock) -> None:
        """Testa busca quando produto não existe (retorna None)."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            resultado = buscar_preco_salvo("MLB999", "mercado_livre")

        assert resultado is None

    def test_buscar_preco_salvo_sem_credenciais(self) -> None:
        """Testa erro quando credenciais não estão configuradas."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ErroCredenciaisSupabase, match="SUPABASE_URL e SUPABASE_KEY"):
                buscar_preco_salvo("MLB123", "mercado_livre")

    @patch("afiliados.armazenamento.requests.request")
    def test_buscar_preco_salvo_erro_rede(self, mock_request: Mock) -> None:
        """Testa erro de rede."""
        import requests

        mock_request.side_effect = requests.exceptions.ConnectionError()

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            with pytest.raises(ErroRedeSupabase, match="conexão"):
                buscar_preco_salvo("MLB123", "mercado_livre")


class TestSalvarProduto:
    """Testes para salvar_produto."""

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_produto_completo(self, mock_request: Mock) -> None:
        """Testa upsert de produto com todos os campos."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        agora = datetime(2024, 1, 15, 10, 30, 0)

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_produto(
                "MLB123", "Produto Teste", 99.90, 120.00, "http://link", agora, "mercado_livre"
            )

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert "produtos_rastreados" in args[1]
        assert kwargs["params"]["on_conflict"] == "id"
        payload = kwargs["json"]
        assert payload["id"] == "MLB123"
        assert payload["titulo"] == "Produto Teste"
        assert payload["preco_atual"] == 99.90
        assert payload["preco_anterior"] == 120.00
        assert payload["link"] == "http://link"
        assert payload["ultima_atualizacao"] == "2024-01-15T10:30:00"
        assert payload["plataforma"] == "mercado_livre"

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_produto_shopee(self, mock_request: Mock) -> None:
        """Testa upsert de produto Shopee."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        agora = datetime(2024, 1, 15, 10, 30, 0)

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_produto(
                "1234567890", "Produto Shopee", 89.90, 100.00, "http://link", agora, "shopee"
            )

        payload = mock_request.call_args.kwargs["json"]
        assert payload["id"] == "1234567890"
        assert payload["plataforma"] == "shopee"

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_produto_sem_preco_anterior(self, mock_request: Mock) -> None:
        """Testa upsert sem preco_anterior (None)."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        agora = datetime(2024, 1, 15, 10, 30, 0)

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_produto("MLB123", "Produto", 50.0, None, "http://link", agora)

        payload = mock_request.call_args.kwargs["json"]
        assert payload["preco_anterior"] is None
        assert payload["plataforma"] == "mercado_livre"  # default


class TestSalvarOferta:
    """Testes para salvar_oferta."""

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_oferta_completa(self, mock_request: Mock) -> None:
        """Testa inserção de oferta com todos os campos."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        oferta = {
            "produto_id": "MLB123",
            "titulo": "Produto Oferta",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
            "link": "http://oferta",
        }

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_oferta(oferta)

        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert "ofertas_encontradas" in args[1]
        payload = kwargs["json"]
        assert payload["produto_id"] == "MLB123"
        assert payload["titulo"] == "Produto Oferta"
        assert payload["preco_anterior"] == 100.0
        assert payload["preco_novo"] == 80.0
        assert payload["queda_pct"] == 20.0
        assert payload["link"] == "http://oferta"
        assert payload["plataforma"] == "mercado_livre"  # default

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_oferta_shopee(self, mock_request: Mock) -> None:
        """Testa inserção de oferta Shopee."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        oferta = {
            "produto_id": "1234567890",
            "titulo": "Produto Shopee",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
            "link": "http://oferta",
            "plataforma": "shopee",
        }

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_oferta(oferta)

        payload = mock_request.call_args.kwargs["json"]
        assert payload["plataforma"] == "shopee"

    @patch("afiliados.armazenamento.requests.request")
    def test_salvar_oferta_sem_link(self, mock_request: Mock) -> None:
        """Testa inserção de oferta sem link (opcional)."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = []
        mock_request.return_value = mock_resposta

        oferta = {
            "produto_id": "MLB123",
            "titulo": "Produto",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
        }

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            salvar_oferta(oferta)

        payload = mock_request.call_args.kwargs["json"]
        assert payload["link"] is None


class TestErrosSupabase:
    """Testes para exceções do Supabase."""

    @patch("afiliados.armazenamento.requests.request")
    def test_erro_http_supabase(self, mock_request: Mock) -> None:
        """Testa erro HTTP do Supabase."""
        import requests

        mock_resposta = Mock()
        mock_resposta.status_code = 401
        mock_resposta.text = "Unauthorized"
        mock_request.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            with pytest.raises(ErroRespostaSupabase, match="Erro HTTP do Supabase: 401"):
                buscar_preco_salvo("MLB123", "mercado_livre")

    @patch("afiliados.armazenamento.requests.request")
    def test_timeout_supabase(self, mock_request: Mock) -> None:
        """Testa timeout no Supabase."""
        import requests

        mock_request.side_effect = requests.exceptions.Timeout()

        with patch.dict(
            os.environ, {"SUPABASE_URL": "https://test.supabase.co", "SUPABASE_KEY": "test-key"}
        ):
            with pytest.raises(ErroRedeSupabase, match="Timeout"):
                buscar_preco_salvo("MLB123", "mercado_livre")
