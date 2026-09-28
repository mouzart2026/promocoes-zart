#!/usr/bin/env python3
"""Ponto de entrada CLI para captação de ofertas de afiliados."""

import argparse
import sys

from afiliados import orquestrador
from afiliados.http_utils import configurar_logging


def main() -> int:
    configurar_logging()

    parser = argparse.ArgumentParser(
        description="Captação de ofertas em marketplaces para links de afiliado",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--termo",
        required=True,
        help="Termo de busca (ex: 'notebook gamer', 'fone bluetooth')",
    )
    parser.add_argument(
        "--queda",
        type=float,
        default=10.0,
        help="Porcentagem mínima de queda de preço para considerar oferta",
    )
    parser.add_argument(
        "--plataformas",
        nargs="+",
        choices=["mercado_livre", "shopee"],
        default=["mercado_livre"],
        help="Plataformas para buscar",
    )

    args = parser.parse_args()

    print(f"Buscando ofertas para: '{args.termo}' (queda >= {args.queda}%)")
    print("-" * 60)

    try:
        ofertas = orquestrador.rodar(args.termo, args.queda, args.plataformas)
    except Exception as e:
        print(f"[ERRO] Falha na execução: {e}", file=sys.stderr)
        return 1

    if not ofertas:
        print("Nenhuma oferta encontrada nesta rodada.")
        return 0

    print(f"\n🎯 {len(ofertas)} oferta(s) encontrada(s):\n")
    for i, oferta in enumerate(ofertas, 1):
        print(f"  {i}. {oferta['titulo']}")
        print(f"     ID: {oferta['produto_id']}")
        print(f"     Preço anterior: R$ {oferta['preco_anterior']:.2f}")
        print(f"     Preço atual:    R$ {oferta['preco_novo']:.2f}")
        print(f"     Queda:          {oferta['queda_pct']:.2f}%")
        print(f"     Link afiliado:  {oferta['link']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())