# PG_PROJECT_LEARNINGS

Este ficheiro guarda aprendizagens consultivas reutilizáveis observadas em projetos Odoo.
Serve para acelerar triagem, reconhecer sinais recorrentes e evitar erros repetidos.
Não substitui a validação do projeto atual contra `PG_CONTEXT.md`, código do projeto, `vendor/odoo_src` e documentação oficial da versão ativa.

## LEARNING 001 - Studio parecia suficiente, mas fragilizou o processo
Contexto:
- pedido de campos, regras e automações cresceu iterativamente sobre o mesmo fluxo

Sinal inicial:
- a solução parecia "leve" e rapida porque cada alteração isolada era pequena

O que aconteceu:
- a soma das pequenas regras criou dependência de Studio difícil de manter e explicar

Aprendizagem:
- Studio e bom para extensoes moderadas e bem delimitadas, não para substituir desenho funcional consistente

Heuristica reutilizável:
- se o requisito atravessa vários modelos, vários estados e várias exceções, reavaliar cedo se Studio continua adequado

## LEARNING 002 - Módulo standard adicional evitou custom desnecessario
Contexto:
- pedido parecia exigir desenvolvimento para approvals e governance operacional

Sinal inicial:
- a equipa assumiu que o módulo principal não cobria o caso

O que aconteceu:
- um módulo standard adicional do Odoo cobria a maior parte do requisito com adaptação de processo aceitável

Aprendizagem:
- limitar a análise aos módulos já instalados aumenta risco de customização prematura

Heuristica reutilizável:
- quando o gap parece estrutural, procurar primeiro módulos standard adicionais no `vendor/odoo_src` da versão ativa

## LEARNING 003 - O pedido era preferência, não necessidade real
Contexto:
- cliente pediu alteração funcional com forte componente de interface e conforto operativo

Sinal inicial:
- a justificação vinha em termos de preferência e não de risco, custo ou compliance

O que aconteceu:
- a necessidade real foi resolvida com configuração e treino, sem alterar o comportamento base

Aprendizagem:
- nem toda a fricção operacional e gap funcional do sistema

Heuristica reutilizável:
- antes de avaliar custom, perguntar sempre que decisão de negocio falha sem a alteração pedida

## LEARNING 004 - Parecia documental, mas era operacional
Contexto:
- pedido foi descrito como necessidade de anexos, documentos e assinatura

Sinal inicial:
- a conversa focava ficheiros e templates, mas os erros aconteciam no handoff entre equipas

O que aconteceu:
- o problema principal estava no fluxo operacional, não na camada documental

Aprendizagem:
- sintomas documentais podem esconder falha de processo, aprovação ou ownership

Heuristica reutilizável:
- se ha muitos anexos e exceções, validar primeiro o processo que gera esses documentos

## LEARNING 005 - Workflow parecia complexo, mas o problema era de processo
Contexto:
- equipa pediu múltiplos estados, aprovações e validações adicionais

Sinal inicial:
- cada interveniente queria um checkpoint próprio no sistema

O que aconteceu:
- a complexidade vinha da indefinição de responsabilidade e não de limite real do Odoo

Aprendizagem:
- desenhar workflow custom sobre processo mal definido cristaliza ineficiência

Heuristica reutilizável:
- se o pedido de estados cresce depressa, parar e clarificar ownership, exceções e critério de decisão antes de modelar o fluxo

## LEARNING 006 - Reporting falhou por dados, não por falta de dashboard
Contexto:
- pedido para dashboards executivos mais ricos e relatórios adicionais

Sinal inicial:
- havia pressão para ver melhor, mas pouca confianca nos números de origem

O que aconteceu:
- o gargalo principal estava em classificação, completude e disciplina de registo de dados

Aprendizagem:
- dashboard novo não corrige semantica de dados inconsistente

Heuristica reutilizável:
- antes de recomendar reporting adicional, validar definições de KPI, campos obrigatórios e qualidade dos dados base

## LEARNING 007 - O filtro não estava avariado; a migração 18 → 19 não recalculou o campo
Contexto:
- utilizador reportou que o filtro "Employees" na escolha de participantes do Calendar devolvia meia dúzia de nomes em vez de todos os colegas (observado no Odoo da Parâmetro Global, 2026-08-10: 4 nomes de 13 empregados activos, e 2 desses 4 já arquivados)

Sinal inicial:
- o sintoma parecia de vista, permissões ou multi-empresa, e o filtro é standard (`hr`, domínio `[('employee', '=', True)]`)

O que aconteceu:
- em Odoo 19 o campo `res.partner.employee` deixou de ser a checkbox manual do `base` e passou a `compute='_compute_employee', store=True, readonly=False` no módulo `hr`, dependente de `employee_ids` (ser `work_contact_id` de um `hr.employee` activo)
- a migração de 18 para 19 não recalculou a coluna dos registos existentes: só as fichas criadas ou alteradas depois do upgrade dispararam o cálculo, e arquivar um empregado também não dispara recálculo (o `work_contact_id` não muda), deixando flags a `True` a mais
- a correcção foi de dados, com reconciliação de contagens no fim; não houve código, Studio nem módulo novo

Aprendizagem:
- quando uma versão nova converte um campo manual em calculado e armazenado, os dados antigos não se corrigem sozinhos; o sintoma chega ao utilizador como "o filtro está avariado" e leva a equipa a procurar na camada errada

Heuristica reutilizável:
- perante um filtro standard que devolve resultados incompletos, comparar primeiro a contagem do critério com a contagem da fonte que o devia alimentar (aqui: `res.partner` com `employee = True` vs `hr.employee` com `work_contact_id` preenchido); se divergirem, é drift de dados e não configuração
- confirmar no `vendor/odoo_src` se o campo mudou de natureza entre a versão de origem e a de destino da migração — a definição do campo na versão nova explica o sintoma melhor do que a vista
- tratar como defeito latente de frota: qualquer base que tenha migrado de 18 para 19 com `hr` instalado tem o mesmo desvio até ser recalculada
