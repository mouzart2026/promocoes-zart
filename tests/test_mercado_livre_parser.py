"""Testes para o módulo mercado_livre_parser."""

from unittest.mock import Mock, patch

import pytest

from afiliados.mercado_livre_parser import (
    ErroParseHTML,
    ErroRedeParser,
    ErroURLInvalida,
    _extrair_id_da_url,
    _validar_url_mercado_livre,
    extrair_produto_da_url,
    extrair_produtos_das_urls,
)


class TestValidacaoURL:
    """Testes para validação e extração de ID da URL."""

    def test_extrair_id_da_url_padrao(self) -> None:
        """Testa extração de ID do formato padrão MLB-123456."""
        url = "https://produto.mercadolivre.com.br/MLB-123456-produto-teste"
        assert _extrair_id_da_url(url) == "MLB123456"

    def test_extrair_id_da_url_sem_hifen(self) -> None:
        """Testa extração de ID do formato sem hífen MLB123456."""
        url = "https://produto.mercadolivre.com.br/MLB123456-produto-teste"
        assert _extrair_id_da_url(url) == "MLB123456"

    def test_extrair_id_da_url_www(self) -> None:
        """Testa extração com www no domínio."""
        url = "https://www.mercadolivre.com.br/MLB-789012-outro-produto"
        assert _extrair_id_da_url(url) == "MLB789012"

    def test_extrair_id_da_url_catalogo(self) -> None:
        """Testa extração de ID do padrão de catálogo /p/MLBxxxxxx."""
        url = "https://www.mercadolivre.com.br/refletor-led-lumanti/p/MLB70273909"
        assert _extrair_id_da_url(url) == "MLB70273909"

    def test_extrair_id_da_url_catalogo_com_hifen(self) -> None:
        """Testa extração de ID do padrão de catálogo com hífen (não deveria acontecer mas por segurança)."""
        url = "https://www.mercadolivre.com.br/produto/p/MLB-70273909"
        assert _extrair_id_da_url(url) == "MLB70273909"

    def test_extrair_id_da_url_invalida(self) -> None:
        """Testa que URL inválida retorna None."""
        url = "https://google.com/MLB-123456"
        assert _extrair_id_da_url(url) is None

    def test_validar_url_mercado_livre_valida(self) -> None:
        """Testa validação de URL válida (anúncio padrão)."""
        _validar_url_mercado_livre("https://produto.mercadolivre.com.br/MLB-123456")
        _validar_url_mercado_livre("https://www.mercadolivre.com.br/MLB-123456")

    def test_validar_url_mercado_livre_catalogo(self) -> None:
        """Testa validação de URL de catálogo /p/MLBxxxxxx."""
        _validar_url_mercado_livre("https://www.mercadolivre.com.br/produto/p/MLB70273909")
        _validar_url_mercado_livre("https://produto.mercadolivre.com.br/outro/p/MLB123456")

    def test_validar_url_mercado_livre_dominio_ml_com_br(self) -> None:
        """Testa validação de domínio ml.com.br (URL curta)."""
        _validar_url_mercado_livre("https://ml.com.br/abc123")
        _validar_url_mercado_livre("https://www.ml.com.br/xyz789")

    def test_validar_url_mercado_livre_sec_redirect(self) -> None:
        """Testa validação de URL de redirect /sec/."""
        _validar_url_mercado_livre("https://mercadolivre.com.br/sec/abc123")

    def test_validar_url_mercado_livre_dominio_invalido(self) -> None:
        """Testa erro para domínio inválido."""
        with pytest.raises(ErroURLInvalida, match="Domínio não suportado"):
            _validar_url_mercado_livre("https://google.com/MLB-123456")

    def test_validar_url_mercado_livre_sem_id(self) -> None:
        """Testa erro para URL sem ID de produto."""
        with pytest.raises(ErroURLInvalida, match="não parece ser de produto MLB"):
            _validar_url_mercado_livre("https://mercadolivre.com.br/categoria")


