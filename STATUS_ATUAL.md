# Status do Projeto - Automação de Marketing de Afiliados

**Data:** 28/09/2026  
**Diretório:** `C:\Gestão Zart\Projetos\Site Promoções`

---

## Resumo Executivo

Projeto Python completo para automação de marketing de afiliados (**Mercado Livre + Shopee**), com:
- Busca de produtos na API do Mercado Livre (OAuth client_credentials) e Shopee Affiliate Open API (GraphQL + HMAC-SHA256)
- Geração de links de afiliado (ML: `matt_tool`; Shopee: link já vem com tracking da API)
- Armazenamento no Supabase (REST API) com suporte multi-plataforma
- Orquestrador que detecta quedas de preço em múltiplas plataformas com filtros de qualidade
- CLI funcional com suporte a WhatsApp
- **Agendador automático** (`agendador.py`) com loop configurável via `termos.json` (preço min/max por termo)
- **Site estático no Cloudflare Pages** com filtros, busca, ordenação, SEO/Open Graph, dark mode
- **Dashboard** com estatísticas, gráficos (SVG), top 10 descontos
- **Aviso de Afiliado** obrigatório (página dedicada + rodapé em todas as páginas)
- **Notificações WhatsApp** via Evolution API (opcional)
- **Retry com backoff exponencial** + logging estruturado em `logs/afiliados.log`
- **81 testes** passando (mockados, sem chamadas reais)
- Lint (ruff), format (black), type-check (mypy strict) configurados

---

## URLs de Produção

| Serviço | URL |
|---------|-----|
| **Site (Cloudflare Pages)** | https://promocoes-zart.pages.dev |
| **Dashboard** | https://promocoes-zart.pages.dev/dashboard.html |
| **Aviso de Afiliado** | https://promocoes-zart.pages.dev/aviso.html |
| Supabase (backend) | https://innyohbvgtsoihooykxp.supabase.co |

> **Nota:** O site era um Cloudflare Worker em `promocoes-zart.iwebb.workers.dev` — migrado para Pages em 27/09/2026. O Worker antigo pode ser removido manualmente no dashboard do Cloudflare.

---

## Estrutura de Arquivos

```
Site Promoções/
├── src/
│   └── afiliados/
│       ├── __init__.py
│       ├── mercado_livre.py      # API ML com OAuth client_credentials + cache token
│       ├── shopee.py             # Shopee GraphQL + HMAC-SHA256
│       ├── links.py              # Gera links afiliado (ML + Shopee)
│       ├── armazenamento.py      # Supabase REST API (multi-plataforma)
│       ├── orquestrador.py       # Fluxo principal multi-plataforma + filtros qualidade
│       ├── whatsapp.py           # Evolution API integration
│       ├── mensagens.py          # Formatadores WhatsApp
│       ├── http_utils.py         # Retry backoff + logging estruturado
│       └── py.typed              # Marker para mypy
├── tests/
│   ├── test_mercado_livre.py     # 18 testes (OAuth + retry)
│   ├── test_shopee.py            # 14 testes
│   ├── test_links.py             # 7 testes
│   ├── test_armazenamento.py     # 13 testes
│   ├── test_orquestrador.py      # 18 testes
│   ├── test_whatsapp.py          # 7 testes
│   └── test_mensagens.py         # 7 testes
├── site/                         # Site estático (Cloudflare Pages)
│   ├── index.html                # Página principal com filtros
│   ├── dashboard.html            # Dashboard de estatísticas
│   ├── aviso.html                # Aviso de afiliado (compliance)
│   ├── app.js                    # Lógica do site (filtros, busca, ordenação)
│   ├── dashboard.js              # Lógica do dashboard (gráficos SVG)
│   ├── styles.css                # Estilos compartilhados
│   ├── favicon.svg               # Favicon
│   ├── _headers                  # Security headers
│   ├── _redirects                # Redirects
│   └── README.md
├── agendador.py                  # Agendador loop contínuo + preço min/max
├── termos.json                   # Configuração termos (preco_minimo, preco_maximo)
├── main.py                       # CLI entry point + --whatsapp
├── pyproject.toml                # Config: build, ruff, black, mypy, deps
├── requirements.txt              # requests, python-dotenv, pytest
├── .env.example                  # Template variáveis de ambiente
├── .env                          # Credenciais reais (local only)
├── .gitignore                    # Python padrão + .env + logs/
├── wrangler.toml                 # Config Cloudflare Pages
├── README.md                     # Descrição completa + guia retomada
└── STATUS_ATUAL.md               # Este arquivo
```

