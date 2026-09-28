"""Testes para o módulo links."""

import os
from unittest.mock import patch

import pytest

from afiliados.links import (
    PlataformaNaoImplementada,
    gerar_link_afiliado,
)


class TestGerarLinkAfiliado:
    """Testes para a função gerar_link_afiliado."""

    def test_mercado_livre_com_tag(self) -> None:
        """Testa que a tag aparece na URL quando ML_AFFILIATE_TAG está definida."""
        with patch.dict(os.environ, {"ML_AFFILIATE_TAG": "minha_tag_123"}):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123456"}
            resultado = gerar_link_afiliado(item, "mercado_livre")

            assert "matt_tool=minha_tag_123" in resultado
            assert resultado.startswith("https://produto.mercadolivre.com.br/MLB-123456")

    def test_mercado_livre_com_tag_e_word(self) -> None:
        """Testa que ambos matt_tool e matt_word aparecem quando ambos configurados."""
        with patch.dict(
            os.environ,
            {"ML_AFFILIATE_TAG": "minha_tag", "ML_AFFILIATE_WORD": "minha_word"},
        ):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123456"}
            resultado = gerar_link_afiliado(item, "mercado_livre")

            assert "matt_tool=minha_tag" in resultado
            assert "matt_word=minha_word" in resultado
            assert resultado.count("matt_") == 2

    def test_mercado_livre_sem_word_so_tag(self) -> None:
        """Testa que só matt_tool é enviado quando word está vazia."""
        with patch.dict(os.environ, {"ML_AFFILIATE_TAG": "tag", "ML_AFFILIATE_WORD": ""}):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123456"}
            with patch("afiliados.links.logger") as mock_logger:
                resultado = gerar_link_afiliado(item, "mercado_livre")

                assert "matt_tool=tag" in resultado
                assert "matt_word" not in resultado
                mock_logger.warning.assert_called_once_with(
                    "ML_AFFILIATE_WORD não configurada. Enviando apenas matt_tool."
                )

    def test_mercado_livre_sem_tag_retorna_original(self) -> None:
        """Testa que retorna link original e avisa quando tag não está configurada."""
        with patch.dict(os.environ, {}, clear=True):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123456"}

            with pytest.warns(UserWarning, match="ML_AFFILIATE_TAG não configurada"):
                resultado = gerar_link_afiliado(item, "mercado_livre")

            assert resultado == "https://produto.mercadolivre.com.br/MLB-123456"
            assert "matt_tool" not in resultado

    def test_mercado_livre_link_com_query_existente(self) -> None:
        """Testa link que já tem query parameters."""
        with patch.dict(os.environ, {"ML_AFFILIATE_TAG": "tag_teste"}):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123?foo=bar"}
            resultado = gerar_link_afiliado(item, "mercado_livre")

            assert "matt_tool=tag_teste" in resultado
            assert "&matt_tool=tag_teste" in resultado

    def test_mercado_livre_link_com_query_existente_com_word(self) -> None:
        """Testa link com query existente e ambos parâmetros."""
        with patch.dict(os.environ, {"ML_AFFILIATE_TAG": "tag", "ML_AFFILIATE_WORD": "word"}):
            item = {"link": "https://produto.mercadolivre.com.br/MLB-123?foo=bar"}
            resultado = gerar_link_afiliado(item, "mercado_livre")

            assert "matt_tool=tag" in resultado
            assert "matt_word=word" in resultado
            assert resultado.startswith("https://produto.mercadolivre.com.br/MLB-123?foo=bar&")

    def test_shopee_retorna_link_original(self) -> None:
        """Testa que para Shopee retorna o link original (já vem com tracking da API)."""
        item = {"link": "https://shopee.com.br/produto?aff=tracking123"}
        resultado = gerar_link_afiliado(item, "shopee")

        assert resultado == "https://shopee.com.br/produto?aff=tracking123"

    def test_amazon_levanta_excecao(self) -> None:
        """Testa que plataforma 'amazon' levanta PlataformaNaoImplementada."""
        item = {"link": "https://amazon.com.br/dp/B012345678"}

        with pytest.raises(PlataformaNaoImplementada, match="ainda não implementada"):
            gerar_link_afiliado(item, "amazon")

    def test_plataforma_desconhecida_levanta_excecao(self) -> None:
        """Testa que plataforma desconhecida levanta PlataformaNaoImplementada."""
        item = {"link": "https://exemplo.com/produto"}

        with pytest.raises(PlataformaNaoImplementada, match="não suportada"):
            gerar_link_afiliado(item, "magalu")

    def test_item_sem_link_retorna_vazio(self) -> None:
        """Testa comportamento quando item não tem link."""
        with patch.dict(os.environ, {"ML_AFFILIATE_TAG": "tag", "ML_AFFILIATE_WORD": ""}):
            item = {}
            resultado = gerar_link_afiliado(item, "mercado_livre")

            assert resultado == "?matt_tool=tag"
