# Parâmetro Global - Setup global para projetos Odoo

Este documento descreve a configuração de máquina esperada para trabalhar com o template consultivo Odoo.

## Estrutura recomendada

Repositórios:
`C:\Users\Utilizador\Desktop\Repos`

Cada projeto bootstrapado deve guardar o source Odoo no próprio repositório:

```text
NOME_DO_REPO\
|-- vendor\
|   `-- odoo_src\
|       |-- community
|       `-- enterprise
`-- .pg_framework
```

## Regras globais

- o source Odoo e apenas referência técnica
- nunca alterar `vendor/odoo_src`
- nunca versionar `vendor/odoo_src` em Git
- cada projeto deve apontar para uma única versão ativa
- a versão real deve ser detetada a partir do checkout em `vendor/odoo_src/community` e sincronizada para `PG_CONTEXT.md`

## Fontes de verdade

Sempre que houver duvida ou conflito, prevalece:
1. código do projeto
2. `vendor/odoo_src`
3. `PG_CONTEXT.md`
4. documentação oficial da mesma versão
