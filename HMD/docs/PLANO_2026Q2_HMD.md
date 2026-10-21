# Plano de Trabalhos — HMD Interiors

**Período de referência:** reunião 2026-05-20 + estado atual do tenant Odoo 18 Enterprise
**Documento elaborado em:** 2026-05-21
**Autor:** João Barros — Parâmetro Global
**Fontes:** `PG_CONTEXT.md` (sync 2026-05-18), requisitos cliente (PDF), transcrição da reunião 2026-05-20, inventário de módulos custom em repositório, `vendor/odoo_src` v18.0

---

## 1. Resumo executivo

Após reunião de 20/05/2026 com HMD, o projeto está estabilizado nas frentes nucleares (CRM, Vendas, Compras, Inventário, Manufatura, Adiantamentos, eCommerce básico). O cliente apresentou uma lista consolidada em cinco áreas (CRM/Vendas/Contactos; Inventário/Manufatura/Qualidade; Projeto/Tarefas; Marketing/Website; Contabilidade/Tesouraria) e expressou três dores principais:

1. **Modelo de acompanhamento centrado em tickets** está a gerar frustração — pedido para passar a sessões consultivas semanais (Quinta 10h-10h30) e produção de vídeos/documentação HMD-specific.
2. **Falta de fases claras nos projetos** — projetos atuais têm estágios a mais e mal mapeados; é preciso reduzir a 3 fases (Novo / Em Progresso / Concluído) e mover as etapas operacionais (Desenho / Compras / Produção / Montagem) para dentro das tarefas via templates.
3. **Workflow de Controlo de Qualidade pouco acessível** — verificações estão no recebimento mas falta painel, criação espontânea no terreno e visualização por imagens.

Em paralelo, está em cima da mesa a **migração v18 → v19** (regra Odoo: máx. 3 versões antes de cobrar 25% de suporte adicional) e o **acerto de armazenamento OneDrive vs Odoo.sh** discutido com Cláudio.

---

## 2. O que já está implementado (FACTO OBSERVADO)

> Base: 30 módulos custom presentes no repositório + PG_CONTEXT (170 itens curados, 183 tarefas espelhadas, 2 abertas).

### 2.1 CRM, Vendas e Contactos
- `pg_crm_project_opportunities` — ligação CRM ↔ Projeto (base para automatismo de criação de projeto ao qualificar lead).
- `pg_email_cc` — campo CC nos emails (pedido inicial do scope).
- `hmd_sale_price_calculator` — calculadora de preço no orçamento (a "mini calculadora" mencionada na reunião).
- `hmd_sale_product_image_once` — controlo de imagem do produto em venda.
- `pg_multi_discount` — múltiplos descontos em ordem de venda.
- `pg_sale_purchase_link` — ligação venda ↔ compra.

### 2.2 Adiantamentos
- `sale_advance_payment` + `ptplus_sale_advance_payment` — fluxo de Advance Payment funcional (incl. tarefa aberta `FA adiantamento PARA ANALISAR` em revisão).

### 2.3 Compras
- `hmd_purchase_history_all` — histórico agregado de compras.
- `hmd_purchase_image_toggle` — toggle de imagens em RFQ/compras.
- `pg_supplierinfo_purchase` — gestão de supplierinfo no fluxo de compra.
- `hmd_product_rfq_button` — botão direto "criar RFQ" no artigo (mecanismo central para o workflow casing/serralharia discutido na reunião).

### 2.4 Inventário, Produção e Tecidos
- `hmd_mrp_product_button` — atalho MRP a partir do artigo.
- `hmd_product_project_button` + `hmd_product_tag_project_link` — link artigo ↔ projeto/tag.
- `pg_tecidos` — gestão de tecidos.
- `pg_product_multi_attachment` — múltiplos anexos no produto (desenhos técnicos).
- `pg_packing_list` — packing list customizado.

