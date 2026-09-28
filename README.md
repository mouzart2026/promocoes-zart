# Automação de Marketing de Afiliados

Projeto para captação de ofertas em marketplaces (Mercado Livre e Shopee), geração de links de afiliado, armazenamento no Supabase, site estático no Cloudflare Pages, dashboard, notificações WhatsApp e agendador automático.

## URLs de Produção

| Serviço | URL |
|---------|-----|
| **Site (Cloudflare Pages)** | https://promocoes-zart.pages.dev |
| **Dashboard** | https://promocoes-zart.pages.dev/dashboard.html |
| **Aviso de Afiliado** | https://promocoes-zart.pages.dev/aviso.html |
| Supabase (backend) | https://innyohbvgtsoihooykxp.supabase.co |

## Funcionalidades

- 🔍 **Busca multi-plataforma**: Mercado Livre (REST API + OAuth) e Shopee (GraphQL + HMAC-SHA256)
- 🔗 **Links de afiliado**: ML (`matt_tool`), Shopee (já vem com tracking), Amazon (planejado)
- 💾 **Armazenamento**: Supabase REST API com suporte multi-plataforma
- 📊 **Dashboard**: Estatísticas, gráficos de ofertas por dia/plataforma, top 10 descontos
- 📱 **WhatsApp**: Envio via Evolution API (opcional)
- 🛡 **Qualidade**: Deduplicação (24h), filtro preço zero/absurdo, preço min/max por termo
- 🎨 **Site**: Filtros (plataforma, busca, período, ordenação), SEO/Open Graph, dark mode
- ⚖ **Compliance**: Aviso de afiliado obrigatório, rodapé em todas as páginas
- ⏰ **Agendador**: Loop contínuo configurável via `termos.json`
- 🧪 **Testes**: 81 testes (mockados, sem chamadas reais)
- ✨ **Qualidade**: ruff, black, mypy (strict)

## Estrutura

```
src/
  afiliados/           # Pacote principal
    mercado_livre.py   # API ML com OAuth client_credentials
    shopee.py          # Shopee GraphQL + HMAC
    links.py           # Geração de links afiliado
    armazenamento.py   # Supabase REST API
    orquestrador.py    # Fluxo principal multi-plataforma
    whatsapp.py        # Evolution API integration
    mensagens.py       # Formatadores WhatsApp
    http_utils.py      # Retry + logging estruturado
site/                  # Site estático (Cloudflare Pages)
  index.html           # Página principal com filtros
  dashboard.html       # Dashboard de estatísticas
  aviso.html           # Aviso de afiliado (compliance)
  app.js               # Lógica do site (filtros, busca)
  dashboard.js         # Lógica do dashboard
  styles.css           # Estilos compartilhados
  favicon.svg          # Favicon
agendador.py           # Agendador loop contínuo
termos.json            # Configuração termos de busca
main.py                # CLI execução única
```

## Configuração

1. Copie `.env.example` para `.env` e preencha as variáveis:
   ```bash
   copy .env.example .env
   # Edite .env com suas credenciais
   ```

2. Instale as dependências:
   ```bash
   pip install -e ".[dev]"
   ```

3. Configure os termos de busca em `termos.json` (suporta `preco_minimo` e `preco_maximo` por termo).

### Variáveis de Ambiente (.env)

| Variável | Descrição | Obrigatória |
|----------|-----------|-------------|
| `SUPABASE_URL` | URL do projeto Supabase | Sim |
| `SUPABASE_KEY` | Chave anon/public do Supabase | Sim |
| `ML_AFFILIATE_TAG` | Tag de afiliado ML (matt_tool) | Para ML |
| `ML_CLIENT_ID` | Client ID OAuth ML | Para ML |
| `ML_CLIENT_SECRET` | Client Secret OAuth ML | Para ML |
| `SHOPEE_APP_ID` | App ID Shopee Affiliate | Para Shopee |
| `SHOPEE_APP_SECRET` | App Secret Shopee Affiliate | Para Shopee |
| `EVOLUTION_API_URL` | URL da Evolution API | Para WhatsApp |
| `EVOLUTION_API_KEY` | API Key Evolution | Para WhatsApp |
| `EVOLUTION_INSTANCE_NAME` | Nome da instância | Para WhatsApp |
| `WHATSAPP_GROUP_ID` | ID do grupo WhatsApp | Para WhatsApp |

## Execução

### Execução única (CLI)
```bash
# Mercado Livre
python main.py --termo "notebook gamer" --queda 15

# Shopee
python main.py --termo "celular" --queda 10 --plataformas shopee

# Ambas
python main.py --termo "promocao" --queda 10 --plataformas mercado_livre shopee

# Com WhatsApp
python main.py --termo "fone" --queda 15 --plataformas mercado_livre shopee --whatsapp
```

### Agendador automático (loop contínuo)
```bash
# Usa termos.json e intervalo padrão de 60 min
python agendador.py

# Intervalo personalizado
python agendador.py --intervalo 30

# Arquivo de termos personalizado
python agendador.py --termos meus_termos.json --intervalo 45
```

### termos.json — Configuração avançada
```json
{
  "termos": [
    {
      "termo": "notebook gamer",
      "queda_minima_pct": 15.0,
      "plataformas": ["mercado_livre", "shopee"],
      "preco_minimo": 2000.0,
      "preco_maximo": 15000.0
    }
  ],
  "configuracao_padrao": {
    "intervalo_minutos": 60,
    "log_level": "INFO"
  }
}
```

### Agendador no Windows (Task Scheduler) — Rodar em segundo plano
Veja a seção completa no README original.

## Deploy do Site (Cloudflare Pages)
```bash
wrangler pages deploy site --project-name promocoes-zart
```

## Testes e Qualidade
```bash
pytest -v          # 81 testes
ruff check src tests
black src tests
python -m mypy src
```

## Como retomar amanhã

1. **Ative o ambiente virtual** (se usar): `venv\Scripts\activate`
2. **Verifique se o .env está preenchido** com as credenciais
3. **Rode os testes**: `pytest -q` (deve dar 81 passed)
4. **Execute uma busca teste**: `python main.py --termo "teste" --queda 10`
5. **Inicie o agendador**: `python agendador.py --intervalo 60`
6. **Deploy do site** (se mudou algo no site/): `wrangler pages deploy site --project-name promocoes-zart`

### Logs
- Logs estruturados em `logs/afiliados.log` (rotação automática 5MB, 3 backups)
- Console mostra resumo colorido

### Banco de dados (Supabase)
- Tabelas: `produtos_rastreados`, `ofertas_encontradas`
- Coluna `plataforma` em ambas para multi-plataforma
- RLS habilitado para leitura pública em `ofertas_encontradas`

### Próximos passos sugeridos
- [ ] Amazon Associates integration
- [ ] Telegram notifications
- [ ] GitHub Actions para agendador (não depender de Windows)
- [ ] Rate limiting adaptativo
- [ ] Métricas Prometheus/Grafana