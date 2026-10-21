# PG_IMPLEMENTATION_CONTINUITY_PROTOCOL

## Objetivo

Definir um protocolo curto e repetível para qualquer futura implementação deste trabalho, de modo a que a pergunta `qual o proximo passo logico?` tenha sempre resposta objetiva sem depender do histórico do chat.

## Regra de continuidade

Para qualquer `IMP`, `REP` novo ou ronda corretiva:

1. confirmar contexto operativo
2. implementar no repo canónico
3. testar no repo canónico
4. propagar para o repo de deploy
5. fazer `Upgrade` no Odoo
6. repetir o sync relevante no piloto
7. medir no repo de destino
8. documentar o resultado

Nenhuma iteração fica considerada fechada antes do passo 7.

## Passo 0 - Confirmar contexto operativo

Antes de mexer em código, confirmar:

- source of truth: `_pg_template`
- repo de deploy do addon: `Parametro_Global/TesteExo`
- repo de destino factual do espelho do piloto: `ancoravip/teste`
- piloto ativo: `Odoo - Ancoravip Produção`

Documento de referência:
- `docs/PG_CURRENT_WORKING_STATE.md`

## Passo 1 - Implementar no repo canónico

Local:
- `C:\Users\Utilizador\Desktop\Repos\_pg_template`

Objetivo:
- aplicar a alteração no source of truth

Obrigatório:
- ler o código atual relevante
- atualizar docs se a iteração mudar regras ou topologia
- fazer branch de trabalho dedicada quando a ronda o justificar

## Passo 2 - Testar no repo canónico

Objetivo:
- garantir que a alteração passa nos testes certos antes de sair do source of truth

Mínimo esperado:
- testes focados nos ficheiros alterados
- quando aplicável, suite do addon

Regra:
- uma iteração não deve seguir para deploy sem verificação mínima no repo canónico

## Passo 3 - Propagar para o repo de deploy

Local:
- `C:\Users\Utilizador\Desktop\Repos\Parametro_Global`

Branch:
- `TesteExo`

Objetivo:
- levar para o Odoo.sh apenas o delta necessário do addon ou da framework relevante

Regra:
- sempre que o worktree principal estiver sujo, usar um worktree limpo para a propagação

## Passo 4 - Fazer `Upgrade` no Odoo

Local de execução:
- Odoo.sh / base de staging ou teste

Objetivo:
- garantir que o runtime do addon no Odoo já usa a nova versão

Regra:
- sem `Upgrade`, não ha validação real de comportamento novo

## Passo 5 - Repetir o sync relevante no piloto

Projeto:
- `Odoo - Ancoravip Produção`

Sequência mínima:

1. executar o onboarding ou migração necessária quando a iteração tocar no circuito de espelho
2. correr o `mirror sync` ou publish factual relevante no projeto piloto
3. confirmar atualização dos artefactos do espelho no repo factual
4. confirmar refresh do `PG_CONTEXT.md` quando aplicável

Regra:
- quando a iteração mexer no espelho, repetir o `mirror sync`
- quando a iteração mexer apenas em artefactos factuais legados, repetir o publish factual relevante

## Passo 6 - Medir no repo de destino

Local:
- `C:\Users\Utilizador\Desktop\Repos\ancoravip`

Branch:
- `teste`

Objetivo:
- observar o efeito real no espelho factual e no `PG_CONTEXT.md`

O que medir:
- novos commits de espelho e contexto
- diff dos artefactos factuais afetados
- warnings do `smoke test`
- melhoria ou regressão do problema alvo

## Passo 7 - Documentar a iteração

Objetivo:
- fechar a ronda sem depender da memória do operador

Mínimo a registar:
- commit do repo canónico
- commit do repo de deploy
- commits do espelho/contexto no repo de destino
- resultado dos testes
- resultado do smoke
- residuos ou riscos

Documentos onde registar:
- backlog do `IMP` ou `REP` ativo
- nota técnica da intervenção, quando justificável
- roadmap, quando mudar a ordem ou a estrategia

## Como responder a `qual o proximo passo logico?`

A resposta deve seguir esta ordem de decisão:

1. a frente atual já esta fechada ou validada no nível exigido?
2. se não, o próximo passo e o primeiro passo em falta do protocolo acima
3. se sim, abrir a próxima frente por ordem do backlog operativo dominante

Aplicação atual desta regra:

- `IMP-004`, `IMP-005` e `IMP-006` ficaram fechados com validação em piloto real
- a baseline `v2.9.0` fica fechada como release histórica da linha anterior
- o piloto `PG AI Assistant V1 mirror redesign` fica fechado com `READY WITH GUARDRAILS`
- antes de abrir nova frente estrutural, a prioridade passa a ser corrigir qualidade do espelho factual publicado

## Como responder a `avanca com o proximo passo logico`

A execução deve sempre declarar:

- em que repo a ação vai acontecer
- qual o objetivo dessa ação
- que validação fica esperada depois

## Documento de backlog atualmente dominante

Backlog a seguir nas próximas frentes:
- `docs/PG_CURRENT_WORKING_STATE.md`
- `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`

## Regra adicional para backlog histórico

Documentos `V29`, `IMP` ou `REP` anteriores podem continuar úteis como contexto ou histórico de decisões.
Mas deixam de ser backlog dominante quando um documento mais recente:

- fecha formalmente uma linha nova
- regista `READY`, `READY WITH GUARDRAILS` ou `NOT READY`
- redefine explicitamente o bloqueio principal e o próximo passo lógico

Quando isso acontecer, a ronda nova passa a prevalecer sobre a anterior.

## Regra final

Se em algum momento o trabalho voltar a depender de contexto oral para perceber:

- que repo editar
- que repo fazer deploy
- que repo validar
- que branch usar

então este protocolo ou o documento de contexto operativo ficaram incompletos e devem ser atualizados antes da iteração seguinte.
