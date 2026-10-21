# Começar aqui

Este repositório está preparado para testes manuais/on-premise de instalação, adaptação e validação de addons customizados Odoo 17 em Odoo 18.

## Fluxo esperado

O trabalho é iterativo:

```text
Documentar erro -> corrigir/adaptar -> testar novamente -> documentar novo erro ou validar comportamento -> repetir
```

Corrigir o primeiro erro que aparece não significa que o módulo esteja migrado. Depois de cada correção, é obrigatório voltar a testar a instalação/atualização. Se instalar sem erro, validar também se o comportamento do módulo continua equivalente ao esperado face à versão Odoo 17.

## O que tens de fazer

1. Coloca ou atualiza os addons customizados em `custom_addons/`.
2. Testa a instalação/atualização dos módulos no teu ambiente Odoo 18.
3. Quando encontrares um erro, copia o bloco abaixo para o Codex ou Claude.
4. Cola o traceback/log completo no campo indicado.
5. Pede ao agente para documentar o erro e propor/aplicar uma correção focada.
6. Depois da correção, volta a executar o mesmo teste.
7. Se surgir novo erro, repete o processo.
8. Se a instalação passar, valida o comportamento funcional do módulo e devolve feedback ao agente.

Não precisas de preencher JSON, CSV ou taxonomias manualmente. O agente faz isso.

## Prompt para copiar para Codex/Claude quando encontrares erro

```text
Estou a testar a instalação/migração de addons customizados Odoo 17 em Odoo 18.

Módulo testado:
<nome_do_modulo>

Fase:
<instalação módulo / atualização módulo / arranque servidor / abertura de view / teste funcional / relatório / permissões / outro>

Comando executado:
<colar comando, se aplicável>

Erro completo:
<colar traceback/log completo>

Contexto funcional:
<o que estavas a tentar fazer>

Resultado esperado:
<o que deveria acontecer>

Resultado obtido:
<o que aconteceu>

Pedido ao agente:
1. Documenta este erro seguindo AGENTS.md.
2. Identifica a causa provável com base no erro e no código do repositório.
3. Propõe ou aplica uma correção focada no módulo afetado.
4. Atualiza migration-docs/ com o erro, causa provável, correção aplicada/proposta e próximo teste recomendado.
5. Se a causa raiz não for certa, marca como provável ou desconhecida.
6. Verifica se é duplicado de erro já existente.
7. No final, indica o MIG-XXXX criado/atualizado, severidade, camada técnica provável, correção aplicada/proposta e o comando/teste que devo repetir.
```

## Prompt para colar depois de uma correção

```text
Resultado do reteste após a correção anterior.

Módulo testado:
<nome_do_modulo>

Comando repetido:
<colar comando>

Resultado:
<instalou com sucesso / voltou a falhar / apareceu novo erro>

Novo erro, se existir:
<colar traceback/log completo>

Validação funcional, se a instalação passou:
<indicar se o comportamento parece igual ao Odoo 17 ou que diferenças foram encontradas>

Pedido ao agente:
Atualiza a documentação do erro anterior com o resultado do reteste.
Se apareceu novo erro, documenta como novo MIG-XXXX ou duplicado, seguindo AGENTS.md.
Se a instalação passou, regista a validação funcional ou as diferenças encontradas.
Indica a próxima ação recomendada.
```

## Exemplo rápido

```text
Estou a testar a instalação/migração de addons customizados Odoo 17 em Odoo 18.

Módulo testado:
custom_sale_margin

Fase:
instalação módulo

Comando executado:
odoo-bin -d teste18 -i custom_sale_margin --stop-after-init

Erro completo:
Element '<xpath expr="//field[@name='amount_total']">' cannot be located in parent view

Contexto funcional:
Tentativa de instalar o módulo custom de margem em vendas.

Resultado esperado:
O módulo deveria instalar e a view de venda deveria abrir normalmente.

Resultado obtido:
A instalação falha no carregamento da view herdada.

Pedido ao agente:
1. Documenta este erro seguindo AGENTS.md.
2. Identifica a causa provável com base no erro e no código do repositório.
3. Propõe ou aplica uma correção focada no módulo afetado.
4. Atualiza migration-docs/ com o erro, causa provável, correção aplicada/proposta e próximo teste recomendado.
5. Se a causa raiz não for certa, marca como provável ou desconhecida.
6. Verifica se é duplicado de erro já existente.
7. No final, indica o MIG-XXXX criado/atualizado, severidade, camada técnica provável, correção aplicada/proposta e o comando/teste que devo repetir.
```

## Onde ficam os resultados

O agente vai atualizar:

```text
migration-docs/migration_errors.jsonl
migration-docs/migration_errors.csv
migration-docs/root_causes.json
migration-docs/errors/MIG-XXXX.md
migration-docs/summaries/
```

## Regra importante

O objetivo não é apenas corrigir o primeiro erro. O objetivo é chegar a um módulo que instala em Odoo 18 e cujo comportamento funcional foi validado. Cada erro, correção, reteste e diferença funcional relevante deve ficar documentado.