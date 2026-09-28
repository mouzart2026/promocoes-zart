"""Testes para o módulo orquestrador."""

from unittest.mock import Mock, patch

import pytest

from afiliados import orquestrador
from afiliados.armazenamento import ErroCredenciaisSupabase
from afiliados.links import PlataformaNaoImplementada
from afiliados.mercado_livre import ErroRedeMercadoLivre
from afiliados.shopee import ErroRedeShopee


class TestCalcularQuedaPct:
    """Testes para _calcular_queda_pct."""

    def test_queda_normal(self) -> None:
        assert orquestrador._calcular_queda_pct(100.0, 80.0) == 20.0

    def test_sem_queda(self) -> None:
        assert orquestrador._calcular_queda_pct(100.0, 100.0) == 0.0

    def test_aumento_preco(self) -> None:
        assert orquestrador._calcular_queda_pct(100.0, 120.0) == -20.0

    def test_preco_anterior_zero(self) -> None:
        assert orquestrador._calcular_queda_pct(0.0, 50.0) == 0.0


class TestRodar:
    """Testes para a função rodar."""

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    @patch("afiliados.orquestrador.links.gerar_link_afiliado")
    def test_rodar_encontra_oferta_ml(
        self,
        mock_gerar_link: Mock,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa fluxo completo: produto ML com queda >= limite gera oferta."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB123", "titulo": "Produto Teste", "preco": 80.0, "link": "http://link"}
        ]
        mock_buscar_preco.return_value = 100.0
        mock_gerar_link.return_value = "http://link?matt_tool=tag123"

        ofertas = orquestrador.rodar("notebook", limite_queda_pct=10.0)

        assert len(ofertas) == 1
        oferta = ofertas[0]
        assert oferta["produto_id"] == "MLB123"
        assert oferta["titulo"] == "Produto Teste"
        assert oferta["preco_anterior"] == 100.0
        assert oferta["preco_novo"] == 80.0
        assert oferta["queda_pct"] == 20.0
        assert oferta["link"] == "http://link?matt_tool=tag123"
        assert oferta["plataforma"] == "mercado_livre"

        mock_salvar_produto.assert_called_once()
        mock_salvar_oferta.assert_called_once()
        # Verifica que plataformas foram passadas corretamente
        args, kwargs = mock_salvar_produto.call_args
        assert kwargs["plataforma"] == "mercado_livre"
        # salvar_oferta recebe um dict como argumento posicional
        args, _ = mock_salvar_oferta.call_args
        assert args[0]["plataforma"] == "mercado_livre"

    @patch("afiliados.orquestrador.shopee.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    @patch("afiliados.orquestrador.links.gerar_link_afiliado")
    def test_rodar_encontra_oferta_shopee(
        self,
        mock_gerar_link: Mock,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa fluxo completo: produto Shopee com queda >= limite gera oferta."""
        mock_buscar_produtos.return_value = [
            {
                "id": "1234567890",
                "titulo": "Produto Shopee",
                "preco": 80.0,
                "link": "http://shopee.link?aff=123",
            }
        ]
        mock_buscar_preco.return_value = 100.0
        mock_gerar_link.return_value = "http://shopee.link?aff=123"  # Shopee retorna link original

        ofertas = orquestrador.rodar("notebook", limite_queda_pct=10.0, plataformas=["shopee"])

        assert len(ofertas) == 1
        oferta = ofertas[0]
        assert oferta["produto_id"] == "1234567890"
        assert oferta["titulo"] == "Produto Shopee"
        assert oferta["preco_anterior"] == 100.0
        assert oferta["preco_novo"] == 80.0
        assert oferta["queda_pct"] == 20.0
        assert oferta["link"] == "http://shopee.link?aff=123"
        assert oferta["plataforma"] == "shopee"

        mock_salvar_produto.assert_called_once()
        mock_salvar_oferta.assert_called_once()
        args, kwargs = mock_salvar_produto.call_args
        assert kwargs["plataforma"] == "shopee"

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    def test_rodar_sem_queda_nao_gera_oferta(
        self,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa que queda < limite não gera oferta."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB123", "titulo": "Produto", "preco": 95.0, "link": "http://link"}
        ]
        mock_buscar_preco.return_value = 100.0

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert len(ofertas) == 0
        mock_salvar_produto.assert_called_once()
        mock_salvar_oferta.assert_not_called()

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    def test_rodar_sem_preco_salvo_so_atualiza(
        self,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa que produto sem preço salvo apenas atualiza, não gera oferta."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB999", "titulo": "Novo Produto", "preco": 50.0, "link": "http://link"}
        ]
        mock_buscar_preco.return_value = None

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert len(ofertas) == 0
        mock_salvar_produto.assert_called_once()
        # preco_anterior deve ser None na primeira vez
        args, kwargs = mock_salvar_produto.call_args
        assert kwargs["preco_anterior"] is None
        assert kwargs["plataforma"] == "mercado_livre"
        mock_salvar_oferta.assert_not_called()

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    @patch("afiliados.orquestrador.links.gerar_link_afiliado")
    def test_rodar_multiplos_produtos_algumas_ofertas(
        self,
        mock_gerar_link: Mock,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa múltiplos produtos, alguns viram oferta outros não."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB1", "titulo": "Oferta", "preco": 80.0, "link": "http://l1"},
            {"id": "MLB2", "titulo": "Sem Oferta", "preco": 95.0, "link": "http://l2"},
            {"id": "MLB3", "titulo": "Outra Oferta", "preco": 70.0, "link": "http://l3"},
        ]
        mock_buscar_preco.side_effect = [100.0, 100.0, 100.0]
        mock_gerar_link.side_effect = [
            "http://l1?matt_tool=tag",
            "http://l2?matt_tool=tag",
            "http://l3?matt_tool=tag",
        ]

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert len(ofertas) == 2
        assert ofertas[0]["produto_id"] == "MLB1"
        assert ofertas[1]["produto_id"] == "MLB3"
        assert mock_salvar_produto.call_count == 3
        assert mock_salvar_oferta.call_count == 2

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    def test_rodar_erro_busca_mercado_livre_continua(self, mock_buscar_produtos: Mock) -> None:
        """Testa que erro na busca do ML não trava, apenas loga."""
        mock_buscar_produtos.side_effect = ErroRedeMercadoLivre("Timeout")

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert ofertas == []

    @patch("afiliados.orquestrador.shopee.buscar_produtos")
    def test_rodar_erro_busca_shopee_continua(self, mock_buscar_produtos: Mock) -> None:
        """Testa que erro na busca da Shopee não trava, apenas loga."""
        mock_buscar_produtos.side_effect = ErroRedeShopee("Timeout")

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0, plataformas=["shopee"])

        assert ofertas == []

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    def test_rodar_erro_salvar_produto_continua(
        self,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa que erro ao salvar produto não trava o loop."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB1", "titulo": "Produto", "preco": 80.0, "link": "http://link"}
        ]
        mock_buscar_preco.return_value = 100.0
        mock_salvar_produto.side_effect = ErroCredenciaisSupabase("Sem credenciais")

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert ofertas == []

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.links.gerar_link_afiliado")
    def test_rodar_erro_link_afiliado_continua(
        self,
        mock_gerar_link: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_produtos: Mock,
    ) -> None:
        """Testa que erro ao gerar link afiliado não trava."""
        mock_buscar_produtos.return_value = [
            {"id": "MLB1", "titulo": "Produto", "preco": 80.0, "link": "http://link"}
        ]
        mock_buscar_preco.return_value = 100.0
        mock_gerar_link.side_effect = PlataformaNaoImplementada("Erro")

        ofertas = orquestrador.rodar("teste", limite_queda_pct=10.0)

        assert ofertas == []

    @patch("afiliados.orquestrador.mercado_livre.buscar_produtos")
    @patch("afiliados.orquestrador.shopee.buscar_produtos")
    @patch("afiliados.orquestrador.armazenamento.buscar_preco_salvo")
    @patch("afiliados.orquestrador.armazenamento.salvar_produto")
    @patch("afiliados.orquestrador.armazenamento.salvar_oferta")
    @patch("afiliados.orquestrador.links.gerar_link_afiliado")
    def test_rodar_multiplas_plataformas(
        self,
        mock_gerar_link: Mock,
        mock_salvar_oferta: Mock,
        mock_salvar_produto: Mock,
        mock_buscar_preco: Mock,
        mock_buscar_shopee: Mock,
        mock_buscar_ml: Mock,
    ) -> None:
        """Testa busca em múltiplas plataformas na mesma rodada."""
        mock_buscar_ml.return_value = [
            {"id": "MLB1", "titulo": "ML Oferta", "preco": 80.0, "link": "http://ml1"}
        ]
        mock_buscar_shopee.return_value = [
            {"id": "SP1", "titulo": "SP Oferta", "preco": 90.0, "link": "http://sp1"}
        ]
        mock_buscar_preco.side_effect = [100.0, 120.0]
        mock_gerar_link.side_effect = [
            "http://ml1?matt_tool=tag",
            "http://sp1",  # Shopee retorna original
        ]

        ofertas = orquestrador.rodar(
            "teste", limite_queda_pct=10.0, plataformas=["mercado_livre", "shopee"]
        )

        assert len(ofertas) == 2
        assert ofertas[0]["produto_id"] == "MLB1"
        assert ofertas[0]["plataforma"] == "mercado_livre"
        assert ofertas[1]["produto_id"] == "SP1"
        assert ofertas[1]["plataforma"] == "shopee"
        assert mock_buscar_ml.called
        assert mock_buscar_shopee.called

    def test_rodar_plataforma_desconhecida_ignora(self) -> None:
        """Testa que plataformas desconhecidas levantam erro."""
        with pytest.raises(ValueError, match="Plataforma desconhecida"):
            orquestrador.rodar("teste", limite_queda_pct=10.0, plataformas=["magalu"])


class TestMain:
    """Testes para o CLI main.py."""

    @patch("afiliados.orquestrador.rodar")
    def test_main_sem_ofertas(self, mock_rodar: Mock, capsys: pytest.CaptureFixture) -> None:
        """Testa saída quando não há ofertas."""
        mock_rodar.return_value = []

        import sys

        sys.path.insert(0, "C:\\Gestão Zart\\Projetos\\Site Promoções")
        from main import main

        sys.argv = ["main.py", "--termo", "teste"]
        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Nenhuma oferta encontrada" in captured.out

    @patch("afiliados.orquestrador.rodar")
    def test_main_com_ofertas(self, mock_rodar: Mock, capsys: pytest.CaptureFixture) -> None:
        """Testa saída formatada com ofertas."""
        mock_rodar.return_value = [
            {
                "produto_id": "MLB123",
                "titulo": "Produto Teste",
                "preco_anterior": 100.0,
                "preco_novo": 80.0,
                "queda_pct": 20.0,
                "link": "http://afiliado.com",
                "plataforma": "mercado_livre",
            }
        ]

        import sys

        sys.path.insert(0, "C:\\Gestão Zart\\Projetos\\Site Promoções")
        from main import main

        sys.argv = ["main.py", "--termo", "teste", "--queda", "10"]
        result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "1 oferta(s) encontrada(s)" in captured.out
        assert "Produto Teste" in captured.out
        assert "R$ 100.00" in captured.out
        assert "R$ 80.00" in captured.out
        assert "20.00%" in captured.out

    def test_main_termo_obrigatorio(self) -> None:
        """Testa que --termo é obrigatório."""
        import sys

        sys.path.insert(0, "C:\\Gestão Zart\\Projetos\\Site Promoções")
        from main import main

        sys.argv = ["main.py"]
        with pytest.raises(SystemExit) as exc:
            main()
        assert exc.value.code != 0
