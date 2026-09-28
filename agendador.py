#!/usr/bin/env python3
"""
Agendador de busca de ofertas de afiliados.

Roda orquestrador.rodar em loop para múltiplos termos definidos em termos.json.
"""

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from afiliados import orquestrador
from afiliados.http_utils import configurar_logging

configurar_logging()

logger = logging.getLogger(__name__)


class Agendador:
    """Gerencia execução periódica de buscas de ofertas."""

    def __init__(
        self,
        termos_path: str = "termos.json",
        intervalo_minutos: int = 60,
    ):
        self.termos_path = Path(termos_path)
        self.intervalo_segundos = intervalo_minutos * 60
        self.rodando = False
        self._configurar_sinais()

    def _configurar_sinais(self) -> None:
        """Configura handlers para encerramento gracioso."""
        signal.signal(signal.SIGINT, self._sinal_encerramento)
        signal.signal(signal.SIGTERM, self._sinal_encerramento)

    def _sinal_encerramento(self, signum: int, frame: Any) -> None:
        """Handler para Ctrl+C / SIGTERM."""
        logger.info("Sinal de encerramento recebido. Finalizando...")
        self.rodando = False

    def _carregar_termos(self) -> list[dict]:
        """Carrega termos do arquivo JSON."""
        if not self.termos_path.exists():
            raise FileNotFoundError(f"Arquivo de termos não encontrado: {self.termos_path}")

        with open(self.termos_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        termos = dados.get("termos", [])
        if not termos:
            raise ValueError("Nenhum termo definido em termos.json")

        # Validação básica
        for i, t in enumerate(termos):
            if "termo" not in t:
                raise ValueError(f"Termo {i} não tem campo 'termo'")
            if "queda_minima_pct" not in t:
                t["queda_minima_pct"] = 10.0
            if "plataformas" not in t:
                t["plataformas"] = ["mercado_livre"]

        return termos

    def _executar_rodada(self, termo_config: dict) -> list[dict]:
        """Executa uma rodada de busca para um termo."""
        termo = termo_config["termo"]
        queda = termo_config["queda_minima_pct"]
        plataformas = termo_config.get("plataformas", ["mercado_livre"])
        preco_minimo = termo_config.get("preco_minimo")
        preco_maximo = termo_config.get("preco_maximo")

        try:
            ofertas = orquestrador.rodar(
                termo=termo,
                limite_queda_pct=queda,
                plataformas=plataformas,
                preco_minimo=preco_minimo,
                preco_maximo=preco_maximo,
            )
            return ofertas
        except Exception as e:
            logger.exception("Erro ao executar rodada para '%s'", termo)
            return []

    def executar(self) -> None:
        """Loop principal do agendador."""
        try:
            termos = self._carregar_termos()
        except (FileNotFoundError, ValueError, json.JSONDecodeError) as e:
            logger.error("Erro ao carregar termos: %s", e)
            sys.exit(1)

        logger.info("=" * 60)
        logger.info("Agendador de Ofertas - Iniciado")
        logger.info("Arquivo de termos: %s", self.termos_path)
        logger.info("Intervalo: %d minuto(s)", self.intervalo_segundos // 60)
        logger.info("Termos configurados: %d", len(termos))
        for t in termos:
            logger.info("  - %s (queda >= %.1f%%) | %s", t["termo"], t["queda_minima_pct"], t["plataformas"])
        logger.info("=" * 60)
        logger.info("Pressione Ctrl+C para encerrar")

        self.rodando = True
        rodada = 0

        while self.rodando:
            rodada += 1
            inicio_rodada = time.time()

            logger.info("Rodada #%d iniciada (%d termo(s))", rodada, len(termos))

            for termo_config in termos:
                if not self.rodando:
                    break
                ofertas = self._executar_rodada(termo_config)
                if ofertas:
                    logger.info("%s | %d oferta(s) | Plataformas: %s", termo_config["termo"], len(ofertas), {o.get("plataforma") for o in ofertas})
                    for o in ofertas:
                        logger.info("  [%s] %s... | R$ %.2f -> R$ %.2f (%.1f%% OFF)",
                                    o.get("plataforma"), o["titulo"][:50], o["preco_anterior"], o["preco_novo"], o["queda_pct"])
                else:
                    logger.info("%s | Nenhuma oferta (queda >= %.1f%%)", termo_config["termo"], termo_config["queda_minima_pct"])

            if not self.rodando:
                break

            duracao = time.time() - inicio_rodada
            logger.info("Rodada #%d concluída em %.1fs", rodada, duracao)

            # Sleep com verificação periódica para permitir Ctrl+C rápido
            tempo_restante = self.intervalo_segundos
            while tempo_restante > 0 and self.rodando:
                sleep_chunk = min(10, tempo_restante)
                time.sleep(sleep_chunk)
                tempo_restante -= sleep_chunk

        logger.info("Agendador encerrado. Total de rodadas: %d", rodada)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Agendador de busca de ofertas de afiliados",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--termos",
        default="termos.json",
        help="Caminho para arquivo JSON com termos de busca",
    )
    parser.add_argument(
        "--intervalo",
        type=int,
        default=60,
        help="Intervalo entre rodadas em minutos",
    )

    args = parser.parse_args()

    agendador = Agendador(
        termos_path=args.termos,
        intervalo_minutos=args.intervalo,
    )
    agendador.executar()
    return 0


if __name__ == "__main__":
    sys.exit(main())