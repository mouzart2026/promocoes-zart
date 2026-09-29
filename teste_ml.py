import requests, json, re
from bs4 import BeautifulSoup

url = 'https://www.mercadolivre.com.br/refletor-led-lumanti-urbe-de-100w-para-poste-ip66-luz-branco-frio/p/MLB70273909'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7'
}

res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# Busca 1: OpenGraph
title = soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'})
img = soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'})

# Busca 2: JSON-LD (Dados estruturados do schema.org)
json_data = {}
for script in soup.find_all('script', type='application/ld+json'):
    try:
        data = json.loads(script.string)
        if isinstance(data, dict) and data.get('@type') in ['Product', 'ItemPage']:
            json_data = data
            break
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and item.get('@type') in ['Product', 'ItemPage']:
                    json_data = item
                    break
    except:
        continue

final_title = (title['content'] if title else None) or json_data.get('name') or soup.title.string if soup.title else 'Não encontrado'
final_img = (img['content'] if img else None) or json_data.get('image') or 'Não encontrada'

# Preço no JSON-LD ou HTML
offers = json_data.get('offers', {})
if isinstance(offers, list) and len(offers) > 0:
    offers = offers[0]
final_price = offers.get('price') or offers.get('lowPrice')

print('--- DADOS EXTRAÍDOS DO MERCADO LIVRE ---')
print('Status Code:', res.status_code)
print('Título:', final_title)
print('Imagem:', final_img)
print('Preço:', final_price if final_price else 'Não encontrado')