---

## Módulos Implementados

### 1. `afiliados.mercado_livre`
**Função:** `buscar_produtos(termo: str, limite: int = 20) -> list[dict]`

- Consulta `https://api.mercadolibre.com/sites/MLB/search?q=...` com **OAuth client_credentials**
- **Autenticação:** POST `https://api.mercadolibre.com/oauth/token` com `ML_CLIENT_ID` + `ML_CLIENT_SECRET`
- **Cache de token** em memória até expirar (margem 60s), limpa automaticamente em 401
- **Retry** com backoff exponencial (3 tentativas, base 1s)
- **Logging estruturado** via `http_utils`
- Retorna: `id`, `titulo`, `preco`, `link`
- **Exceções customizadas:**
  - `MercadoLivreError` (base)
  - `ErroCredenciaisMercadoLivre` (credenciais não configuradas)
  - `ErroRedeMercadoLivre` (timeout, connection error)
  - `ErroRespostaMercadoLivre` (HTTP error, JSON inválido, results não-lista)
- Trata erros sem derrubar o programa

### 2. `afiliados.shopee` ⭐ NOVO
**Função:** `buscar_produtos(termo: str, limite: int = 20) -> list[dict]`

- Consulta GraphQL endpoint `https://open-api.affiliate.shopee.com.br/graphql` com query `productOfferV2`
- Autenticação HMAC-SHA256: `Signature = SHA256(AppId + Timestamp + Payload + Secret)`
- Headers: `Authorization: SHA256 Credential={AppId}, Timestamp={Timestamp}, Signature={Signature}`
- **Retry** com backoff exponencial (3 tentativas, base 1.5s)
- Retorna: `id` (itemId), `titulo` (productName), `preco` (priceMin/100), `link` (offerLink já com tracking)
- **Exceções customizadas:**
  - `ShopeeError` (base)
  - `ErroCredenciaisShopee`
  - `ErroRedeShopee`
  - `ErroRespostaShopee`
- Trata erros sem derrubar o programa

### 3. `afiliados.links`
**Função:** `gerar_link_afiliado(item: dict, plataforma: str) -> str`

- **Mercado Livre:** adiciona `matt_tool={ML_AFFILIATE_TAG}` na URL
  - Se `ML_AFFILIATE_TAG` não configurada → warning + retorna link original
- **Shopee:** retorna link original (já vem com tracking `offerLink` da API)
- **Amazon/outros:** levanta `PlataformaNaoImplementada`
- **Exceção:** `PlataformaNaoImplementada`

### 4. `afiliados.armazenamento`
**Funções:**

| Função | Descrição |
|--------|-----------|
| `buscar_preco_salvo(produto_id, plataforma) -> float \| None` | Consulta `preco_atual` em `produtos_rastreados` filtrando por id + plataforma |
| `salvar_produto(..., plataforma)` | UPSERT em `produtos_rastreados` (on_conflict=id,plataforma) |
| `salvar_oferta(oferta: dict)` | INSERT em `ofertas_encontradas` com campo `plataforma` |
| `oferta_recente_existe(produto_id, plataforma, horas=24) -> bool` | Verifica duplicata nas últimas N horas |

- Usa **REST API do Supabase** via `requests` (sem `supabase-py`)
- **Retry** com backoff exponencial (3 tentativas, base 1s)
- Lê `SUPABASE_URL` e `SUPABASE_KEY` do `.env` em runtime
- **Exceções:**
  - `SupabaseError` (base)
  - `ErroCredenciaisSupabase`
  - `ErroRedeSupabase`
  - `ErroRespostaSupabase`

**Schema Supabase (com coluna `plataforma`):**
```sql
ALTER TABLE produtos_rastreados
ADD COLUMN IF NOT EXISTS plataforma TEXT NOT NULL DEFAULT 'mercado_livre';

CREATE INDEX IF NOT EXISTS idx_produtos_rastreados_id_plataforma
ON produtos_rastreados (id, plataforma);

ALTER TABLE ofertas_encontradas
ADD COLUMN IF NOT EXISTS plataforma TEXT NOT NULL DEFAULT 'mercado_livre';
```

### 5. `afiliados.orquestrador`
**Função principal:** `rodar(termo, limite_queda_pct=10.0, plataformas=["mercado_livre"], enviar_whatsapp=False, preco_minimo=None, preco_maximo=None) -> list[dict]`

