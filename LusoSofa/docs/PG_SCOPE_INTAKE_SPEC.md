# PG_SCOPE_INTAKE_SPEC

`PG_SCOPE_INTAKE.yaml` e um ficheiro local ao projeto.
Serve como fonte estruturada para semear e atualizar os blocos auto-geridos do `PG_CONTEXT.md`.

Não substitui o `PG_CONTEXT.md`.
O `PG_CONTEXT.md` continua a ser a memória funcional e decisória do projeto.

## Finalidade

Usar este ficheiro para registar de forma mais estruturada:

- identificação do projeto
- fase atual
- edição e ambiente
- restrições contratuais
- objetivo de negocio
- pedido atual
- processo atual
- trigger, frequência, volumes e urgência
- utilizadores, papeis, exceções e aprovações
- documentos, integrações e reporting
- o que já foi tentado no standard
- porque isso foi considerado insuficiente

## Como usar

1. O bootstrap copia `PG_SCOPE_INTAKE.yaml` para o repositório do projeto.
2. `scripts/pg_init_scope_intake.ps1` pode inicializar o ficheiro.
3. A equipa preenche ou reve o intake.
4. `scripts/pg_build_pg_context.ps1` atualiza os blocos auto-geridos do `PG_CONTEXT.md`.

## Regra de ownership

- `PG_SCOPE_INTAKE.yaml` e local ao projeto
- pode ser atualizado manualmente pela equipa
- pode ser usado como input estruturado antes de discovery, proposta ou refinamento do contexto
- não deve ser promovido automaticamente para memória global reutilizável
