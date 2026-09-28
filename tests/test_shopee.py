"""Testes para o módulo shopee."""

import os
from unittest.mock import Mock, patch

import pytest

from afiliados.shopee import (
    ErroCredenciaisShopee,
    ErroRedeShopee,
    ErroRespostaShopee,
    _gerar_signature,
    _montar_payload_graphql,
    buscar_produtos,
)


class TestGerarSignature:
    """Testes para _gerar_signature."""

    def test_signature_calculo_correto(self) -> None:
        """Testa cálculo da signature HMAC-SHA256."""
        app_id = "123456"
        timestamp = 1704067200
        payload = '{"query":"test"}'
        secret = "abc123xyz"

        signature = _gerar_signature(app_id, timestamp, payload, secret)

        # Verifica se é um hash SHA256 válido (64 chars hex)
        assert len(signature) == 64
        assert all(c in "0123456789abcdef" for c in signature)

    def test_signature_deterministico(self) -> None:
        """Testa que mesma entrada produz mesma signature."""
        app_id = "123456"
        timestamp = 1704067200
        payload = '{"query":"test"}'
        secret = "abc123xyz"

        sig1 = _gerar_signature(app_id, timestamp, payload, secret)
        sig2 = _gerar_signature(app_id, timestamp, payload, secret)

        assert sig1 == sig2


class TestMontarPayloadGraphQL:
    """Testes para _montar_payload_graphql."""

    def test_payload_contem_query_e_variaveis(self) -> None:
        """Testa que payload contém query GraphQL e variáveis."""
        payload = _montar_payload_graphql("notebook", 20)

        assert "productOfferV2" in payload
        assert "keyword" in payload
        assert "notebook" in payload
        assert "limit" in payload
        assert "20" in payload
        # Payload deve ser JSON compacto (sem espaços/quebras de linha)
        assert "\n" not in payload
        assert "  " not in payload


