"""Testes para o módulo mercado_livre."""

from unittest.mock import Mock, patch

import pytest

from afiliados.mercado_livre import (
    _TOKEN_CACHE,
    ErroCredenciaisMercadoLivre,
    ErroRedeMercadoLivre,
    ErroRespostaMercadoLivre,
    buscar_produtos,
)


@pytest.fixture(autouse=True)
def limpar_cache_token():
    """Limpa o cache de token antes de cada teste."""
    _TOKEN_CACHE.clear()
    yield
    _TOKEN_CACHE.clear()


class TestBuscarProdutos:
    """Testes para a função buscar_produtos."""

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_sucesso(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa busca com resposta válida da API."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {
                "access_token": "TEST_TOKEN_123",
                "expires_in": 3600,
            }
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.return_value = {
                "results": [
                    {
                        "id": "MLB123456",
                        "title": "Produto Teste 1",
                        "price": 99.90,
                        "permalink": "https://produto.mercadolivre.com.br/MLB-123456",
                    },
                    {
                        "id": "MLB789012",
                        "title": "Produto Teste 2",
                        "price": 149.90,
                        "permalink": "https://produto.mercadolivre.com.br/MLB-789012",
                    },
                ]
            }
            mock_get.return_value = mock_resposta

            resultado = buscar_produtos("notebook", limite=2)

            assert len(resultado) == 2
            assert resultado[0]["id"] == "MLB123456"
            assert resultado[0]["titulo"] == "Produto Teste 1"
            assert resultado[0]["preco"] == 99.90
            assert resultado[0]["link"] == "https://produto.mercadolivre.com.br/MLB-123456"
            assert resultado[1]["id"] == "MLB789012"

            mock_post.assert_called_once_with(
                "https://api.mercadolibre.com/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": "TEST_CLIENT_ID",
                    "client_secret": "TEST_CLIENT_SECRET",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
            mock_get.assert_called_once_with(
                "https://api.mercadolibre.com/sites/MLB/search",
                params={"q": "notebook", "limit": 2},
                headers={"Authorization": "Bearer TEST_TOKEN_123"},
                timeout=10,
            )

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_limite_padrao(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa que o limite padrão é 20."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.return_value = {"results": []}
            mock_get.return_value = mock_resposta

            buscar_produtos("teste")

            mock_get.assert_called_once_with(
                "https://api.mercadolibre.com/sites/MLB/search",
                params={"q": "teste", "limit": 20},
                headers={"Authorization": "Bearer TOKEN"},
                timeout=10,
            )

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_filtra_campos_vazios(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa que produtos com campos faltando são filtrados."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.return_value = {
                "results": [
                    {"id": "MLB1", "title": "Completo", "price": 10.0, "permalink": "http://link"},
                    {"id": "MLB2", "title": "Sem preco", "permalink": "http://link"},
                    {"id": "MLB3", "title": "Sem link", "price": 20.0},
                ]
            }
            mock_get.return_value = mock_resposta

            resultado = buscar_produtos("teste")

            assert len(resultado) == 1
            assert resultado[0]["id"] == "MLB1"

    def test_buscar_produtos_sem_credenciais(self) -> None:
        """Testa erro quando credenciais não estão configuradas."""
        with patch.dict("os.environ", {"ML_CLIENT_ID": "", "ML_CLIENT_SECRET": ""}, clear=True):
            with pytest.raises(
                ErroCredenciaisMercadoLivre, match="ML_CLIENT_ID e ML_CLIENT_SECRET"
            ):
                buscar_produtos("teste")

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_timeout_token(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro de timeout ao obter token."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_post.side_effect = requests.exceptions.Timeout()

            with pytest.raises(ErroRedeMercadoLivre, match="Timeout ao obter token"):
                buscar_produtos("teste")

            mock_get.assert_not_called()

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_erro_conexao_token(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro de conexão ao obter token."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_post.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(ErroRedeMercadoLivre, match="conexão ao obter token"):
                buscar_produtos("teste")

            mock_get.assert_not_called()

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_erro_http_token(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro HTTP ao obter token."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_resposta = Mock()
            mock_resposta.status_code = 400
            mock_post.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

            with pytest.raises(ErroRespostaMercadoLivre, match="Erro HTTP ao obter token"):
                buscar_produtos("teste")

            mock_get.assert_not_called()

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_token_json_invalido(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa resposta de token que não é JSON válido."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.side_effect = ValueError("Invalid JSON")
            mock_post.return_value = mock_resposta

            with pytest.raises(ErroRespostaMercadoLivre, match="JSON válido"):
                buscar_produtos("teste")

            mock_get.assert_not_called()

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_token_sem_access_token(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa resposta de token sem access_token."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.return_value = {"expires_in": 3600}
            mock_post.return_value = mock_resposta

            with pytest.raises(ErroRespostaMercadoLivre, match="Token de acesso não retornado"):
                buscar_produtos("teste")

            mock_get.assert_not_called()

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_timeout_busca(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro de timeout na busca."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_get.side_effect = requests.exceptions.Timeout()

            with pytest.raises(ErroRedeMercadoLivre, match="Timeout ao consultar"):
                buscar_produtos("teste")

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_erro_conexao_busca(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro de conexão na busca."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_get.side_effect = requests.exceptions.ConnectionError()

            with pytest.raises(ErroRedeMercadoLivre, match="conexão com a API"):
                buscar_produtos("teste")

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_erro_http_busca(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa erro HTTP na busca."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.status_code = 500
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

            with pytest.raises(ErroRespostaMercadoLivre, match="Erro HTTP da API"):
                buscar_produtos("teste")

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_erro_401_limpa_cache(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa que erro 401 limpa o cache do token."""
        import requests

        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.status_code = 401
            mock_get.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

            with pytest.raises(ErroRespostaMercadoLivre, match="Token expirado ou inválido"):
                buscar_produtos("teste")

            assert "access_token" not in _TOKEN_CACHE

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_json_invalido_busca(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa resposta de busca que não é JSON válido."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.side_effect = ValueError("Invalid JSON")
            mock_get.return_value = mock_resposta

            with pytest.raises(ErroRespostaMercadoLivre, match="JSON válido"):
                buscar_produtos("teste")

    @patch("afiliados.mercado_livre.requests.post")
    @patch("afiliados.mercado_livre.requests.get")
    def test_buscar_produtos_results_nao_lista(self, mock_get: Mock, mock_post: Mock) -> None:
        """Testa quando 'results' não é uma lista."""
        with patch.dict(
            "os.environ",
            {"ML_CLIENT_ID": "TEST_CLIENT_ID", "ML_CLIENT_SECRET": "TEST_CLIENT_SECRET"},
        ):
            mock_token_resposta = Mock()
            mock_token_resposta.raise_for_status.return_value = None
            mock_token_resposta.json.return_value = {"access_token": "TOKEN", "expires_in": 3600}
            mock_post.return_value = mock_token_resposta

            mock_resposta = Mock()
            mock_resposta.raise_for_status.return_value = None
            mock_resposta.json.return_value = {"results": "nao eh lista"}
            mock_get.return_value = mock_resposta

            with pytest.raises(ErroRespostaMercadoLivre, match="não é uma lista"):
                buscar_produtos("teste")
