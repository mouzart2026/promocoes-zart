# Promoções Zart - Site Estático

Site estático (HTML/CSS/JS puro) que exibe ofertas de afiliados consumindo a tabela `ofertas_encontradas` do Supabase via REST API.

## Estrutura

```
site/
├── index.html      # HTML principal
├── styles.css      # Estilos (mobile-first, sem framework)
├── app.js          # Lógica de fetch + render
```

## Configuração Obrigatória

Antes de fazer deploy, edite `site/app.js` e substitua os valores placeholder em `SUPABASE_CONFIG`:

```javascript
const SUPABASE_CONFIG = {
    url: 'https://SEU_PROJETO.supabase.co',     // ← Sua URL do Supabase
    anonKey: 'SEU_ANON_KEY_AQUI',               // ← Chave anon/publishable (segura p/ expor)
    table: 'ofertas_encontradas',
    // ... resto mantém igual
};
```

**Onde encontrar:**
- URL: Supabase Dashboard → Settings → API → Project URL
- Anon Key: Supabase Dashboard → Settings → API → `anon` / `public` key

> ⚠️ **Nunca use a `service_role` key no frontend!** Apenas a `anon`/`publishable`.

## Deploy no Cloudflare Pages

### Opção 1: Via Dashboard (Recomendado - sem CLI)

1. Acesse [dash.cloudflare.com](https://dash.cloudflare.com) → **Pages**
2. Clique em **"Create a project"** → **"Upload assets"**
3. Nome do projeto: `promocoes-zart` (ou seu preferido)
4. Arraste a pasta **`site/`** inteira para a área de upload
5. Clique em **"Deploy site"**
6. Pronto! Seu site estará em `https://promocoes-zart.pages.dev`

### Opção 2: Via Wrangler CLI

**Pré-requisitos:**
```bash
npm install -g wrangler
# ou: pnpm add -g wrangler / yarn global add wrangler
```

**Login (uma vez):**
```bash
wrangler login
# Abre navegador para autorizar acesso à sua conta Cloudflare
```

**Deploy:**
```bash
# Na raiz do projeto (onde está wrangler.toml)
wrangler pages deploy site
```

**Deploy com preview (branch):**
```bash
wrangler pages deploy site --branch=minha-branch
```

### Opção 3: Git Integration (CI/CD automático)

1. Faça push deste repositório para GitHub/GitLab
2. No Cloudflare Pages → "Connect to Git"
3. Selecione o repo
4. Build settings:
   - **Build command:** (deixe vazio)
   - **Build output directory:** `site`
   - **Root directory:** `/` (raiz do repo)
5. Deploy automático a cada push na `main`

## Variáveis de Ambiente (Opcional)

Se preferir não hardcodar no `app.js`, configure no Cloudflare Pages Dashboard:

1. Pages → seu projeto → **Settings** → **Environment variables**
2. Adicione:
   - `SUPABASE_URL` = `https://seu-projeto.supabase.co`
   - `SUPABASE_ANON_KEY` = `sua-anon-key`
3. No `app.js`, leia via `window.ENV` (requer pequeno ajuste no JS)

## Supabase - Configuração de Acesso Público

Para o site conseguir ler a tabela, a tabela `ofertas_encontradas` precisa ter **política de leitura pública** (RLS):

```sql
-- No SQL Editor do Supabase
ALTER TABLE ofertas_encontradas ENABLE ROW LEVEL SECURITY;

-- Política: permitir SELECT público (apenas leitura)
CREATE POLICY "Public read access" ON ofertas_encontradas
    FOR SELECT USING (true);
```

> Isso permite que a `anon key` leia a tabela sem autenticação de usuário.

## Personalização

### Cores
Edite as variáveis CSS em `styles.css` (`:root`):
```css
:root {
    --color-accent: #e84d2a;      /* Cor principal (descontos) */
    --color-accent-hover: #d03d1f;
    --color-success: #16a34a;     /* Preço novo */
}
```

### Limite de ofertas
Em `app.js`, altere `limit: 50` no `SUPABASE_CONFIG`.

### Ordenação
Mude `order: 'criado_em.desc'` para `'queda_pct.desc'` se quiser maiores descontos primeiro.

## Testes Locais

```bash
# Na pasta site/
npx serve .
# ou
python -m http.server 8000
# Abre http://localhost:8000
```

## Troubleshooting

| Problema | Solução |
|----------|---------|
| "Failed to fetch" / CORS | Verifique se a tabela tem RLS com policy de SELECT público |
| Dados não aparecem | Confirme `url` e `anonKey` corretos no `app.js` |
| Erro 401/403 | Chave `anon` incorreta ou policy RLS bloqueando |
| Deploy falha no CLI | Rode `wrangler login` novamente ou use upload manual |

## Licença

MIT - Use livremente para seus projetos de afiliados.