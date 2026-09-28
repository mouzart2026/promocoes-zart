#!/usr/bin/env python3
"""Teste manual dos endpoints do Mercado Livre com token OAuth."""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

client_id = os.getenv("ML_CLIENT_ID", "").strip()
client_secret = os.getenv("ML_CLIENT_SECRET", "").strip()

if not client_id or not client_secret:
    print("ERRO: ML_CLIENT_ID e ML_CLIENT_SECRET não configurados")
    exit(1)

# 1. Obter token
print("=== Obtendo token OAuth ===")
token_url = "https://api.mercadolibre.com/oauth/token"
token_data = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
}
token_headers = {"Content-Type": "application/x-www-form-urlencoded"}

try:
    token_resp = requests.post(token_url, data=token_data, headers=token_headers, timeout=10)
    print(f"Token status: {token_resp.status_code}")
    print(f"Token response: {token_resp.text}")
    token_resp.raise_for_status()
    token_json = token_resp.json()
    access_token = token_json.get("access_token")
    print(f"Access token obtido: {access_token[:20]}..." if access_token else "SEM TOKEN")
except Exception as e:
    print(f"Erro ao obter token: {e}")
    exit(1)

if not access_token:
    print("Falha: token não obtido")
    exit(1)

auth_header = {"Authorization": f"Bearer {access_token}"}

# 2. Testar endpoint /sites/MLB/search
print("\n=== Testando GET /sites/MLB/search?q=fone ===")
url1 = "https://api.mercadolibre.com/sites/MLB/search"
params1 = {"q": "fone", "limit": 5}

try:
    resp1 = requests.get(url1, params=params1, headers=auth_header, timeout=10)
    print(f"Status: {resp1.status_code}")
    print(f"URL: {resp1.url}")
    print(f"Response: {resp1.text[:2000]}")
except Exception as e:
    print(f"Erro: {e}")

# 3. Testar endpoint /products/search
print("\n=== Testando GET /products/search?status=active&site_id=MLB&q=fone ===")
url2 = "https://api.mercadolibre.com/products/search"
params2 = {"status": "active", "site_id": "MLB", "q": "fone", "limit": 5}

try:
    resp2 = requests.get(url2, params=params2, headers=auth_header, timeout=10)
    print(f"Status: {resp2.status_code}")
    print(f"URL: {resp2.url}")
    print(f"Response: {resp2.text[:2000]}")
except Exception as e:
    print(f"Erro: {e}")

print("\n=== Fim dos testes ===")