### 2.5 eCommerce e Website
- `pg_3d_viewer`, `pg_3d_ecommerce`, `pg_product_model_viewer` — viewer 3D / model viewer no website.
- `hmd_product_gallery_bridge`, `hmd_product_images_snippet`, `pg_website_attribute_image` — galeria e imagens por atributo.
- `pg_website_hide_unavailable_variant` — esconder variantes indisponíveis.
- `pg_shop_public_override` — override loja pública.
- `pg_web_attach_pdf_view` — pré-visualização PDF.
- `hmd_website_editor_diagnostics` — diagnóstico do editor (utilitário interno).

### 2.6 Tabelas de preço
- `pg_price_table` — tabela de preços com quantidade mínima por produto (item do scope inicial).

### 2.7 Qualidade
- Pontos de qualidade configurados em `Receção` com template tipo "tirar foto" (validado na reunião — funciona para novos recebimentos a partir do momento em que o ponto foi criado).

### 2.8 Adoção e infraestrutura
- Backup 5G instalado no cliente (semana de 13/05/2026).
- Tenant Odoo 18 Enterprise on-premise estável; 560 mensagens, 424 anexos espelhados.
- Decisão: alojamento mantém-se on-premise enquanto performance for aceitável; Odoo.sh entra quando servidor degradar.

---

## 3. O que falta fazer (planeado para os próximos 6 meses)

> Cada item está classificado segundo a ordem consultiva obrigatória (`Standard` → `Módulo standard adicional` → `Studio` → `Custom`).

### 3.1 Projetos e Tarefas — *prioridade ALTA, foco da próxima sprint*

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| P1 | Reduzir fases de projeto a `Novo` / `Em Progresso` / `Concluído` | **Configuração standard** | Reorganizar `project.project.stage`; preservar filtros existentes para projetos internos/formação |
| P2 | Mover estágios atuais (Desenho/Compras/Produção/Montagem/etc.) para **fases da tarefa** dentro de cada projeto | **Configuração standard** + templates | Cada projeto-template tem o seu `project.task.type` |
| P3 | Templates de projeto por tipo: `Encomenda cliente`, `Projeto interno`, `Formação`, `Desenvolvimento` | **Configuração standard** | Já existe template "produtos novos" — reaproveitar |
| P4 | Auto-criação de projeto ao qualificar lead no CRM (com tarefas template) | **Customizado leve** sobre `pg_crm_project_opportunities` | Já temos o link base; falta o hook de qualificação + cópia das tarefas |
| P5 | Espelhar item de venda → tarefa de projeto (1 SOL = 1 task) | **Customizado** (já parcialmente feito — confirmar cobertura nos novos SO) | Verificar comportamento em SO em rascunho vs confirmado |
| P6 | Vista agregada "tudo o que tenho para desenhar/comprar/montar" entre projetos | **Configuração standard** (vista de tarefas agrupada por etapa) | Resolve-se assim que P1+P2 estiverem feitos |
| P7 | Custo/hora por colaborador para análise pré-venda | **Configuração standard** (`hr.employee.hourly_cost`) | Apenas configurar; não envolve timesheet detalhado por tarefa |

