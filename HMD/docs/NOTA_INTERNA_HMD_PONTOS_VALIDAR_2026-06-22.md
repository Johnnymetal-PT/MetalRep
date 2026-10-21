# Nota Interna — Pontos por Validar | Projeto Odoo HMD

**Uso:** interno Parâmetro Global (não enviar ao cliente)
**Data:** 22 de junho de 2026
**Autor:** Bruno Pinheiro
**Contexto:** preparação do ponto de situação a enviar à HMD e do enquadramento face ao âmbito protocolado (Ordem S00465, 16/12/2024).

---

## 1. Ponto por validar — interno

- **(Por validar) Balanço de horas de serviço** — a Ordem S00465 protocola **400 horas** de serviços de apoio (50 dias). O Odoo de gestão de projeto (`parametroglobal.odoo.com`, projeto id 93) regista `allocated_hours = 338`. Importa **reconciliar internamente** qual é a referência correta antes de formalizar o planeamento e antes de comunicar qualquer balanço de esforço ao cliente. Não foi exposto qualquer número de horas no documento do cliente.

---

## 2. Pontos por validar — enquadramento de âmbito (também no documento do cliente)

Estes pontos estão assinalados como "por validar" no ponto de situação enviado ao cliente, para validação conjunta:

- **(Por validar) Acompanhamento semanal contínuo** — o âmbito protocolado prevê apenas **6 dias de suporte após venda**. O acompanhamento semanal continuado excede esse suporte protocolado → forte candidato a **frente adicional / contrato de suporte recorrente**. É, comercialmente, o ponto mais relevante a fechar.
- **(Por validar) Empréstimos/leasings e cartão de crédito** — enquadrados, por agora, na frente de gestão de tesouraria do âmbito protocolado. Classificação discutível; confirmar.
- **(Por validar) Automação de criação de projeto ao qualificar oportunidade (CRM)** — enquadrada, por agora, na frente de CRM do âmbito protocolado. Automatismo custom específico; confirmar.

---

## 3. Frentes já classificadas como adicionais (no documento do cliente)

- **Comunicação por WhatsApp Business** — fora do âmbito protocolado.
- **Upgrade para Odoo 19** — fora do âmbito protocolado.
- Nota: capacidades já entregues (**modelos 3D no website**, **Intrastat / código HS**) também extravasaram o âmbito protocolado.

---

## 4. Base factual

- Âmbito protocolado: Ordem S00465 (16/12/2024) — bolsa de 400h de serviços + licenciamento, faturação certificada, alojamento e 6 dias de suporte após venda.
- Estado verificado em produção (leitura, 22/06/2026): `intranet.hmdfurniture.com`, DB `HMD`, Odoo 18.0+e — WhatsApp instalado, diário de cartão de crédito criado, 1 empréstimo em `account.loan`, site com 292 produtos publicados.
