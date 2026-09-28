"""Formatadores de mensagens para WhatsApp."""


def formatar_oferta_whatsapp(oferta: dict) -> str:
    """
    Formata uma oferta para envio via WhatsApp.

    Args:
        oferta: Dicionário com chaves:
            - titulo (str)
            - preco_anterior (float)
            - preco_novo (float)
            - queda_pct (float)
            - link (str)
            - plataforma (str, opcional)

    Returns:
        Texto formatado com emojis.
    """
    titulo = oferta.get("titulo", "Produto")
    preco_anterior = oferta.get("preco_anterior", 0)
    preco_novo = oferta.get("preco_novo", 0)
    queda_pct = oferta.get("queda_pct", 0)
    link = oferta.get("link", "")
    plataforma = oferta.get("plataforma", "mercado_livre")

    icones = {
        "mercado_livre": "🟡",
        "shopee": "🧡",
        "amazon": "📦",
    }
    icone = icones.get(plataforma, "🔗")

    linhas = [
        f"{icone} *{titulo}*",
        "",
        f"💰 *De:* R$ {preco_anterior:.2f}",
        f"🔥 *Por:* R$ {preco_novo:.2f}",
        f"📉 *Desconto:* {queda_pct:.1f}% OFF",
        "",
        f"🔗 {link}",
        "",
        "_Como afiliado, posso receber comissão pelas compras feitas pelos links. Os preços podem mudar sem aviso._",
    ]

    return "\n".join(linhas)


def formatar_resumo_ofertas(ofertas: list[dict]) -> str:
    """
    Formata um resumo de múltiplas ofertas para WhatsApp.

    Args:
        ofertas: Lista de ofertas.

    Returns:
        Texto formatado.
    """
    if not ofertas:
        return "📭 Nenhuma oferta encontrada nesta rodada."

    linhas = [f"🎯 *{len(ofertas)} nova(s) oferta(s) encontrada(s):*", ""]

    for i, oferta in enumerate(ofertas[:10], 1):
        titulo = oferta.get("titulo", "Produto")[:50]
        preco_novo = oferta.get("preco_novo", 0)
        queda_pct = oferta.get("queda_pct", 0)
        plataforma = oferta.get("plataforma", "mercado_livre")

        icones = {
            "mercado_livre": "🟡",
            "shopee": "🧡",
            "amazon": "📦",
        }
        icone = icones.get(plataforma, "🔗")

        linhas.append(f"{i}. {icone} {titulo}... - R$ {preco_novo:.2f} ({queda_pct:.1f}% OFF)")

    if len(ofertas) > 10:
        linhas.append(f"\n... e mais {len(ofertas) - 10} ofertas.")

    linhas.append("\n🔗 Acesse o site para ver todas: https://promocoes-zart.pages.dev")

    return "\n".join(linhas)
