import re
import requests

url = "https://www.mercadolivre.com.br/refletor-led-lumanti-urbe-de-100w-para-poste-ip66-luz-branco-frio/p/MLB70273909"
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )
}

res = requests.get(url, headers=headers)
print("Status Code:", res.status_code)

precos_rs = re.findall(r"R\$\s?[\d\.,]+", res.text)
print("Preços com R$:", list(set(precos_rs))[:5])

precos_attr = re.findall(r'"price":\s*([\d\.]+)', res.text)
print('Valores no atributo "price":', list(set(precos_attr))[:5])

# Busca por ofertas no schema
precos_amount = re.findall(r'"priceAmount":\s*([\d\.]+)', res.text)
print('Valores no atributo "priceAmount":', list(set(precos_amount))[:5])