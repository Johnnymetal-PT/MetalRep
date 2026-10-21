# PG_PRE_RESPONSE_CHECKLIST

> **Odoo Studio está proibido desde 2026-09-11.** Não é um passo da ordem de decisão nem uma categoria de recomendação. O que não se resolve por standard resolve-se por desenvolvimento versionado. O Studio **já aplicado** num cliente continua a ser lido, documentado e migrado — a proibição é de criar. Ver `AGENTS_SHARED.md`, secção «O Odoo Studio não é um passo desta ordem».


Este ficheiro funciona como checklist final antes de respostas consultivas relevantes.
Não substitui `PG_CONTEXT.md`, `templates/AGENTS.md`, `.pg_framework/templates/AGENTS_SHARED.md` nem `docs/PG_DECISION_ENGINE_PROMPT.md`.
Serve apenas como camada de verificação antes da resposta final.

## Checklist antes da resposta final

### 1. Contexto validado
- confirmei o objetivo funcional, processo atual, problema real e impacto no negócio?
- confirmei ou marquei como `PONTO POR VALIDAR` a versão, edição, ambiente e restrições contratuais?

### 2. Evidência técnica consultada
- consultei `PG_CONTEXT.md`?
- consultei código do projeto relevante?
- consultei `vendor/odoo_src` da versão ativa?
- consultei documentação oficial da mesma versão, quando necessário?

### 3. Ordem consultiva respeitada
- avaliei primeiro standard já existente no projeto?
- avaliei módulo standard adicional antes de custom?
- verifiquei se existe Studio **já aplicado** que explique o comportamento atual? (criar em Studio está proibido)

### 4. Factos, inferências e pontos por validar
- distingui claramente `FACTO OBSERVADO`, `INFERENCIA` e `PONTO POR VALIDAR`?
- evitei apresentar inferência como facto?

### 5. Descoberta de módulos standard adicionais
- procurei também no `vendor/odoo_src` módulos standard potencialmente relevantes, incluindo módulos novos do Odoo?
- se recomendei módulo standard adicional, expliquei cobertura, implicações de adoção e gaps remanescentes?

### 6. Coerência com o contexto do projeto
- a recomendação respeita `PG_CONTEXT.md` e o estado real do projeto?
- a recomendação respeita as restrições contratuais identificadas?

### 7. Justificação da recomendação final
- expliquei porque a opção recomendada é a mais adequada?
- se a conclusão for custom, justifiquei porque standard existente e módulo standard adicional não chegam?
- se a conclusão for custom, explicitei risco, manutenção e impacto de upgrade?

### 8. Redação em português europeu
- a resposta e os documentos gerados usam acentuação e cedilhas corretas (ver `.pg_framework/templates/AGENTS_SHARED.md`, secção `Regras de redação em português europeu`)?
- corrigi a acentuação de conteúdo reaproveitado que estava em ASCII, em vez de a perpetuar?
- validei que não restaram palavras sem acento por inércia de redação em ASCII (excepto chaves técnicas, paths, identificadores e código)?

## Regra final
Se a evidência não for suficiente, não fechar a decisão.
Nessa situação, apresentar apenas `RECOMENDACAO PRELIMINAR` e indicar o que falta validar.
