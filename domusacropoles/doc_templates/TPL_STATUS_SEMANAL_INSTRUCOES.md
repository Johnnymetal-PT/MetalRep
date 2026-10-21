# TPL_STATUS_SEMANAL_INSTRUCOES.md

# Instruções ao Agente — Status Semanal (com Adoção Odoo)

> Ficheiro de instrução ao agente (Claude/Codex/Gemini). NÃO é um template de
> output: o seu conteúdo nunca deve ser copiado para o documento final.

## Quando aplicar
Quando, num repositório de cliente, for pedido um "status semanal" / "ponto de
situação semanal" ou equivalente. Produzido a pedido (via prompt), não agendado.

## Onde corre o workflow de adoção
O workflow de adoção é **infraestrutura**: vive na **default branch** do repo do
cliente (único sítio de onde o `workflow_dispatch` fica disponível) e é de lá que
se despacha. Os dados de adoção vêm do Odoo e **não dependem da branch de
trabalho** — podes pedir o status a partir de qualquer branch (incluindo de
teste); o report é gerado na mesma. A branch em uso só importa para onde gravar o
documento final, se o pedires (nunca commitar o report automaticamente).

## Como produzir o documento
1. Usar a estrutura de `TPL_STATUS_SEMANAL_V1.md` (Cabeçalho + secções 1–11).
2. Preencher 1–11 a partir do `PG_CONTEXT.md` e das fontes do projeto (`.pg/...`),
   seguindo as regras do `AGENTS_SHARED.md`. Marcar lacunas como `[POR VALIDAR]`.
3. **Secção 12 — Adoção Odoo (automática, nunca inventada):**
   - Verificar se existe `.github/workflows/pg_weekly_status_adoption.yml` na
     **default branch** e se estão definidos `PG_TEMPLATE_REF` (var) e os secrets
     `PG_ODOO_BASE_URL`, `PG_ODOO_DATABASE`, `PG_ODOO_LOGIN`,
     `PG_ODOO_KNOWLEDGE_TOKEN`.
   - Se faltar o workflow na default branch: provisioná-lo via
     `.pg_framework/scripts/pg_sync_shared_assets.ps1` e commit/push para a
     **default branch** (commit de infraestrutura, único).
   - Se faltarem secrets/vars: parar e encaminhar para o Brodoo
     (`pg.ai.repository` → "Sincronizar Adoção → GitHub"). Não inventar.
   - Disparar: `gh workflow run pg_weekly_status_adoption.yml --repo <owner>/<repo> --ref <default branch>`.
   - Aguardar: `gh run watch <run_id> --repo <owner>/<repo> --exit-status`.
   - Descarregar: `gh run download <run_id> --repo <owner>/<repo> --name status-semanal-with-adoption --dir <tmp>`.
   - Extrair de `handoff/STATUS_SEMANAL_WITH_ADOPTION.md` o bloco entre
     `<!-- PG_AUTO:WEEKLY_ADOPTION:START -->` e `<!-- PG_AUTO:WEEKLY_ADOPTION:END -->`.
4. Montar o documento final: secções 1–11 + secção 12 (bloco obtido).
5. Apresentar ao utilizador. **Não commitar automaticamente** — só gravar/commitar
   se o utilizador o pedir.

## Notas
- O pull de adoção é **só de leitura**; não altera a base de dados do cliente.
- Janela = últimos 30 dias; tabela por **Utilizador × App × Documentos**.
- Se o workflow falhar com `Access Denied`, corrigir a ligação Odoo no Brodoo e
  re-sincronizar, depois repetir.
- Requisitos: `gh` autenticado; `PG_TEMPLATE_REF` a apontar para um runtime com o
  suporte de adoção.
