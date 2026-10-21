# Protótipo Odoo — Virgin Details, Lda
**Apresentação para:** Daniela Martins  
**Preparado por:** Pedro Coelho — Parâmetro Global  
**Data:** 2026-05-18  
**Instância:** [waterdetails.odoo.com](https://waterdetails.odoo.com)

---

## Sobre a Virgin Details

A Virgin Details, Lda é uma empresa sediada na Maia, Porto, especializada em depósitos e bombas de água. Pertence a um grupo de duas empresas e atua como representante comercial de marcas europeias — Starplast (Itália), HASA (Espanha), Jeremias (Espanha) e Sunerg (Itália) — no mercado português B2B, servindo distribuidores, construtores e instaladores.

---

## O problema que o Odoo resolve

| Hoje | Com o Odoo |
|---|---|
| Faturação no PHC GO — isolado do resto | Uma única plataforma para toda a operação |
| Stock controlado em Excel — manual e propenso a erros | Stock em tempo real, com receções e expedições registadas |
| Ferramenta separada para tarefas e projetos | Projetos integrados com custos, despesas e rentabilidade |
| Sem CRM — negócios geridos por email e telefone | Pipeline comercial com histórico completo por cliente |
| Sem visão integrada — cada área trabalha em silos | Informação centralizada, acessível a toda a equipa |
| Dois sistemas para o grupo de empresas | Multiempresa — separação operacional e consolidação de números |
| Sem acesso móvel para a equipa comercial | Aplicação móvel — orçamentos e stock em qualquer lugar |

---

## O que construímos para si

Com base nos documentos da sua empresa — catálogos, orçamentos, encomendas e faturas — configurámos um protótipo funcional do Odoo adaptado ao modelo de negócio da Virgin Details.

---

## Objetivos alcançados no protótipo

| Objetivo | Estado |
|---|---|
| Empresa Virgin Details, Lda configurada | ✓ |
| Fornecedores europeus configurados (4 marcas) | ✓ |
| Clientes portugueses configurados (7) | ✓ |
| Catálogo de produtos com variantes (23 templates, 31+ SKUs) | ✓ |
| Fornecedor configurado por produto (tab Compras) | ✓ |
| Rotas MTO + Comprar em todos os produtos | ✓ |
| Pipeline CRM com oportunidades reais | ✓ |
| Orçamentos e encomendas de cliente | ✓ |
| Encomendas a fornecedores (4 marcas) | ✓ |
| Módulo de faturação portuguesa (l10n_pt) instalado | ✓ |
| Módulo de gestão de projetos instalado | ✓ |

---

## O que pode explorar na instância

### 1. CRM — Pipeline Comercial

**Acesso:** Menu CRM → Pipeline

O pipeline mostra as oportunidades comerciais organizadas por fase:

| Fase | Oportunidades configuradas |
|---|---|
| Novo Lead / Contacto | Cisternas Alentejo (Mendes); Tratamento Águas Lisboa (Districthive) |
| Qualificado / Em Estudo | Solar+Armazenamento (MACOP); VMC Jeremias (Torneiras OFA) |
| Proposta Enviada | Sistema Tratamento Funchal (Districthive); Solar 5.1kWp (MACOP) |
| Em Negociação | Bombas Shark Leiria (Bombas do Liz) |

Cada oportunidade está ligada ao respetivo orçamento de venda — pode navegar diretamente do CRM para o documento.

---

### 2. Vendas — Orçamentos e Encomendas

**Acesso:** Menu Vendas → Pedidos

| Nº | Cliente | Produtos | Valor est. | Estado |
|---|---|---|---|---|
| S00001 | Districthive Lda | QuickOne 32 + 10× Minisol + 10× NS100 | ~€35.000 | Orçamento |
| S00003 | Mendes e Irmãos S.A. | Tanques + Cisternas | ~€3.800 | Confirmado |
| S00004 | Alberto Félix Unipessoal | CLY5000-P180 Panettone 5000L | ~€1.050 | Confirmado |
| S00005 | MACOP - Mat. Construção SA | 12× Solar 425W + Inversor + 3× Bat. | ~€15.670 | Orçamento |
| S00007 | Torneiras OFA Lda | 3× VMC + 3× EkkoFlex + Sifões | ~€5.000 | Orçamento |
| S00008 | Nextgreen Unipessoal Lda | Cisterna Subterrânea 1050L | €527 | Confirmado |
| S00009 | Bombas do Liz Lda | Bombas Shark (75/100/150W Mono) | ~€3.380 | Orçamento |

**Destaque:** Nos produtos com variantes (ex: Bombas Shark), a seleção da potência e do tipo de alimentação elétrica é feita diretamente no orçamento — sem necessidade de produtos separados.

---

### 3. Compras — Encomendas a Fornecedores

**Acesso:** Menu Compras → Pedidos

| Ref. | Fornecedor | País | Tipo Logística | Produtos | Estado |
|---|---|---|---|---|---|
| P00004 | Starplast S.R.L. | Itália | Receção em PT | Tanques CLY + Cisternas SEICC | Rascunho |
| P00007 | HASA Hidráulica Alsina | Espanha | Dropshipping → cliente final | Bombas Shark (variantes) | Rascunho |
| P00003 | Jeremias Chimney Systems | Espanha | Dropshipping → cliente final | VMC + EkkoFlex + Sifões | Rascunho |
| P00002 | Sunerg Solar S.R.L. | Itália | Receção em PT | 12× Solar + Inversor + 3× Baterias | Rascunho |

**Nota sobre logística:** Os fornecedores espanhóis (HASA, Jeremias) entregam diretamente ao cliente final — dropshipping. Os fornecedores italianos (Starplast, Sunerg) enviam para receção em Portugal.

---

### 4. Catálogo de Produtos

**Acesso:** Menu Inventário → Produtos

23 templates ativos em 8 categorias, com 31+ SKUs quando incluídas as variantes:

| Categoria | Produtos | Marca | Variantes |
|---|---|---|---|
| Fossas Sépticas | SET 1500L, SET 2500L | Starplast | Sim — Capacidade |
| Tratamento Biológico | QuickOne 32 CF, BIOSMART 500L, Depur Star 1000L | Starplast / ClearFox | Não |
| Tanques Superficiais | CLY3000-CT145, CLY3000-P180, CLY5000-P180 | Starplast | Não |
| Cisternas Subterrâneas | SEICC-AG 1050/2500/5000L | Starplast | Sim — Capacidade |
| Recuperação Pluvial | IAP3000, BGR500 | Starplast | Não |
| Estações Elevatórias | Minisol 400L, BBS 600L, MXS 1200L | Starplast | Não |
| Filtros e Acessórios | NS100, Tampa T32, Módulo Filtro | Starplast | Não |
| Bombas Hidráulicas | Shark HASA — 6 variantes | HASA | Sim — Potência × Alimentação |
| Ventilação Controlada | VMC-R100, EkkoFlex Kit, Sifão Condensados | Jeremias | Não |
| Energia Solar | Painel 425W, SolaX X1-3.7kW, Triple Power 5.8kWh | Sunerg | Não |

**Cada produto tem configurado:**
- Preço de venda e preço de custo com margens reais
- Fornecedor na tab Compras com prazo de entrega
- Rotas: MTO (encomenda ao fornecedor automática) + Comprar

---

### 5. Contactos — Fornecedores e Clientes

**Acesso:** Menu Contactos

**Fornecedores europeus:**
- Starplast S.R.L. (Casoria, Itália)
- HASA Hidráulica Alsina S.A. (Barcelona, Espanha)
- Jeremias Chimney Systems S.L. (Bizkaia, Espanha)
- Sunerg Solar S.R.L. (Itália)

**Clientes portugueses:**
- Districthive Lda (Funchal) · Nextgreen Unipessoal Lda (Santarém) · Alberto Félix Unipessoal Lda (Argoncilhe) · Mendes e Irmãos S.A. (Loures) · Bombas do Liz Lda (Leiria) · Torneiras OFA Lda (Lisboa) · MACOP SA (Lisboa)

---

## Solução proposta — Visão completa

### Módulos core — Fase 1

```
CRM → Sales → Purchase → Inventory → Accounting (l10n_pt) → Project
```

**Fluxo operacional completo:**

```
Lead CRM
  → Orçamento ao cliente
  → Encomenda confirmada
  → Verificação de stock
  → Encomenda ao fornecedor (automática com MTO)
  → Receção (Itália) ou Dropshipping direto (Espanha)
  → Transformação / montagem (BoM — Fase 2)
  → Entrega + Guia de transporte
  → Faturação (AT-compliant)
  → Pagamento (30/60 dias ou antecipado)
```

### Módulos adicionais — Fase 2

| Módulo | Valor para a Virgin Details |
|---|---|
| **Manufacturing (BoM)** | Transformação de depósitos e bombas, montagem de kits, custo de produto final |
| **Multi-Company** | Segunda empresa do grupo — separação operacional + consolidação |
| **Analytic Accounting** | Rentabilidade por projeto, por marca, por cliente |
| **Sign** | O cliente aprova o orçamento eletronicamente por link |
| **Barcode** | Armazém com leitores — preparação para crescimento |
| **Helpdesk** | Suporte pós-venda e acompanhamento de garantias |

### Acesso móvel

O Odoo Enterprise inclui acesso completo via browser e app móvel. A equipa comercial pode:
- Consultar stock e disponibilidade em tempo real
- Criar e enviar orçamentos diretamente do telemóvel
- Consultar o historial completo de cada cliente
- Acompanhar o estado de entregas
- Trabalhar remotamente sem VPN (SaaS cloud)

---

## Próximos passos sugeridos

1. **Reunião de levantamento de requisitos** — validar modelo de faturação, utilizadores, processos reais, segunda empresa do grupo, transformação de artigos
2. **Definição de âmbito Fase 1** — confirmar módulos, profundidade de configuração, plano de migração de dados PHC GO e Excel
3. **Proposta comercial** — orçamento de implementação por módulo e por fase
4. **Kick-off** — arranque da implementação

---

## Notas sobre o protótipo

> Este protótipo foi criado exclusivamente para fins de demonstração. Os dados carregados são dados de demo baseados nos documentos fornecidos. Os contactos utilizam endereços de email de demo (nunca os emails reais dos contactos). O protótipo não substitui a implementação real.

---

*Parâmetro Global — Consultoria Informática S.A.*  
*it.odoo@parametro.global*
