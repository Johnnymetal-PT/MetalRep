# Análise de Requisitos — Virgin Details, Lda
**Projeto:** Waterdetails — Implementação Odoo  
**Cliente:** Daniela Martins / Virgin Details, Lda  
**Consultor:** Pedro Coelho — Parâmetro Global  
**Data:** 2026-05-18  
**Versão:** 1.1 (atualizada com contexto completo da cliente)

---

## 1. Contexto e Modelo de Negócio

### 1.1 Quem é a Virgin Details, Lda

- Empresa portuguesa sediada na **Maia, Porto**
- Pertence a um **grupo de duas empresas** (multiempresa a considerar na implementação)
- Setor: **depósitos e bombas de água** — produtos de tratamento de águas, cisternas, estações elevatórias, ventilação e energia solar
- Modelo: **representante comercial** exclusiva de marcas europeias no mercado português B2B
- Mercado-alvo: distribuidores, construtores, instaladores, materiais de construção

### 1.2 Marcas representadas

| Marca | País | Produto | Logística |
|---|---|---|---|
| Starplast S.R.L. | Itália | Tanques polietileno, fossas sépticas, cisternas, estações elevatórias, tratamento biológico | Receção em Portugal (armazém) |
| HASA - Hidráulica Alsina S.A. | Espanha | Bombas hidráulicas série Shark | Dropshipping direto de Espanha para o cliente final |
| Jeremias Chimney Systems S.L. | Espanha | Sistemas VMC, ventilação mecânica controlada, tubagens EkkoFlex | Dropshipping direto de Espanha para o cliente final |
| Sunerg Solar S.R.L. | Itália | Painéis fotovoltaicos, inversores híbridos SolaX, baterias Triple Power | Receção em Portugal (armazém) |

### 1.3 Fluxo comercial completo

```
Lead/Contacto
    ↓
Orçamento ao cliente
    ↓
Encomenda confirmada
    ↓
Verificação de stock disponível
    ↓
Compra internacional ao fornecedor
    ↓
Receção (PT) ou Dropshipping direto (ES)
    ↓
Transformação / montagem (quando aplicável — via BoM)
    ↓
Entrega ao cliente
    ↓
Guia de transporte
    ↓
Faturação
    ↓
Pagamento (antecipado ou a 30/60 dias)
```

### 1.4 Logística internacional

**Dropshipping (Espanha → Cliente final):**
- HASA e Jeremias entregam diretamente ao cliente português
- A Virgin Details não recebe fisicamente estes produtos
- O Odoo gere o fluxo com uma encomenda de compra ligada à encomenda de venda, sem movimentação de stock próprio

**Receção em Portugal (Itália → Armazém Virgin Details):**
- Starplast e Sunerg enviam para armazém da Virgin Details na Maia
- Produtos são recebidos, possivelmente transformados (BoM) e expedidos ao cliente
- Requer gestão de stock próprio e receções documentadas

### 1.5 Transformação de artigos (Bill of Materials)

A Virgin Details realiza **transformação de produtos** antes da entrega ao cliente final:
- Montagem de depósitos com acessórios (tampas, filtros, módulos)
- Criação de kits ou conjuntos de produtos finais a partir de componentes
- Gestão de custos de componentes e produto acabado

O módulo **Fabrico (BoM)** do Odoo suporta este processo através de:
- Definição de listas de materiais (Bill of Materials)
- Ordens de fabrico para transformação/montagem
- Controlo de componentes consumidos e custo do produto final

---

## 2. Situação Atual — Problemas Identificados

| Sistema atual | Uso | Problema |
|---|---|---|
| **PHC GO** | Faturação | Sistema isolado, sem ligação ao stock, CRM ou compras |
| **Excel** | Controlo de stock | Manual, sem rastreabilidade, erros frequentes, não partilhável em tempo real |
| **Ferramenta separada** | Gestão de tarefas | Desligada do ERP, sem visibilidade de custos por projeto |
| — | CRM / Pipeline | Não existe — negócios geridos por email/telefone |
| — | Compras internacionais | Sem registo sistemático de encomendas a fornecedores, prazos e custos |

**Consequências práticas:**
- Informação descentralizada — cada área trabalha em silos
- Falta de visão integrada da operação (stock ↔ vendas ↔ compras ↔ faturação)
- Dificuldade em controlar despesas por projeto e rentabilidade
- Sem reporting consolidado para as duas empresas do grupo
- Limitação à escabilidade — o crescimento da empresa exige uma plataforma unificada