**Filtros de qualidade implementados:**
1. **Preço zero/negativo** → ignora
2. **Queda absurda > 90%** → ignora (provavelmente erro de dado)
3. **Duplicata 24h** → verifica `oferta_recente_existe` antes de salvar
4. **Preço min/max por termo** → lido de `termos.json` e passado via `preco_minimo`/`preco_maximo`

**Fluxo multi-plataforma:**
1. Para cada plataforma em `plataformas`: chama `buscar_produtos`
2. Para cada produto:
   - Busca preço salvo no Supabase (filtrando por `produto_id` + `plataforma`)
   - Calcula queda %: `((anterior - atual) / anterior) * 100`
   - Aplica filtros de qualidade
   - Se queda >= limite e passa filtros:
     - Gera link afiliado (específico por plataforma)
     - Salva em `ofertas_encontradas` com `plataforma`
     - Envia WhatsApp se `enviar_whatsapp=True`
   - **Sempre** atualiza `produtos_rastreados` (preco_atual, preco_anterior, plataforma)
3. Retorna lista consolidada de ofertas encontradas

**Plataformas suportadas:** `mercado_livre`, `shopee` (extensível)

### 6. `afiliados.whatsapp` ⭐ NOVO
**Funções:**
- `enviar_mensagem_texto(texto, numero=None) -> dict` — envio genérico via Evolution API
- `enviar_oferta(oferta) -> dict | None` — formata e envia oferta (retorna None se credenciais não configuradas)

**Configuração (.env):**
- `EVOLUTION_API_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE_NAME`, `WHATSAPP_GROUP_ID`
- **Retry** com backoff (3 tentativas, base 1s)
- Endpoint: `POST /message/sendText/{instance}`

### 7. `afiliados.mensagens` ⭐ NOVO
**Funções:**
- `formatar_oferta_whatsapp(oferta) -> str` — emojis, preço de/por, % desconto, link, disclaimer
- `formatar_resumo_ofertas(ofertas) -> str` — resumo múltiplas ofertas + link do site

### 8. `afiliados.http_utils` ⭐ NOVO
- `retry_com_backoff(max_tentativas=3, backoff_base=1.0)` — decorator reutilizável
- `configurar_logging()` — logging estruturado para `logs/afiliados.log` (RotatingFileHandler 5MB, 3 backups) + console

### 9. `main.py` (CLI)
```bash
python main.py --termo "notebook gamer" --queda 15 --plataformas mercado_livre shopee --whatsapp
```
- `--termo` (obrigatório): termo de busca
- `--queda` (float, default 10.0): % mínima de queda
- `--plataformas` (lista, default ["mercado_livre"]): plataformas
- `--whatsapp` (flag): envia notificações via WhatsApp
- Saída formatada com cores/emojis
- Exit code 0 (sucesso) / 1 (erro)

### 10. `agendador.py` ⭐ ATUALIZADO
**Script de execução contínua** que roda `orquestrador.rodar` em loop para múltiplos termos.

**termos.json — campos suportados por termo:**
```json
{
  "termo": "notebook gamer",
  "queda_minima_pct": 15.0,
  "plataformas": ["mercado_livre", "shopee"],
  "preco_minimo": 2000.0,
  "preco_maximo": 15000.0
}
```

**Uso:**
```bash
python agendador.py                    # padrão: termos.json, 60 min
python agendador.py --intervalo 30     # a cada 30 min
python agendador.py --termos meus.json --intervalo 45
```

**Funcionamento:**
- Lê `termos.json` (termos, queda mínima, plataformas, preço min/max)
- A cada X minutos, executa `orquestrador.rodar` para cada termo passando `preco_minimo`/`preco_maximo`
- Log estruturado: termo, horário, ofertas (com detalhes)
- Ctrl+C encerra limpo (handler SIGINT/SIGTERM)

---

## Site Estático (Cloudflare Pages)

**URL:** https://promocoes-zart.pages.dev

**Páginas:**
- `index.html` — Ofertas com filtros
- `dashboard.html` — Estatísticas e gráficos
- `aviso.html` — Aviso de afiliado (compliance)

**Funcionalidades (index.html):**
- **Filtros:** Busca textual, Plataforma (ML/Shopee/Todas), Período (72h/24h/7d/Todo), Ordenação (Maior desconto, Mais recentes, Menor/Maior preço)
- **Botão "Limpar"** para resetar filtros
- Cards responsivos (mobile-first: 1 col → 4 col desktop)
- Preço anterior riscado, preço novo verde, badge `% OFF` vermelho/laranja
- Badge de plataforma (ML/Shopee) em cada card
- Info de resultados: "X de Y ofertas" + "Atualizado Xh atrás"
- Estados: loading (spinner), empty (ilustração), erro (toast + retry)
- Dark mode automático (`prefers-color-scheme`)
- **SEO/Open Graph:** meta tags para título, descrição, imagem, Twitter Card
- **Favicon:** SVG + ICO + Apple touch icon
- Security headers via `_headers` (CSP, HSTS, etc.)
- **Rodapé com aviso de afiliado** + links para Dashboard e Aviso