### 3.2 CRM, Vendas e Contactos

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| V1 | **Templates de cotação** (caixas de amostra, modelos por linha de produto) | **Configuração standard** (`sale.order.template`) | Não confundir com calculadora |
| V2 | **Calculadora de cotações via Spreadsheet** (transportes, calculo de custo) | **Módulo standard adicional** (`spreadsheet` + `documents_spreadsheet`) | A folha não foi configurada — é o passo que ficou em aberto há vários meses |
| V3 | **WhatsApp Business** integrado | **Módulo standard adicional** (`whatsapp` enterprise) | Requer conta Meta e número dedicado; templates aprovados pela Meta; URGENTE para o cliente |
| V4 | Auto-criação de canal WhatsApp por SO (ver demonstração) | Incluído em V3 — **Standard** | Funciona out-of-the-box uma vez `whatsapp_sale` ativo |
| V5 | **Verificação contactos PHC vs Odoo** (detectar em falta sem duplicar) | **Customizado leve** (script de import com matching por VAT/email) | Pedir extracção PHC antes |
| V6 | Listas de mailing separadas dos contactos comerciais | **Configuração standard** (`mailing.list` + categorias) | Limpar `res.partner.category` |
| V7 | **Novo documento contabilístico anexo à fatura** com HS Code, código Intrastat, país de origem, peso e cubicagem (só quando aplicável a clientes UE/extra-UE) | **Módulo standard adicional** (`account_intrastat` enterprise — fornece HS Code e Intrastat codes em `product.template` e `account.move.line`) **+ Customizado leve** (novo relatório QWeb `pg_export_document` sobre `account.move`, ligado à fatura mas separado) | **NÃO mexer no documento de fatura certificada PT.** Decisão da reunião: criar documento anexo (estilo "Declaração de Mercadorias" / "Export Document"). Reaproveitar peso/cubicagem de `pg_packing_list` e adicionar HS Code/Intrastat via standard. Imprimível sob pedido a partir do botão Imprimir da fatura |
| V8 | Botão "IDU" (impressão direta única) para encomendas e faturas | **Configuração standard** (action shortcut) | Validar se já existe via Estudio |
| V9 | Excel resumo de encomendas | **Configuração standard** (export listview / spreadsheet dashboard) | Avaliar dashboard sale |

### 3.3 Controlo de Qualidade

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| Q1 | **Painel de bordo QC** (QC pendentes, por tipo, por fornecedor) | **Configuração standard** (kanban + filtros guardados) | Standard 18 já suporta |
| Q2 | **Criação espontânea de QC no terreno** (foto + nota) | **Configuração standard** (`quality.check` direto) — completar UX | Hoje obriga a passar pelo `Quality Control Point`; criar action atalho mobile |
| Q3 | Visualização por imagens (gallery view) das verificações QC | **Customizado leve** (vista gallery em `quality.check`) | Pequeno; alta utilidade segundo Mónica |
| Q4 | Painel "encomendas a fornecedor" com QC associadas | **Configuração standard** (vista de purchase + smart button) | Pode integrar-se com painel P6 |

### 3.4 Inventário e Manufatura

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| I1 | Decisão final sobre **artigo "custom genérico"** vs criação por encomenda | **Configuração standard** — manter criação de artigo + BOM em pré-venda | Confirmado em reunião: gera mais trabalho criar genérico depois |
| I2 | Embalagens como artigos consumíveis com custo logístico | **Configuração standard** (`product.type='consu'` + landed cost) | Documentar limitação: consumíveis não entram em algumas vistas de stock |
| I3 | Datas de subcontratação (planeamento vs entrega) | **PONTO POR VALIDAR** — comportamento na v19 melhora; rever após upgrade | Workaround atual aceitável |