---

## 3. Objetivos com o Odoo

| Objetivo | Descrição |
|---|---|
| **Centralização total** | Uma única plataforma para CRM, vendas, compras, stock, faturação e projetos |
| **Solução all-in-one** | Substituição do PHC GO + Excel + ferramenta de tarefas por um único sistema |
| **Controlo operacional** | Visibilidade em tempo real de stock, encomendas pendentes e margem por negócio |
| **Reporting centralizado** | Dashboards integrados; contabilidade analítica por projeto, por marca, por cliente |
| **Multiempresa** | Gestão das duas empresas do grupo com separação operacional e consolidação de números |
| **Preparação para crescimento** | Base escalável — códigos de barras, e-commerce, helpdesk, assinatura digital |
| **Mobilidade** | Acesso móvel para a equipa comercial em campo |

---

## 4. Documentos Analisados

| Documento | Tipo | Valor | Data |
|---|---|---|---|
| Catálogo Starplast.pdf | Catálogo fornecedor | 108 páginas, 100+ produtos | — |
| HASA2025-47.pdf | Encomenda fornecedor | €4.588 (60% desc.) | — |
| JEREMIAS-6.pdf | Encomenda fornecedor | €4.761,15 (40% desc.) | — |
| SUN2026-330.pdf | Encomenda fornecedor | €9.558,82 | — |
| Orçamento-15-Districthive.pdf | Orçamento cliente | €35.396,45 (IVA+20% desc.) | 2026-05-14 |
| Fatura Proforma-1-Nextgreen.pdf | Proforma | €428,43 (60% desc.) | 2026-04-09 |
| Fatura-69-Alberto Félix.pdf | Fatura | €850,62 (60% desc.) | 2026-05-15 |
| Encomenda-79-Mendes e Irmãos.pdf | Encomenda cliente | €2.557,72 | 2026-05-14 |

---

## 5. Módulos Odoo — Âmbito da Implementação

### 5.1 Módulos instalados no protótipo (Fase 1 — base)

| Módulo | Função |
|---|---|
| **CRM** | Pipeline comercial, oportunidades, leads |
| **Sales** | Orçamentos, encomendas de cliente, políticas de desconto |
| **Purchase** | Encomendas a fornecedores europeus, preços de custo |
| **Inventory** | Catálogo de produtos, stock, receções, expedições |
| **Accounting + l10n_pt** | Faturação portuguesa, IVA 23%, SAF-T, plano de contas PT |
| **Project** | Gestão de obras/projetos, tarefas, custos |
| **Contacts** | Base de dados de clientes e fornecedores |

### 5.2 Módulos a avaliar para implementação completa

| Módulo | Justificação |
|---|---|
| **Manufacturing (BoM)** | Transformação de depósitos/bombas, montagem de kits, controlo de componentes |
| **Multi-Company** | Gestão das duas empresas do grupo com separação contabilística |
| **Analytic Accounting** | Contabilidade analítica por projeto, por marca, por cliente |
| **Sign** | Aprovação eletrónica de orçamentos pelo cliente |
| **Barcode** | Preparação para gestão de armazém com leitores de código de barras |
| **Helpdesk** | Suporte pós-venda, garantias, acompanhamento de reclamações |
| **Documents** | Gestão de catálogos, fichas técnicas, documentação de projeto |

---

## 6. Dados Configurados no Protótipo

### 6.1 Fornecedores (4)
- Starplast S.R.L. (Itália) — produtos Tratamento de Águas
- HASA - Hidráulica Alsina S.A. (Espanha) — Bombas Hidráulicas
- Jeremias Chimney Systems S.L. (Espanha) — Ventilação Controlada
- Sunerg Solar S.R.L. (Itália) — Energia Solar

### 6.2 Clientes (7)
- Districthive Lda (Funchal, Madeira)
- Nextgreen Unipessoal Lda (Santarém)
- Alberto Félix de Almeida Unipessoal Lda (Argoncilhe)
- Mendes e Irmãos S.A. (Loures)
- Bombas do Liz Lda (Leiria)
- Torneiras OFA Lda (Lisboa)
- MACOP - Materiais de Construção SA (Lisboa)

### 6.3 Produtos (23 templates ativos)

