# Implementação Odoo — Virgin Details, Lda — Estimativa de Esforço

**Versão:** 1.0  
**Data:** 20/05/2026  
**Válido até:** 20/06/2026  
**Preparado por:** Pedro Coelho — Parâmetro Global, Consultoria Informática S.A.  
**Para aprovação de:** Daniela Martins — Virgin Details, Lda  

---

## Contexto

A Virgin Details, Lda é uma empresa sediada na Maia, Porto, que atua como representante comercial exclusiva de marcas europeias (Starplast, HASA, Jeremias, Sunerg) no mercado português B2B.  
A empresa gere hoje a operação com PHC GO (faturação), Excel (stock) e Pipedrive (CRM, 10+ anos de dados), sem integração entre sistemas.  
O objetivo é substituir estes sistemas por uma plataforma Odoo unificada — cobrindo CRM, vendas, compras, inventário, faturação portuguesa e gestão de projetos.

---

## Âmbito Coberto

Esta estimativa cobre os trabalhos de implementação Odoo para a **Fase 1 — Core Operacional** e apresenta valores indicativos para a **Fase 2 — Expansão**.

A implementação baseia-se no protótipo funcional já desenvolvido em [waterdetails.odoo.com](https://waterdetails.odoo.com), na reunião de apresentação de 20/05/2026 e na Análise de Requisitos — Virgin Details, Lda (v1.1, 2026-05-18).

**Plataforma:** Odoo Enterprise saas~19.3 · Odoo SH (cloud) · Localização PT (l10n_pt)  
**Utilizadores:** 5  
**Empresas:** 1 na Fase 1 (Virgin Details, Lda); expansão multiempresa na Fase 2

---

## Detalhe de Esforço

### Fase 1 — Core Operacional

| # | Área | Descrição do Trabalho | Esforço (dias) | Observações |
|---|---|---|---|---|
| 1 | Gestão de Projeto | Kick-off interno e com cliente; reuniões quinzenais de acompanhamento; reporting de progresso; encerramento de fase e handover | 4 | |
| 2 | Configuração Inicial | Setup da empresa Virgin Details, Lda; criação e configuração de 5 utilizadores; grupos de acesso (comercial, logística, financeiro, gestão); configuração de e-mail e templates de comunicação | 2 | |
| 3 | Contactos e Regras de Preço | Tipificação de contactos (clientes, fornecedores, serviços externos); etiquetas de classificação; regras de preço por perfil de cliente; configuração de múltiplos endereços (faturação, entrega) | 1 | |
| 4 | CRM | Configuração do pipeline comercial; definição de fases e probabilidades; templates de e-mail por fase; atividades automáticas; dashboards e relatórios CRM | 2 | |
| 5 | Vendas | Templates de orçamento; listas de preço (margens 40–60% por marca); políticas de desconto; configuração de condições de entrega; gestão de moradas de entrega variáveis (dropshipping HASA/Jeremias); configuração base do portal B2B | 3 | |
| 6 | Compras | Configuração de fornecedores europeus (Starplast IT, HASA ES, Jeremias ES, Sunerg IT); listas de preço de custo; lead times por fornecedor; regras de abastecimento MTO (Make-to-Order); fluxo de encomenda automática | 2 | |
| 7 | Inventário e Logística | Configuração do armazém (Maia, PT); rotas MTO + Comprar; fluxo de receção (Starplast/Sunerg via Itália); fluxo de dropshipping direto (HASA/Jeremias via Espanha para cliente final); configuração e impressão de guias de transporte | 2 | |
| 8 | Financeiro — l10n_pt | Plano de contas português; grupos de IVA (23%/13%/6%/Isento); configuração SAF-T; plugin de certificação de faturas AT; condições de pagamento (30 dias, 60 dias, antecipado); configuração de adiantamentos; setup de reconciliação bancária | 3 | Plugin certificação AT licenciado separadamente |
| 9 | Migração de Dados | Importação do catálogo de produtos (23 templates, 31+ SKUs, variantes) via template Parâmetro; importação de clientes e fornecedores de PHC GO / Excel / Moloni; passagem de saldos em aberto (faturas por regularizar) | 3 | Cliente fornece dados em Excel limpo antes do início |
| 10 | Migração Pipedrive | Exportação, mapeamento e importação de contactos e histórico CRM (10+ anos) do Pipedrive para o módulo CRM do Odoo | 2 | **[POR VALIDAR]** — esforço depende do volume, qualidade e estrutura dos dados exportados |
| 11 | Testes e Validação | Testes do fluxo completo end-to-end (lead → orçamento → encomenda cliente → encomenda fornecedor → receção/dropshipping → entrega → faturação → pagamento); validação com o cliente; correções | 2 | |
| 12 | Formação e Arranque | Formação de utilizadores (5 pessoas, por perfis: comercial, logística, financeiro); suporte ao go-live; documentação de utilização | 3 | |
| | | **Total Fase 1** | **29** | Inclui 2 dias Pipedrive [POR VALIDAR] |

---

### Fase 2 — Expansão *(valores indicativos; a confirmar após arranque da Fase 1)*

| # | Área | Descrição do Trabalho | Esforço (dias) | Observações |
|---|---|---|---|---|
| 13 | Manufatura (BoM) | Criação de Listas de Materiais (depósitos com acessórios, kits de instalação); configuração de Ordens de Fabrico; controlo de componentes consumidos; custo de produto final | 4 | **[POR VALIDAR]** — âmbito depende de levantamento dos kits/montagens mais frequentes (PV-06) |
| 14 | Multiempresa — Starplast SRLE | Configuração da segunda empresa do grupo; utilizadores e acessos partilhados; transações intercompany (compra Virgin Details → venda Starplast SRLE); relatórios financeiros consolidados | 3 | **[POR VALIDAR]** — âmbito depende de confirmação da estrutura legal e operacional da segunda empresa (PV-04) |
| 15 | Contabilidade Analítica | Definição e ativação de contas analíticas por projeto, por marca (4 marcas) e por cliente; reporting de margem por dimensão analítica | 2 | |
| 16 | Módulos adicionais | Sign (aprovação eletrónica de orçamentos), Barcode (armazém com leitores), Documents (gestão de catálogos e fichas técnicas), Helpdesk (suporte pós-venda e garantias) — a definir por prioridade | [POR VALIDAR] | A orçamentar separadamente após levantamento de prioridades |
| | | **Total Fase 2 (base)** | **9** | Não inclui módulos adicionais (linha 16) |

---

## Valorização

| | Fase 1 — Core | Fase 2 — Expansão (base) |
|---|---|---|
| **Esforço (dias)** | 29 dias | 9 dias |
| **Taxa diária** | €\_\_\_\_\_ / dia | €\_\_\_\_\_ / dia |
| **Total implementação** | €\_\_\_\_\_ | €\_\_\_\_\_ |

> A taxa diária aplicável é a constante no contrato de serviços assinado entre a Parâmetro Global e a Virgin Details, Lda.  
> O licenciamento Odoo SH e as licenças de utilizadores são apresentados em proposta separada por Stefano Biglieri.

**Modalidade de pagamento:** A implementação pode ser faturada por fases concluídas e aceites pelo cliente, de acordo com acordo entre as partes.

---

## Pressupostos

1. O cliente disponibiliza os dados mestres (catálogo de produtos, clientes, fornecedores, saldos em aberto) em ficheiro Excel limpo segundo o template Parâmetro, antes do início da fase de migração.
2. Existe um interlocutor do cliente (Daniela Martins ou delegado) disponível para validações e testes, pelo menos 4 horas por semana durante a implementação.
3. O plugin de certificação de faturas AT é licenciado separadamente e está disponível antes do arranque do módulo financeiro.
4. A Virgin Details utiliza Odoo SH cloud — sem infraestrutura on-premise a gerir pela Parâmetro.
5. O âmbito da Fase 1 não inclui desenvolvimento custom — toda a implementação é configuração e parametrização standard Odoo.
6. A migração Pipedrive (linha 10) pressupõe que os dados exportados do Pipedrive têm qualidade suficiente para importação direta, após mapeamento. Se o volume ou a qualidade exigirem limpeza extensiva, o esforço será revisto.
7. A Fase 2 só é iniciada após validação e aceite da Fase 1 pelo cliente.
8. O número de utilizadores da Fase 1 é 5, com perfis a definir no kick-off.

---

## Exclusões

- Licenciamento Odoo (SH subscription + licenças de utilizadores) — proposta separada Stefano Biglieri
- Plugin de certificação de faturas AT — custo de licença não incluído
- Desenvolvimento de custom code (sem âmbito de custom na Fase 1)
- Integrações com sistemas externos não listados no âmbito (ex: banca online para OFX automático — a confirmar PV-07)
- Formação de utilizadores adicionais para além dos 5 previstos
- Suporte pós go-live — coberto por contrato de suporte separado
- Migração de histórico de faturação anterior ao go-live (apenas saldos em aberto)
- Módulos adicionais da Fase 2 (Sign, Barcode, Documents, Helpdesk) — a orçamentar após levantamento
- Configuração da segunda empresa do grupo (Starplast SRLE) na Fase 1

---

## Pontos Por Validar

| # | Ponto | Impacto nesta estimativa |
|---|---|---|
| PV-04 | Segunda empresa do grupo (Starplast SRLE): nome legal, atividade, relação operacional com Virgin Details | Define âmbito linha 14 — Multiempresa |
| PV-06 | Quais os kits e montagens mais frequentes da Virgin Details? | Define âmbito linha 13 — BoM/Manufatura |
| PV-07 | Banco(s) da Virgin Details e formato de extratos (OFX/SEPA) | Pode afetar esforço linha 8 — reconciliação bancária |
| PV-10 (Pipedrive) | Volume total de contactos e deals no Pipedrive; qualidade e estrutura dos dados exportados | Define esforço real linha 10 — Migração Pipedrive |

---

## Condições

- Esta estimativa tem uma margem de variação de **±15%** para trabalhos de análise, configuração e testes.
- A linha de Migração Pipedrive (linha 10) está marcada como **[POR VALIDAR]** — a estimativa de 2 dias é baseada num volume padrão. Após análise do export do Pipedrive, o esforço pode ser revisto antes do início dessa fase.
- Trabalhos fora do âmbito desta estimativa serão orçamentados separadamente antes de serem iniciados.
- Validade desta estimativa: **20/06/2026**. Após esta data, os valores podem ser revistos.
- A estimativa da Fase 2 é indicativa e será confirmada em proposta separada após go-live da Fase 1.

---

## Cronograma Indicativo

| Fase | Início previsto | Duração estimada |
|---|---|---|
| Fase 1 — Core Operacional | 2–3 semanas após assinatura | ~3 meses |
| Fase 2 — Expansão | ~1 mês após go-live Fase 1 | ~2 meses |

> O cronograma definitivo será apresentado no kick-off, após confirmação da disponibilidade do cliente e do consultor.

---

## Aprovação

| | Parâmetro Global | Cliente |
|---|---|---|
| **Nome** | Pedro Coelho | Daniela Martins |
| **Cargo** | Consultor / Project Manager | Gerente — Virgin Details, Lda |
| **Data** | | |
| **Assinatura** | | |

---

*Parâmetro Global — Consultoria Informática S.A.*  
*it.odoo@parametro.global*  
*Versão 1.0 — 20/05/2026*