**Dashboard (dashboard.html):**
- Cards de estatísticas: Total, ML, Shopee, Maior desconto, Desconto médio, Últimas 24h
- Gráfico de barras SVG: Ofertas por dia (últimos 14 dias) — empilhado ML + Shopee
- Gráfico de barras SVG: Ofertas por plataforma
- Top 10 maiores descontos (ranking com medalhas ouro/prata/bronze)
- Badge de plataforma em cada linha

**Aviso de Afiliado (aviso.html):**
- Página dedicada explicando programa de afiliados
- Transparência: comissão paga pelo marketplace, não pelo usuário
- Preços podem mudar sem aviso
- Link de volta para ofertas

**Deploy:**
```bash
wrangler pages deploy site --project-name promocoes-zart
```

**Configuração no `site/app.js` / `dashboard.js`:**
```javascript
const SUPABASE_CONFIG = {
    url: 'https://innyohbvgtsoihooykxp.supabase.co',
    anonKey: 'sb_publishable_Ryxrj3xL0wShOOwx2vGaRA_QH7SLzRW',
    table: 'ofertas_encontradas',
    select: 'produto_id,titulo,preco_anterior,preco_novo,queda_pct,link,criado_em,plataforma',
    order: 'criado_em.desc',
    limit: 200
};
```

**RLS no Supabase (leitura pública):**
```sql
ALTER TABLE ofertas_encontradas ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Public read access" ON ofertas_encontradas
    FOR SELECT USING (true);
```

---

## Testes

**Total: 84 testes** - todos passando

| Arquivo | Testes | Cobertura |
|---------|--------|-----------|
| `test_mercado_livre.py` | 18 | OAuth sucesso, cache token, 401 limpa cache, sem credenciais, timeout token, erro conexão token, HTTP error token, JSON inválido token, sem access_token, sucesso busca, limite padrão, filtra campos vazios, timeout busca, erro conexão busca, HTTP error busca, 401 limpa cache, JSON inválido busca, results não-lista |
| `test_shopee.py` | 14 | Signature HMAC, payload GraphQL, sucesso, limite padrão, filtra sem link, sem credenciais, erro GraphQL, JSON inválido, campo ausente, nodes não-lista, timeout, conexão, HTTP error |
| `test_links.py` | 7 | ML com tag, ML sem tag (warning), ML query existente, Shopee retorna original, Amazon exceção, plataforma desconhecida, item sem link |
| `test_armazenamento.py` | 13 | Buscar preço (ML/Shopee encontrado/não existe/sem creds/erro rede), salvar produto (ML/Shopee completo/sem preco_anterior), salvar oferta (ML/Shopee completa/sem link), erros Supabase (HTTP 401, timeout) |
| `test_orquestrador.py` | 18 | Cálculo queda, rodar ML/Shopee (oferta/sem queda/sem preço salvo/múltiplos/erros), múltiplas plataformas, erros ML/Shopee, main CLI |
| `test_whatsapp.py` | 7 | Enviar mensagem sucesso, sem credenciais, timeout, erro HTTP, enviar oferta sucesso, sem credenciais retorna None |
| `test_mensagens.py` | 7 | Formatar oferta ML/Shopee/desconhecida, campos faltando, resumo vazio/1/múltiplas, truncamento título |

**Padrão:** Mocks de `requests` via `unittest.mock.patch`, sem chamadas reais a APIs externas.

---

## Qualidade de Código

### Ferramentas configuradas

| Ferramenta | Comando | Config |
|------------|---------|--------|
| **ruff** | `ruff check src tests` | lint + import sort, 100 cols, target py310, ignora N818 |
| **black** | `black src tests` | format, 100 cols, double quotes |
| **mypy** | `python -m mypy src` | strict mode, explicit package bases |
| **pytest** | `pytest` | 81 testes, cobertura implícita |

### pyproject.toml - pontos chave
```toml
[project.optional-dependencies]
dev = ["pytest", "ruff", "black", "mypy", "types-requests"]

[tool.ruff]
line-length = 100
select = ["E","W","F","I","N","UP","B","C4","T20"]
ignore = ["E501", "N818"]

[tool.black]
line-length = 100

[tool.mypy]
python_version = "3.10"
disallow_untyped_defs = true
ignore_missing_imports = true
explicit_package_bases = true
```