| Categoria | Templates | Tipo |
|---|---|---|
| Tratamento de Águas — Tratamento Biológico | QuickOne 32 CF, BIOSMART 500L, Depur Star 1000L | Simples |
| Tratamento de Águas — Tanques Superficiais | CLY3000-CT145, CLY3000-P180, CLY5000-P180 | Simples |
| Tratamento de Águas — Cisternas Subterrâneas | SEICC-AG | **Com variantes** (1050/2500/5000L) |
| Tratamento de Águas — Fossas Sépticas | SET | **Com variantes** (1500/2500L) |
| Tratamento de Águas — Pluvial | IAP3000, BGR500 | Simples |
| Tratamento de Águas — Elevatórias | MINISOL400, BBS600, MXS1200 | Simples |
| Tratamento de Águas — Filtros | NS100, ACESSO-T32, ACESSO-MGF | Simples |
| Bombas Hidráulicas | Shark HASA | **Com variantes** (75/100/150W × Mono/Trifásica) |
| Ventilação Controlada | VMC-R100, EKKOFLEX-KIT, SIFAO-COND | Simples |
| Energia Solar | SUNERG-425W, SOLAX-X1-3700, TRIPLE-PWR-5800 | Simples |

**Configurações por produto:**
- Preço de venda e preço de custo (desconto de 40–60% conforme marca)
- Fornecedor configurado na tab Compras (product.supplierinfo) com prazo de entrega
- Rotas: MTO (Reabastecer mediante Encomenda) + Comprar

### 6.4 Pipeline CRM (7 oportunidades)
| Fase | Oportunidades |
|---|---|
| Novo Lead / Contacto | Cisternas Alentejo (Mendes); Tratamento Águas Lisboa (Districthive) |
| Qualificado / Em Estudo | Solar+Armazenamento Centro Logístico (MACOP); VMC Jeremias (Torneiras OFA) |
| Proposta Enviada | Sistema Tratamento Funchal (Districthive); Solar 5.1kWp (MACOP) |
| Em Negociação | Bombas Shark Leiria (Bombas do Liz) |

### 6.5 Documentos Comerciais
- 7 Sale Orders (S00001–S00009, com gaps de cancelados)
- 4 Purchase Orders (P00002 Sunerg, P00003 Jeremias, P00004 Starplast, P00007 HASA)
- Opportunity_id configurado em 5 SOs (ligação CRM ↔ Vendas)

---

## 7. Faturação e Contabilidade — Requisitos

| Requisito | Detalhe | Estado no protótipo |
|---|---|---|
| Localização portuguesa (l10n_pt) | IVA 23%, plano de contas PT | ✓ Instalado |
| Conformidade AT | SAF-T, comunicação faturas | ✓ Módulo instalado |
| Pagamentos antecipados | Adiantamentos de cliente | A configurar no levantamento |
| Condições de pagamento | 30 dias / 60 dias / imediato | A configurar (standard Odoo) |
| Reconciliação bancária | Importação de extratos, matching automático | Disponível no módulo Accounting |
| Contabilidade analítica | Por projeto / por marca / por cliente | A ativar no levantamento |
| Multiempresa — faturação | Faturação separada por empresa do grupo | Requer configuração multi-company |

---

## 8. Gestão de Projetos — Requisitos

O módulo **Project** do Odoo suporta a gestão de obras e projetos de instalação:

| Requisito | Capacidade Odoo |
|---|---|
| Obras / projetos | Projetos com tarefas, fases e responsáveis |
| Custos por projeto | Registo de despesas e tempos imputados a projeto |
| Despesas | Módulo Expenses integrado com Project e Analítica |
| Rentabilidade | Margem por projeto = receita vendas - custos diretos |
| Contabilidade analítica | Cada projeto tem conta analítica automática |

**PONTO POR VALIDAR (PV-09):** A Virgin Details gere obras de instalação internamente ou apenas vende e a instalação é feita pelo cliente/instalador?

---

## 9. Inventário — Requisitos

| Requisito | Detalhe |
|---|---|
| Substituição do Excel | Centralização de todo o stock no Odoo |
| Armazém Virgin Details | Receção de produtos Starplast (IT) e Sunerg (IT) |
| Dropshipping (ES) | HASA e Jeremias entregam diretamente — sem stock físico na Virgin Details |
| Preparação para crescimento | Estrutura base para expansão futura com códigos de barras |
| Valorizações de stock | FIFO ou preço médio — a definir no levantamento |

**PONTO POR VALIDAR (PV-05):** Confirmar quais os produtos que a Virgin Details recebe fisicamente vs. dropshipping direto ao cliente.

