# Odoo 17 -> 18 migration documentation

Este repositório serve para apoiar testes manuais/on-premise de instalação e adaptação de addons customizados Odoo 17 em Odoo 18.

O objetivo **não** é executar a migração dentro do GitHub. O objetivo é centralizar:

- os addons customizados a testar;
- o feedback bruto dos erros encontrados pelo colega;
- os logs, tracebacks e notas de teste;
- a documentação estruturada gerada por Codex ou Claude.

## Fluxo de trabalho

1. Colocar os addons customizados em `custom_addons/`.
2. Testar a instalação/atualização dos módulos num ambiente Odoo 18 local, on-premise ou de teste.
3. Quando surgir um erro, copiar/colar o erro diretamente no Codex ou Claude usando o template em `COLLEAGUE_START_HERE.md`.
4. O agente lê `AGENTS.md` ou `CLAUDE.md`, consulta o repo se necessário e documenta o erro em `migration-docs/`.
5. O colega continua os testes e repete o processo para cada erro encontrado.

## Estrutura principal

```text
custom_addons/          Addons custom Odoo 17 a testar/adaptar em Odoo 18
migration-feedback/    Feedback bruto opcional, logs e notas por execução
migration-docs/        Documentação estruturada mantida pelo agente
scripts/               Validação e análise da documentação
AGENTS.md              Regras para Codex
CLAUDE.md              Regras para Claude Code
COLLEAGUE_START_HERE.md Template que o colega copia para o agente
```

## Dados do projeto

- Versão origem dos addons: Odoo 17
- Versão destino: Odoo 18
- Colaborador previsto: `joao-barros-pg`
- Branch base: `main`

## Resultado esperado

No fim dos testes, `migration-docs/` deve permitir analisar:

- módulos com mais erros;
- tipos de erro mais frequentes;
- fases mais problemáticas;
- causas raiz recorrentes;
- severidade dos problemas;
- duplicados;
- recomendações para adaptação dos addons.

## Ficheiros principais

- `migration-docs/migration_errors.jsonl` - fonte estruturada principal.
- `migration-docs/migration_errors.csv` - versão tabular para Excel/Sheets.
- `migration-docs/root_causes.json` - agrupamento por causa raiz.
- `migration-docs/errors/MIG-XXXX.md` - fichas detalhadas para erros importantes.
- `migration-docs/summaries/` - resumos por ciclo de teste.

## Nota importante

O agente deve documentar, classificar e agrupar os erros. Não deve alterar código dos addons sem pedido explícito.