---

## Variáveis de Ambiente (.env)

```bash
SUPABASE_URL=https://innyohbvgtsoihooykxp.supabase.co
SUPABASE_KEY=sb_publishable_Ryxrj3xL0wShOOwx2vGaRA_QH7SLzRW
ML_AFFILIATE_TAG=seu-tag-mercado-livre
AMAZON_AFFILIATE_TAG=seu-tag-amazon  # futuro
SHOPEE_APP_ID=seu-app-id-shopee
SHOPEE_APP_SECRET=seu-app-secret-shopee
ML_CLIENT_ID=seu-client-id-ml
ML_CLIENT_SECRET=seu-client-secret-ml
EVOLUTION_API_URL=https://sua-evolution-api.com
EVOLUTION_API_KEY=sua-api-key
EVOLUTION_INSTANCE_NAME=sua-instancia
WHATSAPP_GROUP_ID=123456789@g.us
```

---

## Como Rodar

```bash
# Instalar deps
pip install -e ".[dev]"

# Rodar testes
pytest -v

# Lint + format + type-check
ruff check src tests
black src tests
python -m mypy src

# Executar busca (CLI) - Mercado Livre
python main.py --termo "fone bluetooth" --queda 10

# Executar busca (CLI) - Shopee
python main.py --termo "celular" --queda 15 --plataformas shopee

# Executar busca (CLI) - Ambas + WhatsApp
python main.py --termo "promocao" --queda 10 --plataformas mercado_livre shopee --whatsapp

# Agendador automático (loop contínuo)
python agendador.py                    # padrão: termos.json, 60 min
python agendador.py --intervalo 30     # a cada 30 min
python agendador.py --termos meus.json --intervalo 45

# Deploy site (Pages)
wrangler pages deploy site --project-name promocoes-zart
```

---

## Como Retomar Amanhã (Guia Rápido)

1. **Ative o ambiente virtual** (se usar): `venv\Scripts\activate`
2. **Verifique se o `.env` está preenchido** com todas as credenciais (incluindo `ML_CLIENT_ID/SECRET` e opcional WhatsApp)
3. **Rode os testes**: `pytest -q` (deve dar **84 passed**)
4. **Execute uma busca teste**: `python main.py --termo "teste" --queda 10`
5. **Inicie o agendador**: `python agendador.py --intervalo 60`
6. **Deploy do site** (se mudou algo no `site/`): `wrangler pages deploy site --project-name promocoes-zart`

### Logs
- Logs estruturados em `logs/afiliados.log` (rotação automática 5MB, 3 backups)
- Console mostra resumo colorido com timestamps

### Banco de dados (Supabase)
- Tabelas: `produtos_rastreados`, `ofertas_encontradas`
- Coluna `plataforma` em ambas para multi-plataforma
- RLS habilitado para leitura pública em `ofertas_encontradas`

### Notas importantes
- Pacote instalado em modo editável (`pip install -e .`)
- Para mypy funcionar com pacote instalado: `pip uninstall -y afiliados` antes do `mypy src`
- Imports usam `from afiliados.modulo import ...` (nome do pacote)
- Testes usam `patch("afiliados.modulo.funcao")` para mocks
- `.env` e `logs/` estão no `.gitignore` — nunca commitar credenciais ou logs
- **Site:** Worker antigo em `promocoes-zart.iwebb.workers.dev` pode ser deletado no dashboard
- **Shopee:** Requer cadastro no Shopee Affiliate Program e aprovação para Open API
- **Mercado Livre:** Requer app criado no developers.mercadolivre.com com client_credentials

---

## Próximos Passos Sugeridos

1. **Amazon Associates** em `links.py` (associate tag + `tag=` parameter)
2. **Telegram notifications** — novo módulo `notificacoes.py`
3. **GitHub Actions** para agendador (não depender de Windows Task Scheduler)
4. **Rate limiting adaptativo** por plataforma
5. **Métricas Prometheus/Grafana** para observabilidade

---

## Último Deploy Completo
```bash
# Testes
pytest -q
# 84 passed

# Qualidade
ruff check src tests && black src tests && python -m mypy src

# Deploy site
wrangler pages deploy site --project-name promocoes-zart
# https://promocoes-zart.pages.dev
# https://promocoes-zart.pages.dev/dashboard.html
# https://promocoes-zart.pages.dev/aviso.html
```