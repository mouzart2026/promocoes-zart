"""Testes para o módulo mensagens."""

from afiliados.mensagens import formatar_oferta_whatsapp, formatar_resumo_ofertas


class TestFormatarOfertaWhatsApp:
    """Testes para formatar_oferta_whatsapp."""

    def test_formatar_oferta_mercado_livre(self) -> None:
        """Testa formatação de oferta do Mercado Livre."""
        oferta = {
            "titulo": "Notebook Gamer RTX 4060",
            "preco_anterior": 5999.00,
            "preco_novo": 4799.00,
            "queda_pct": 20.0,
            "link": "https://produto.mercadolivre.com.br/MLB-123456",
            "plataforma": "mercado_livre",
        }

        texto = formatar_oferta_whatsapp(oferta)

        assert "🟡" in texto
        assert "*Notebook Gamer RTX 4060*" in texto
        assert "R$ 5999.00" in texto
        assert "R$ 4799.00" in texto
        assert "20.0% OFF" in texto
        assert "https://produto.mercadolivre.com.br/MLB-123456" in texto
        assert "Como afiliado" in texto

    def test_formatar_oferta_shopee(self) -> None:
        """Testa formatação de oferta da Shopee."""
        oferta = {
            "titulo": "Fone Bluetooth JBL",
            "preco_anterior": 299.90,
            "preco_novo": 199.90,
            "queda_pct": 33.3,
            "link": "https://shopee.com.br/produto/123",
            "plataforma": "shopee",
        }

        texto = formatar_oferta_whatsapp(oferta)

        assert "🧡" in texto
        assert "*Fone Bluetooth JBL*" in texto
        assert "33.3% OFF" in texto

    def test_formatar_oferta_plataforma_desconhecida(self) -> None:
        """Testa formatação com plataforma desconhecida (usa ícone genérico)."""
        oferta = {
            "titulo": "Produto Genérico",
            "preco_anterior": 100.0,
            "preco_novo": 80.0,
            "queda_pct": 20.0,
            "link": "https://link",
            "plataforma": "desconhecida",
        }

        texto = formatar_oferta_whatsapp(oferta)

        assert "🔗" in texto

    def test_formatar_oferta_campos_faltando(self) -> None:
        """Testa formatação com campos faltando (usa valores padrão)."""
        oferta = {}

        texto = formatar_oferta_whatsapp(oferta)

        assert "Produto" in texto
        assert "R$ 0.00" in texto
        assert "0.0% OFF" in texto


class TestFormatarResumoOfertas:
    """Testes para formatar_resumo_ofertas."""

    def test_formatar_resumo_vazio(self) -> None:
        """Testa resumo com lista vazia."""
        texto = formatar_resumo_ofertas([])

        assert "Nenhuma oferta encontrada" in texto

    def test_formatar_resumo_uma_oferta(self) -> None:
        """Testa resumo com uma oferta."""
        ofertas = [
            {
                "titulo": "Produto Teste",
                "preco_novo": 99.90,
                "queda_pct": 15.0,
                "plataforma": "mercado_livre",
            }
        ]

        texto = formatar_resumo_ofertas(ofertas)

        assert "1 nova(s) oferta(s)" in texto
        assert "Produto Teste" in texto
        assert "R$ 99.90" in texto
        assert "15.0% OFF" in texto
        assert "promocoes-zart.pages.dev" in texto

    def test_formatar_resumo_multiplas_ofertas(self) -> None:
        """Testa resumo com múltiplas ofertas."""
        ofertas = [
            {
                "titulo": f"Produto {i}",
                "preco_novo": 100.0 + i,
                "queda_pct": 10.0 + i,
                "plataforma": "mercado_livre",
            }
            for i in range(15)
        ]

        texto = formatar_resumo_ofertas(ofertas)

        assert "15 nova(s) oferta(s)" in texto
        assert "Produto 0" in texto
        assert "Produto 9" in texto
        assert "Produto 10" not in texto  # só mostra até 10
        assert "mais 5 ofertas" in texto

    def test_formatar_resumo_trunca_titulo_longo(self) -> None:
        """Testa que títulos longos são truncados no resumo."""
        ofertas = [
            {
                "titulo": "A" * 60,
                "preco_novo": 50.0,
                "queda_pct": 10.0,
                "plataforma": "mercado_livre",
            }
        ]

        texto = formatar_resumo_ofertas(ofertas)

        assert "A" * 50 in texto
        assert "A" * 51 not in texto  # truncado em 50