class TestBuscarProdutos:
    """Testes para a função buscar_produtos."""

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_sucesso(self, mock_post: Mock) -> None:
        """Testa busca com resposta válida da API."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {
            "data": {
                "productOfferV2": {
                    "nodes": [
                        {
                            "itemId": 1234567890,
                            "productName": "Produto Shopee 1",
                            "productLink": "https://shopee.com.br/produto-1",
                            "offerLink": "https://shopee.com.br/produto-1?aff=tracking123",
                            "imageUrl": "https://img.com/1.jpg",
                            "priceMin": "19990",
                            "priceMax": "24990",
                            "priceDiscountRate": 20,
                            "sales": 100,
                            "ratingStar": 4.5,
                            "commissionRate": "0.15",
                            "shopId": 98765,
                            "shopName": "Loja Teste",
                            "periodStartTime": 1704067200,
                            "periodEndTime": 1706745600,
                        },
                        {
                            "itemId": 9876543210,
                            "productName": "Produto Shopee 2",
                            "productLink": "https://shopee.com.br/produto-2",
                            "offerLink": "https://shopee.com.br/produto-2?aff=tracking456",
                            "imageUrl": "https://img.com/2.jpg",
                            "priceMin": "8990",
                            "priceMax": "12990",
                            "priceDiscountRate": 30,
                            "sales": 50,
                            "ratingStar": 4.8,
                            "commissionRate": "0.20",
                            "shopId": 54321,
                            "shopName": "Outra Loja",
                            "periodStartTime": 1704067200,
                            "periodEndTime": 1706745600,
                        },
                    ],
                    "pageInfo": {"page": 1, "limit": 20, "hasNextPage": False},
                }
            }
        }
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            resultado = buscar_produtos("notebook", limite=2)

        assert len(resultado) == 2
        assert resultado[0]["id"] == "1234567890"
        assert resultado[0]["titulo"] == "Produto Shopee 1"
        assert resultado[0]["preco"] == 199.90  # priceMin / 100
        assert resultado[0]["link"] == "https://shopee.com.br/produto-1?aff=tracking123"
        assert resultado[1]["id"] == "9876543210"
        assert resultado[1]["preco"] == 89.90

        # Verifica chamada HTTP
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://open-api.affiliate.shopee.com.br/graphql"
        assert "data" in kwargs
        assert "headers" in kwargs
        assert "Authorization" in kwargs["headers"]
        assert kwargs["headers"]["Authorization"].startswith("SHA256 Credential=123456")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_limite_padrao(self, mock_post: Mock) -> None:
        """Testa que o limite padrão é 20."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {
            "data": {"productOfferV2": {"nodes": [], "pageInfo": {}}}
        }
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            buscar_produtos("teste")

        args, kwargs = mock_post.call_args
        payload = kwargs["data"]
        assert "limit:20" in payload

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_filtra_sem_link(self, mock_post: Mock) -> None:
        """Testa que produtos sem offerLink nem productLink são filtrados."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {
            "data": {
                "productOfferV2": {
                    "nodes": [
                        {
                            "itemId": 111,
                            "productName": "Com Link",
                            "productLink": "https://shopee.com.br/a",
                            "offerLink": "https://shopee.com.br/a?aff=1",
                            "priceMin": "10000",
                        },
                        {
                            "itemId": 222,
                            "productName": "Sem Link",
                            "productLink": None,
                            "offerLink": None,
                            "priceMin": "20000",
                        },
                    ],
                    "pageInfo": {},
                }
            }
        }
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            resultado = buscar_produtos("teste")

        assert len(resultado) == 1
        assert resultado[0]["id"] == "111"

    def test_buscar_produtos_sem_credenciais(self) -> None:
        """Testa erro quando credenciais não estão configuradas."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ErroCredenciaisShopee, match="SHOPEE_APP_ID e SHOPEE_APP_SECRET"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_erro_graphql(self, mock_post: Mock) -> None:
        """Testa erro GraphQL na resposta."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {
            "errors": [
                {"message": "Invalid Signature", "extensions": {"code": 10020}},
                {"message": "Rate limit exceeded"},
            ]
        }
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRespostaShopee, match="Erros GraphQL"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_json_invalido(self, mock_post: Mock) -> None:
        """Testa resposta que não é JSON válido."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRespostaShopee, match="JSON válido"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_campo_ausente(self, mock_post: Mock) -> None:
        """Testa resposta sem productOfferV2."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {"data": {}}
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRespostaShopee, match="productOfferV2"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_nodes_nao_lista(self, mock_post: Mock) -> None:
        """Testa quando nodes não é lista."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.json.return_value = {
            "data": {"productOfferV2": {"nodes": "nao eh lista", "pageInfo": {}}}
        }
        mock_post.return_value = mock_resposta

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRespostaShopee, match="não é uma lista"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_timeout(self, mock_post: Mock) -> None:
        """Testa erro de timeout."""
        import requests

        mock_post.side_effect = requests.exceptions.Timeout()

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRedeShopee, match="Timeout"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_erro_conexao(self, mock_post: Mock) -> None:
        """Testa erro de conexão."""
        import requests

        mock_post.side_effect = requests.exceptions.ConnectionError()

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRedeShopee, match="conexão"):
                buscar_produtos("teste")

    @patch("afiliados.shopee.requests.post")
    def test_buscar_produtos_erro_http(self, mock_post: Mock) -> None:
        """Testa erro HTTP da API."""
        import requests

        mock_resposta = Mock()
        mock_resposta.status_code = 401
        mock_resposta.text = "Unauthorized"
        mock_post.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

        with patch.dict(os.environ, {"SHOPEE_APP_ID": "123456", "SHOPEE_APP_SECRET": "secret123"}):
            with pytest.raises(ErroRespostaShopee, match="Erro HTTP da API Shopee: 401"):
                buscar_produtos("teste")