### 3.5 Contabilidade, Tesouraria e RH

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| C1 | **Configuração de empréstimos** (importar até 2026) | **Módulo standard adicional** (`account_loans` enterprise) | Não instalado; substitui hack manual atual |
| C2 | **Cash-flow 30/60/90 + previsão recebimentos/pagamentos** | **Módulo standard adicional** (`account_reports` + aging) | Standard enterprise; ativar e ensinar |
| C3 | Controlo de **depósitos 40%** (Advance Payment) — relatório | **Customizado leve** (relatório sobre `account.payment` linked a SO) | Base existe (`ptplus_sale_advance_payment`); só falta reporte |
| C4 | Controlo de margens | **Configuração standard** (sale_margin já standard; ativar dashboard) | Validar dados de custo |
| C5 | **Template recibo de adiantamento** (layout para contabilista) | **Customizado leve** — ajuste QWeb do relatório existente | Cliente confirmou só layout, sem mexer no documento |
| C6 | Fluxo pagamentos **sem fatura** (Seg. Social, IRS, IVA) | **Configuração standard** — criar diário "Custos Pessoal" + fornecedores-entidade | Demonstrado na reunião; falta documentar |
| C7 | **Permissões por diário** | **Configuração standard** (`account.journal.restrict_mode_hash_table` + grupos) | Validar granularidade requerida |
| C8 | Configuração contas **cartão de crédito** | **Configuração standard** (journal tipo bank + statement import) | |
| C9 | **Despesas por utilizador** + extratos mensais cartão | **Módulo standard adicional** (`hr_expense`) + categorias por cartão | Não instalado |
| C10 | Processamento de **recibos de vencimento** com acesso restrito ao próprio | **Decisão**: continuar a fazer no gabinete externo; **lançar via Compra/Fornecedor-funcionário** (fluxo demonstrado) — não ativar `hr_payroll` | Evita-se complexidade de payroll PT |
| C11 | **Alertas pagamento cliente** → mudar estado encomenda automaticamente | **Customizado leve** (server action em `account.payment` → state em `sale.order`) | Nina envia transferência → Sérgio confirma; automatizar transição |
| C12 | Alertas pagamentos sem fatura (impostos) | **Configuração standard** (atividade recorrente / cron) | Simples |

### 3.6 Marketing, Website e Storage

| # | Necessidade | Recomendação | Notas |
|---|---|---|---|
| W1 | **Limpeza das alterações website via código** (blocos com fontes legadas) | **Decisão**: aguardar v19 (refazer com blocos novos) — não investir agora | Mónica pediu correção na base — só vale após upgrade |
| W2 | OneDrive/O365 para arquivo fotográfico pesado | **Fora-Odoo** — configuração cliente | Cláudio a fazer acerto contratual com proposta original |
| W3 | Marketing Automation + Email Marketing | **Módulo standard adicional** já disponível | Avaliar após CRM/projetos estarem estáveis |

### 3.7 Operação consultiva (acompanhamento)

- Reuniões semanais 30min — **Quinta 10h-10h30** (a partir de 2026-05-28).
- Cliente envia agenda até **Quarta 12h**.
- Substituir trabalho-por-tickets por **vídeos curtos / documentação HMD-specific** alojados no chatter de cada tarefa-template.
- Próximos vídeos prioritários: criação de projeto-template, fluxo QC espontâneo, lançamento de pagamentos sem fatura.

---

## 4. Migração para Odoo 19 — análise

### 4.1 FACTOS observados

- HMD está em **Odoo 18.0 Enterprise on-premise** (`vendor/odoo_src/community/odoo/release.py` confirma 18.0).
- **Odoo 19** já lançada; **Odoo 20** anunciada.
- Política Odoo: máximo de 3 versões simultaneamente suportadas; a partir da 4ª versão, suporte custa **+25%** do valor de licença.
- v19 traz melhorias relevantes para HMD: **IA de base**, Quality Control mais evoluído, Project com melhor template engine, integrações website e modos de pagamento mais maduros.

### 4.2 INFERÊNCIAS

- HMD tem ~30 módulos custom + alterações Studio + edições de website via código → migração não é trivial.
- Várias necessidades acima (Q1/Q2/Q3, W1, parte de I3) **beneficiam diretamente da v19** — fazer agora pode duplicar trabalho.
- Janela razoável para o upgrade: **Q4 2026 / Q1 2027**, depois de estabilizar P1-P7, V1-V4 e C1-C6.

### 4.3 PONTOS POR VALIDAR

- Compatibilidade de cada módulo `pg_*`/`hmd_*` com a API 19 (especialmente os de website e 3D viewer).
- Esforço de re-tradução das alterações website feitas via código para blocos standard 19.
- Janela de paragem aceite pelo cliente (sugestão: agendar para semana de baixa atividade após fecho de mês).

### 4.4 Estratégia de upgrade recomendada