---

## 10. Multiempresa — Requisitos

A Virgin Details pertence a um grupo de duas empresas. O Odoo suporta multiempresa com:
- **Separação operacional:** cada empresa tem os seus documentos, stock e contabilidade
- **Consolidação de números:** relatórios financeiros consolidados ao nível do grupo
- **Reporting consolidado:** dashboards e análises cross-empresa
- **Utilizadores partilhados:** os mesmos utilizadores podem operar nas duas empresas

**PONTO POR VALIDAR:** Identificar a segunda empresa do grupo — nome, atividade, relação com a Virgin Details (partilha de produtos? clientes? fornecedores?).

---

## 11. Acesso Móvel

O Odoo Enterprise inclui acesso móvel completo via browser e app:

| Funcionalidade | Disponível |
|---|---|
| Consultar stock | ✓ |
| Consultar clientes e histórico | ✓ |
| Criar e enviar orçamentos | ✓ |
| Acompanhar entregas | ✓ |
| Registo de despesas | ✓ (módulo Expenses) |
| Trabalho remoto — sem VPN | ✓ (SaaS cloud) |

---

## 12. Pontos Por Validar

| # | Ponto | Impacto | Prioridade |
|---|---|---|---|
| PV-01 | Modelo de faturação: Virgin Details fatura em nome próprio (revenda com margem) ou em comissão? | Alto — define ciclo financeiro e módulo de faturação | Alta |
| PV-02 | A Virgin Details emite faturas ou a fatura é da Starplast/HASA diretamente? | Alto — define entidade fiscal nas transações | Alta |
| PV-03 | Número de utilizadores Odoo e funções (comercial, logística, contabilidade, gestão) | Médio — afeta licenciamento | Alta |
| PV-04 | Segunda empresa do grupo: nome, atividade, relação com Virgin Details | Alto — define âmbito multiempresa | Alta |
| PV-05 | Quais produtos têm stock físico (Itália) vs. dropshipping direto (Espanha)? | Alto — define configuração de armazém e rotas | Alta |
| PV-06 | Transformação de artigos: quais os kits/montagens mais frequentes? | Médio-Alto — define âmbito BoM | Alta |
| PV-07 | Integração bancária: qual o banco? Extratos OFX/SEPA? | Médio — define reconciliação automática | Média |
| PV-08 | Condições de pagamento habituais (30/60 dias)? Utilizam adiantamentos? | Médio — define configuração de tesouraria | Média |
| PV-09 | A Virgin Details gere obras de instalação diretamente? | Médio — define âmbito Project | Média |
| PV-10 | Grupos de utilizadores e controlo de acesso por empresa | Médio | Média |

---

## 13. Recomendação Preliminar de Âmbito

### Fase 1 — Core operacional (Configuração Standard)

```
CRM → Sales → Purchase → Inventory → Accounting (l10n_pt) → Project
```

**Fluxo suportado:**
```
Lead CRM → Orçamento → Encomenda Cliente → Verificação Stock →
Encomenda Fornecedor → Receção/Dropshipping → Entrega → Guia → Fatura → Pagamento
```

### Fase 2 — Expansão (após levantamento formal)

| Módulo | Justificação |
|---|---|
| Manufacturing (BoM) | Transformação de artigos e montagem de kits |
| Multi-Company | Segunda empresa do grupo |
| Analytic Accounting | Contabilidade analítica por projeto/marca |
| Sign | Aprovação eletrónica de orçamentos |
| Barcode | Armazém com leitores de código de barras |
| Helpdesk | Suporte pós-venda |

### Classificação da Recomendação

> **Configuração Standard** — Os módulos core cobrem o processo comercial completo da Virgin Details sem necessidade de desenvolvimento custom na Fase 1. A transformação de artigos (BoM) e a multiempresa são módulos standard adicionais a ativar na Fase 2.

---

## 14. Referências Consultadas

- `PG_CONTEXT.md` (sync: 2026-05-15)
- `.pg/PG_SCOPE_SYNC.json`
- Documentos anexos (8 ficheiros PDF analisados)
- Odoo saas~19.3 Enterprise — instância waterdetails.odoo.com
- `.pg_framework/templates/AGENTS_SHARED.md`
- `.pg_framework/docs/PG_PRE_RESPONSE_CHECKLIST.md`
- Informação direta do cliente (Daniela Martins) via Pedro Coelho
