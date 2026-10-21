# PG_FIT_GAP_FRAMING_PROMPT

> **Odoo Studio está proibido desde 2026-09-11.** Não é um passo da ordem de decisão nem uma categoria de recomendação. O que não se resolve por standard resolve-se por desenvolvimento versionado. O Studio **já aplicado** num cliente continua a ser lido, documentado e migrado — a proibição é de criar. Ver `AGENTS_SHARED.md`, secção «O Odoo Studio não é um passo desta ordem».


Quero que operes em modo de **fit-gap framing consultivo** para este projeto.

Usa como input o que já saiu do discovery e, quando existir, o `PG_CONTEXT.md`.
O objetivo deste modo não e decidir já a solução final.
O objetivo e **mapear rapidamente o encaixe da necessidade no Odoo antes da decisão consultiva**, distinguindo o que parece coberto, o que ainda e gap e o que continua por validar.

---

## 1. Fontes obrigatórias

Antes de fechar este framing, consulta obrigatoriamente:

1. `PG_CONTEXT.md`
2. código do projeto
3. `vendor/odoo_src`
4. documentação oficial da versão ativa

Se houver conflito entre memória geral, discovery resumido e evidência do projeto, prevalece sempre a evidência.

---

## 2. Regra de disciplina neste modo

Neste modo:

- não decides ainda a solução final
- não classificas ainda a recomendação como standard, módulo adicional ou custom
- não assumes que uma área Odoo potencialmente impactada já e uma solução validada

Separa sempre explicitamente:

- `FACTO OBSERVADO`
- `INFERENCIA`
- `PONTO POR VALIDAR`

---

## 3. O que tens de mapear

Mapeia explicitamente:

- necessidade ou objetivo
- fit standard observado no projeto
- fit standard adicional potencial no Odoo
- gaps reais observados
- pontos por validar
- risco de decidir cedo demais
- próximo passo recomendado

---

## 4. Como interpretar áreas impactadas

Se no discovery tiverem surgido áreas Odoo potencialmente impactadas, usa-as apenas como orientação de framing.
Não trates "área impactada" como equivalente a "solução encontrada".
O objetivo aqui e perceber o encaixe provável e a natureza do gap, não fechar a implementação.

---

## 5. Formato mínimo esperado na resposta

Responde com esta estrutura:

1. **Necessidade / objetivo**
2. **FACTOS OBSERVADOS**
3. **INFERENCIAS**
4. **PONTOS POR VALIDAR**
5. **Áreas Odoo potencialmente impactadas**
6. **Mapa de fit e gaps**
   - fit standard observado no projeto
   - fit standard adicional potencial no Odoo
      - gaps reais observados
7. **Risco de decidir cedo demais**
8. **Próximo passo recomendado**
9. **Fecho obrigatório**

---

## 6. Fecho obrigatório

No fim do framing, escolhe apenas um:

- `FIT MAIORITARIAMENTE STANDARD`
- `FIT STANDARD COM VALIDACAO ADICIONAL`
- `GAP RELEVANTE AINDA POR CONFIRMAR`
- `NAO HA BASE SUFICIENTE PARA DECISAO`

Se o fecho não permitir ainda decisão consultiva, explica claramente o que falta validar antes de passar para recomendação.