1. **Junho-Setembro 2026** — implementar items prioritários (Projetos P1-P7, WhatsApp V3, Spreadsheet V2, QC Q1-Q2, Tesouraria C1-C6). Foco em **configuração standard** para minimizar dívida técnica que vai migrar.
2. **Outubro 2026** — clone do tenant para ambiente de testes; correr `odoo-bin --upgrade-path` para v19; identificar falhas em módulos custom.
3. **Novembro 2026** — refactor dos módulos custom afetados; refazer alterações de website com blocos v19.
4. **Dezembro 2026 / Janeiro 2027** — janela de upgrade em produção, com rollback preparado (snapshot completo). Testes em staging com utilizadores HMD durante 1-2 semanas antes do go-live.

### 4.5 Decisão pendente do cliente

| Decisão | Impacto | Prazo |
|---|---|---|
| Aprovar janela de upgrade Dez/Jan 2026-27 | Define ordem das melhorias entre Jun-Set | 2026-06-30 |
| Aprovar instalação de `whatsapp` (custos Meta) | Bloqueia V3-V4 | 2026-06-15 |
| Aprovar acerto contratual O365 vs alojamento original | Define onde fica o arquivo fotográfico | 2026-06-30 |

---

## 5. Próximos passos imediatos (até 2026-06-15)

1. **Reformular fases de projeto** (P1+P2+P3) e migrar projetos correntes — **João Barros**.
2. **Configurar Spreadsheet Calculator de transportes** (V2) — **João Barros** com input do Sérgio sobre tabelas dos paranistários.
3. **Documentar fluxo de pagamentos sem fatura** (C6) em vídeo — **Parâmetro Global**.
4. **Reformular template QWeb do recibo de adiantamento** (C5) — **João Barros**.
5. **Levantar pré-requisitos WhatsApp** (V3): conta Meta, número, templates a aprovar — **Parâmetro Global + Mónica**.
6. **Cleanup contactos PHC vs Odoo** (V5) — pedir extracção PHC ao cliente; preparar script de matching.
7. Confirmar com Cláudio o acerto contratual de alojamento/O365.

---

## 6. Riscos e pontos de atenção

- **R1 — Acumulação de dívida técnica antes da v19:** cada novo módulo custom feito agora terá de ser migrado. Mitigação: priorizar standard/Studio sobre custom até estabilizar v18.
- **R2 — Frustração da equipa com modelo de tickets:** reuniões semanais + vídeos resolvem o sintoma; é preciso disciplina interna em executar o que ficou combinado em sessão.
- **R3 — WhatsApp depende de aprovação Meta:** templates podem demorar semanas a ser aprovados — começar o processo já.
- **R4 — Upgrade v19 sem ambiente de teste pré-validado:** risco de regressão em fluxos críticos. Mitigação: clonar tenant em Outubro 2026 e testar com utilizadores reais.

---

## 7. Referências consultadas

- `PG_CONTEXT.md` (sync 2026-05-18) — versão Odoo, edição, ambiente, restrições contratuais.
- Repositório `joao-barros-pg/HMD` — inventário de 30 módulos custom em `hmd_*`, `pg_*`, `ptplus_*`, `sale_advance_payment`.
- `vendor/odoo_src/community/odoo/release.py` — confirmação versão 18.0.
- `vendor/odoo_src/enterprise/` — disponibilidade standard de `whatsapp`, `quality_control`, `account_loans`, `account_reports`, `hr_expense`, `marketing_automation_whatsapp`, `spreadsheet_dashboard_*`, `documents`.
- Requisitos cliente (PDF "Reunião 20/05/2026") — lista consolidada de necessidades.
- Transcrição reunião 20/05/2026 — contexto qualitativo, decisões in-meeting, dores expressas.
- Documentação oficial Odoo 18 (a citar nas próximas iterações para módulos específicos).

---

*Documento elaborado segundo `PG_PRE_RESPONSE_CHECKLIST` e template `TPL_PONTO_SITUACAO.md`. Pronto para revisão e partilha com o cliente após validação interna.*
