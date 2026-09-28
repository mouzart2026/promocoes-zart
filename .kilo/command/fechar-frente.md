# Regra: Fechar Frente

**Gatilho:** Quando o usuário disser "fechar frente" (ou "fechar frente: <nota>")

**Procedimento obrigatório:**

1. **Checks**: Rode lint/typecheck/build/test do projeto (ou uma checagem leve).
   - `ruff check src tests`
   - `black src tests`
   - `pytest -q`

2. **Segredos**: Procure chaves/tokens/senhas em arquivos versionáveis e confira o `.gitignore`. Nunca commitar segredo.

3. **Git**: Mostre `git status` e resumo do `git diff`; sugira um commit, sem commitar sem permissão do usuário.

4. **Status**: Crie/atualize `STATUS-<data>.md` (feito hoje, decisões, pendências, bloqueios, próximos passos, credenciais sensíveis a guardar).

5. **AGENTS.md**: Proponha atualização se regras/pastas/convenções mudaram.

6. **Todo**: Marque o concluído e deixe o pendente listado.

7. **Portfólio**: Atualize **SOMENTE** a entrada deste projeto em `C:\Gestão Zart\Projetos\portfolio.json` (leia, altere só o seu objeto, grave; se não existir, crie com `publico=false`; nunca sobrescreva os outros). Atualize resumo, status, `ultima_atualizacao` (hoje) e `entregas_recentes` com o concluído nesta frente. Texto público e genérico: sem credenciais, chaves, URLs internas, dados de clientes ou detalhes de segurança. Não altere o campo "publico". Peça confirmação do usuário e rode `C:\Gestão Zart\Projetos\publicar-portfolio.ps1`.

**Encerramento**: Resumo curto — estado do repositório, o que ficou pronto, pendências e o **primeiro passo da próxima sessão** (uma linha, para o `/abrirfrente`).

---

*Arquivo: `.kilo/command/fechar-frente.md`*
*Projeto: Renda com Internet - Automação Afiliados*