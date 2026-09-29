from afiliados import mercado_livre_parser

url = "https://www.mercadolivre.com.br/refletor-led-lumanti-urbe-de-100w-para-poste-ip66-luz-branco-frio/p/MLB70273909"
try:
    result = mercado_livre_parser.extrair_produto_da_url(url)
    print("Sucesso!")
    print(f'ID: {result["id"]}')
    print(f'Titulo: {result["titulo"]}')
    print(f'Preco: {result["preco"]}')
    print(f'Imagem: {result.get("imagem", "N/A")}')
    print(f'Link: {result["link"]}')
    print(f'Marca: {result.get("marca", "N/A")}')
except Exception as e:
    print(f"Erro: {type(e).__name__}: {e}")