class TestExtrairProdutoDaURL:
    """Testes para extração completa de produto."""

    HTML_JSON_LD = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "Product",
            "name": "Fone de Ouvido Bluetooth JBL Tune 510BT",
            "description": "Fone sem fio com bateria de 40h",
            "brand": {"@type": "Brand", "name": "JBL"},
            "sku": "JBL510BT",
            "mpn": "JBLT510BTBLKAM",
            "image": "https://http2.mlstatic.com/D_123456.jpg",
            "offers": {
                "@type": "Offer",
                "price": 299.90,
                "priceCurrency": "BRL",
                "availability": "https://schema.org/InStock"
            }
        }
        </script>
    </head>
    <body></body>
    </html>
    """

    HTML_OPEN_GRAPH = """
    <html>
    <head>
        <meta property="og:title" content="Fone de Ouvido Bluetooth JBL Tune 510BT" />
        <meta property="og:price:amount" content="299.90" />
        <meta property="og:image" content="https://http2.mlstatic.com/D_123456.jpg" />
        <meta property="og:url" content="https://produto.mercadolivre.com.br/MLB-123456" />
    </head>
    <body></body>
    </html>
    """

    HTML_MINIMO = """
    <html>
    <head>
        <meta property="og:title" content="Produto Mínimo" />
        <meta property="og:price:amount" content="49.90" />
    </head>
    <body></body>
    </html>
    """

    API_RESPONSE_404 = {"status": 404, "error": "not_found"}

    def _mock_html_response(self, html: str, final_url: str | None = None) -> Mock:
        """Cria mock de resposta HTML com url final."""
        mock_resposta = Mock()
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.text = html
        mock_resposta.url = final_url or "https://produto.mercadolivre.com.br/MLB-123456"
        mock_resposta.json.side_effect = ValueError("Not JSON")
        return mock_resposta

    def _mock_api_response(self, data: dict | None = None, status_code: int = 404) -> Mock:
        """Cria mock de resposta da API."""
        mock_resposta = Mock()
        mock_resposta.status_code = status_code
        if data is not None:
            mock_resposta.json.return_value = data
        else:
            mock_resposta.json.return_value = self.API_RESPONSE_404
        mock_resposta.raise_for_status.return_value = None
        mock_resposta.text = ""
        return mock_resposta

    def _setup_mock_get(
        self,
        mock_get: Mock,
        html: str,
        final_url: str | None = None,
        api_data: dict | None = None,
        api_status: int = 404,
    ) -> None:
        """Configura mock_get para retornar resposta da API e HTML baseado na URL."""
        api_response = self._mock_api_response(api_data, api_status)
        html_response = self._mock_html_response(html, final_url)

        def side_effect(url, *args, **kwargs):
            if "/products/" in url or "/items/" in url:
                return api_response
            return html_response

        mock_get.side_effect = side_effect

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_com_json_ld_completo(self, mock_get: Mock) -> None:
        """Testa extração completa via JSON-LD (API retorna 404)."""
        self._setup_mock_get(mock_get, self.HTML_JSON_LD)

        with patch.dict("os.environ", {"ML_AFFILIATE_TAG": "82539013"}):
            resultado = extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

        assert resultado["id"] == "MLB123456"
        assert resultado["titulo"] == "Fone de Ouvido Bluetooth JBL Tune 510BT"
        assert resultado["preco"] == 299.90
        assert resultado["link"] == "https://produto.mercadolivre.com.br/MLB-123456"
        assert resultado["imagem"] == "https://http2.mlstatic.com/D_123456.jpg"
        assert resultado["marca"] == "JBL"
        assert resultado["descricao"] == "Fone sem fio com bateria de 40h"
        assert resultado["sku"] == "JBL510BT"
        assert resultado["mpn"] == "JBLT510BTBLKAM"
        assert resultado["moeda"] == "BRL"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_com_open_graph_fallback(self, mock_get: Mock) -> None:
        """Testa fallback para OpenGraph quando JSON-LD não tem dados suficientes (API 404)."""
        self._setup_mock_get(mock_get, self.HTML_OPEN_GRAPH)

        resultado = extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

        assert resultado["id"] == "MLB123456"
        assert resultado["titulo"] == "Fone de Ouvido Bluetooth JBL Tune 510BT"
        assert resultado["preco"] == 299.90
        assert resultado["link"] == "https://produto.mercadolivre.com.br/MLB-123456"
        assert resultado["imagem"] == "https://http2.mlstatic.com/D_123456.jpg"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_minimo_open_graph(self, mock_get: Mock) -> None:
        """Testa extração mínima apenas com título e preço no OpenGraph (API 404)."""
        self._setup_mock_get(
            mock_get, self.HTML_MINIMO, final_url="https://produto.mercadolivre.com.br/MLB-999999"
        )

        resultado = extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-999999")

        assert resultado["id"] == "MLB999999"
        assert resultado["titulo"] == "Produto Mínimo"
        assert resultado["preco"] == 49.90
        assert resultado["link"] == "https://produto.mercadolivre.com.br/MLB-999999"
        assert "imagem" not in resultado

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_url_catalogo(self, mock_get: Mock) -> None:
        """Testa extração de produto via URL de catálogo /p/MLBxxxxxx (API 404)."""
        self._setup_mock_get(
            mock_get,
            self.HTML_JSON_LD,
            final_url="https://www.mercadolivre.com.br/refletor-led/p/MLB70273909",
        )

        resultado = extrair_produto_da_url(
            "https://www.mercadolivre.com.br/refletor-led/p/MLB70273909"
        )

        assert resultado["id"] == "MLB70273909"
        assert resultado["titulo"] == "Fone de Ouvido Bluetooth JBL Tune 510BT"
        assert resultado["preco"] == 299.90
        assert resultado["link"] == "https://www.mercadolivre.com.br/refletor-led/p/MLB70273909"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_com_redirect(self, mock_get: Mock) -> None:
        """Testa que segue redirect e usa URL final para ID e link (API 404)."""
        self._setup_mock_get(
            mock_get,
            self.HTML_JSON_LD,
            final_url="https://produto.mercadolivre.com.br/MLB-999888-produto-redirecionado",
        )

        resultado = extrair_produto_da_url("https://ml.com.br/abc123")

        assert resultado["id"] == "MLB999888"
        assert (
            resultado["link"]
            == "https://produto.mercadolivre.com.br/MLB-999888-produto-redirecionado"
        )

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_via_api_produtos(self, mock_get: Mock) -> None:
        """Testa extração via API /products/MLBxxx (catálogo)."""
        api_catalogo = {
            "id": "MLB70273909",
            "name": "Refletor LED Lumanti 100W",
            "pictures": [{"url": "https://http2.mlstatic.com/D_70273909.jpg"}],
            "attributes": [{"id": "BRAND", "value_name": "Lumanti"}],
        }
        api_itens = {
            "paging": {"total": 2, "offset": 0, "limit": 100},
            "results": [
                {"item_id": "MLB111", "price": 159.90, "seller_id": 123},
                {"item_id": "MLB222", "price": 149.90, "seller_id": 456},
            ],
        }

        def side_effect(url, *args, **kwargs):
            if "/products/MLB70273909/items" in url:
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = api_itens
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            elif "/products/MLB70273909" in url:
                mock_resp = Mock()
                mock_resp.status_code = 200
                mock_resp.json.return_value = api_catalogo
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            # HTML response
            mock_resp = Mock()
            mock_resp.raise_for_status.return_value = None
            mock_resp.text = "<html><head></head><body></body></html>"
            mock_resp.url = "https://www.mercadolivre.com.br/refletor-led/p/MLB70273909"
            mock_resp.json.side_effect = ValueError("Not JSON")
            return mock_resp

        mock_get.side_effect = side_effect

        resultado = extrair_produto_da_url(
            "https://www.mercadolivre.com.br/refletor-led/p/MLB70273909"
        )

        assert resultado["id"] == "MLB70273909"
        assert resultado["titulo"] == "Refletor LED Lumanti 100W"
        assert resultado["preco"] == 149.90  # menor preço dos itens
        assert resultado["imagem"] == "https://http2.mlstatic.com/D_70273909.jpg"
        assert resultado["marca"] == "Lumanti"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_via_api_items(self, mock_get: Mock) -> None:
        """Testa extração via API /items/MLBxxx (anúncio)."""
        api_data = {
            "id": "MLB123456",
            "title": "Fone JBL Tune 510BT",
            "price": 249.90,
            "thumbnail": "https://http2.mlstatic.com/D_123456.jpg",
            "buy_box_winner": {"price": 249.90},
        }
        self._setup_mock_get(
            mock_get, "<html><head></head><body></body></html>", api_data=api_data, api_status=200
        )

        resultado = extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

        assert resultado["id"] == "MLB123456"
        assert resultado["titulo"] == "Fone JBL Tune 510BT"
        assert resultado["preco"] == 249.90
        assert resultado["imagem"] == "https://http2.mlstatic.com/D_123456.jpg"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_extrair_api_fallback_para_html(self, mock_get: Mock) -> None:
        """Testa que falha na API cai para HTML parsing."""
        self._setup_mock_get(mock_get, self.HTML_JSON_LD, api_data=None, api_status=404)

        with patch.dict("os.environ", {"ML_AFFILIATE_TAG": "82539013"}):
            resultado = extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

        assert resultado["id"] == "MLB123456"
        assert resultado["titulo"] == "Fone de Ouvido Bluetooth JBL Tune 510BT"

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_erro_sem_titulo(self, mock_get: Mock) -> None:
        """Testa erro quando não encontra título (API 404, HTML vazio)."""
        html = "<html><head></head><body></body></html>"
        self._setup_mock_get(mock_get, html)

        with pytest.raises(ErroParseHTML, match="Título não encontrado"):
            extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_erro_sem_preco(self, mock_get: Mock) -> None:
        """Testa erro quando não encontra preço válido (API 404, HTML sem preço)."""
        html = (
            '<html><head><meta property="og:title" content="Produto" /></head><body></body></html>'
        )
        self._setup_mock_get(mock_get, html)

        with pytest.raises(ErroParseHTML, match="Preço inválido ou não encontrado"):
            extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_erro_rede_timeout(self, mock_get: Mock) -> None:
        """Testa erro de timeout na rede."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        with pytest.raises(ErroRedeParser, match="Timeout ao buscar página"):
            extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_erro_rede_conexao(self, mock_get: Mock) -> None:
        """Testa erro de conexão."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError()

        with pytest.raises(ErroRedeParser, match="Erro de conexão"):
            extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")

    @patch("afiliados.mercado_livre_parser.requests.get")
    def test_erro_http_404(self, mock_get: Mock) -> None:
        """Testa erro HTTP 404."""
        import requests

        mock_resposta = Mock()
        mock_resposta.status_code = 404
        mock_get.side_effect = requests.exceptions.HTTPError(response=mock_resposta)

        with pytest.raises(ErroRedeParser, match="Erro HTTP 404"):
            extrair_produto_da_url("https://produto.mercadolivre.com.br/MLB-123456")


class TestExtrairProdutosDasURLs:
    """Testes para extração em lote."""

    @patch("afiliados.mercado_livre_parser.extrair_produto_da_url")
    def test_extrair_multiplos_sucesso(self, mock_extrair: Mock) -> None:
        """Testa extração de múltiplas URLs com sucesso."""
        mock_extrair.side_effect = [
            {"id": "MLB1", "titulo": "Produto 1", "preco": 100.0, "link": "http://url1"},
            {"id": "MLB2", "titulo": "Produto 2", "preco": 200.0, "link": "http://url2"},
        ]

        urls = [
            "https://produto.mercadolivre.com.br/MLB-1",
            "https://produto.mercadolivre.com.br/MLB-2",
        ]
        resultado = extrair_produtos_das_urls(urls)

        assert len(resultado) == 2
        assert resultado[0]["id"] == "MLB1"
        assert resultado[1]["id"] == "MLB2"

    @patch("afiliados.mercado_livre_parser.extrair_produto_da_url")
    def test_extrair_multiplos_com_falhas(self, mock_extrair: Mock) -> None:
        """Testa que falhas individuais não param o lote."""
        from afiliados.mercado_livre_parser import ErroParseHTML

        mock_extrair.side_effect = [
            {"id": "MLB1", "titulo": "Produto 1", "preco": 100.0, "link": "http://url1"},
            ErroParseHTML("Falha no segundo"),
            {"id": "MLB3", "titulo": "Produto 3", "preco": 300.0, "link": "http://url3"},
        ]

        urls = [
            "https://produto.mercadolivre.com.br/MLB-1",
            "https://produto.mercadolivre.com.br/MLB-2",
            "https://produto.mercadolivre.com.br/MLB-3",
        ]
        resultado = extrair_produtos_das_urls(urls)

        assert len(resultado) == 2
        assert resultado[0]["id"] == "MLB1"
        assert resultado[1]["id"] == "MLB3"
