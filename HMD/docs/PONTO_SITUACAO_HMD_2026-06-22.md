# Ponto de Situação — Projeto Odoo HMD

**Cliente:** HMD Interiors — Edição Produção de Mobiliário, Lda.
**Projeto:** Odoo - HMD
**Data:** 22 de junho de 2026
**Responsável Parâmetro Global:** Bruno Pinheiro

---

Exma. Sra. Nina Hedderich,

Na sequência do nosso contacto telefónico, partilhamos o ponto de situação do projeto Odoo, com o foco nos **trabalhos remanescentes pendentes**. O objetivo deste documento é consolidar, de forma estruturada, tudo o que está em aberto, para que possamos **validá-lo em conjunto** e, a partir daí, formalizar o planeamento e as datas de entrega na nossa plataforma de gestão de projeto, assegurando o controlo de prazos e a qualidade das entregas.

Agradecemos, por isso, que reveja os pontos abaixo e nos confirme: (1) se a lista reflete o que têm em aberto do vosso lado; (2) eventuais ajustes de prioridade; e (3) as decisões assinaladas como pendentes do vosso lado.

---

## 1. Resumo executivo

O projeto encontra-se em fase de evolução e estabilização, com as bases funcionais já em produção (vendas, compras, produção, contabilidade e website). Os trabalhos em aberto distribuem-se por cinco frentes:

- **Estabilização comercial e financeira** — afinações em vendas, contabilidade e tesouraria;
- **Funcionalidades avançadas** — calculadora de transportes, automatismos de CRM/projetos e comunicação por WhatsApp;
- **Website / eCommerce** — finalização e migração do site para Odoo;
- **Preparação do upgrade para Odoo 19** — planeada para a janela do final do ano;
- **Operação e acompanhamento contínuo** — sessões semanais e materiais de apoio.

No global, o projeto está a progredir de forma controlada. Parte destes trabalhos enquadra-se no âmbito protocolado do projeto (Ordem S00465); outros — como a comunicação por WhatsApp e o upgrade para Odoo 19 — constituem frentes adicionais, detalhadas na secção 3. Alguns pontos dependem ainda de **decisões ou inputs do vosso lado** (assinalados na secção 8) e algumas datas iniciais necessitam de ser reagendadas em conjunto, por já terem sido ultrapassadas.

---

## 2. Trabalhos remanescentes pendentes

> A lista seguinte está organizada por área. As datas indicadas são **datas-alvo de referência** do nosso planeamento atual; as marcadas como *(a reagendar)* já foram ultrapassadas e serão acertadas convosco.

### Vendas e orçamentação

Frente de afinação do processo comercial e do cálculo de custo/preço.

- **Calculadora de transporte (cubicagem) ligada ao orçamento** — finalizar a ferramenta que permite calcular o transporte dentro da própria encomenda (em vez de o fazer num ficheiro à parte) e aplicar o custo na linha de venda; depende das tabelas de custo a reunir com o Sérgio. *(data-alvo a reagendar)*;
- **Mudança automática de estado da encomenda quando o pagamento do cliente é confirmado** — automatismo para refletir, no documento de venda, a confirmação do recebimento. *(alvo: agosto/2026)*.

### CRM e gestão de projetos

Ligação entre o funil comercial e a execução em projeto.

- **Criação automática de projeto ao qualificar uma oportunidade no CRM**, com as tarefas-tipo copiadas a partir do modelo. A ligação entre oportunidade e projeto já existe; falta o automatismo de criação e a cópia das tarefas-modelo. *(alvo: setembro/2026)*;
- **Validação do espelhamento "linha de venda → tarefa de projeto"** em novas encomendas, confirmando o comportamento em orçamentos em rascunho e confirmados. *(alvo: junho/2026)*.

### Contabilidade e tesouraria

Consolidação dos processos financeiros.

- **Empréstimos e leasings** — o módulo dedicado já está ativo e há um contrato já registado; falta confirmar a lista completa de empréstimos/leasings históricos e migrar os restantes, descontinuando o registo manual via despesas. *(alvo: junho/2026)*;
- **Cartão de crédito** — o diário já se encontra criado; falta concluir/validar a importação automática de movimentos. *(alvo: junho/2026)*.

### Website e eCommerce

- **Finalização e migração do site para Odoo** — o site em Odoo já existe e tem parte do catálogo publicado; falta concluí-lo e efetuar a transição a partir da solução atual (Shopify). **Ponto urgente** dada a data-limite do Shopify (ver secção 7). *(alvo: imediato)*.

### Comunicação por WhatsApp Business

Frente de comunicação comercial via WhatsApp, integrada com as encomendas.

- **A parte técnica em Odoo já está preparada** (módulos de WhatsApp instalados, com criação de canal por encomenda). O que falta é a **configuração externa junto da Meta** — conta Meta Business, número dedicado e aprovação dos modelos de mensagem — a coordenar com a Mónica. *(alvo: dependente da Meta)*.

### Dados (contactos)

- **Limpeza e reconciliação de contactos PHC vs. Odoo** — deteção e correção de contactos em falta ou duplicados; depende da **extração de dados do PHC** a fornecer pelo vosso lado. *(data-alvo a reagendar)*.

### Preparação do upgrade para Odoo 19

Frente técnica de evolução de versão, planeada para a janela do final do ano.

- **Clonagem do ambiente para testes e execução do upgrade para a versão 19** em ambiente isolado;
- **Adaptação dos módulos personalizados** à versão 19 (com atenção particular aos visualizadores 3D e às personalizações de website);
- **Upgrade em produção e go-live**, com plano de recuperação preparado, na janela proposta de dezembro/janeiro.

### Questões em aberto / suporte

Pontos reportados recentemente, em análise.

- **Erro ao criar fatura de cliente** — em análise;
- **Erros reportados a 22/06** (abertura de projeto e RFQ a partir do artigo) — em análise.

### Operação e acompanhamento

- **Sessões semanais de acompanhamento** (30 min), com agenda enviada pelo vosso lado até à véspera;
- **Vídeos de apoio HMD-specific** (ex.: fluxo de verificação de qualidade no terreno).

---

## 3. Enquadramento no âmbito protocolado

Para apoiar a validação e o planeamento, distinguimos o que se enquadra no âmbito inicialmente protocolado do projeto do que constitui uma frente adicional.

O âmbito protocolado consta da **Ordem S00465 (16/12/2024)** e inclui uma bolsa de **serviços de apoio à implementação Odoo (400 horas)**, abrangendo, entre outras, as seguintes frentes: web B2B, CRM, modelos de venda, folha de cálculo de orçamento, catálogo com variantes, listas de materiais, pedidos de cotação a fornecedor (blanket orders), encomendas a fornecedor, acompanhamento de subcontratação, receção, compras/faturas com Documentos, qualidade, expedição, faturação, contas correntes, custos/FSE/pessoal, pagamentos SEPA, gestão de tesouraria e migração de clientes, fornecedores, produtos e saldos. Inclui ainda o licenciamento Odoo, a faturação certificada, o alojamento e 6 dias de suporte após o arranque.

**A larga maioria dos trabalhos remanescentes da secção 2 enquadra-se neste âmbito protocolado** — designadamente a estabilização comercial e financeira, a calculadora de orçamento, a migração e limpeza de contactos, e os processos de qualidade, expedição, faturação e tesouraria.

### Frentes adicionais ao âmbito protocolado

Os pontos seguintes não constavam do âmbito protocolado inicial e constituem, por isso, frentes adicionais — a planear e orçamentar de forma específica:

- **Comunicação por WhatsApp Business** — integração do WhatsApp com as encomendas (módulos e canais) e respetiva configuração junto da Meta;
- **Upgrade para Odoo 19** — preparação, testes, adaptação das personalizações e go-live em produção, conforme detalhado na secção 2.

Para referência, há ainda capacidades **já implementadas** que também extravasaram o âmbito inicialmente protocolado — designadamente a **visualização de modelos 3D no website** e o **suporte a Intrastat / código HS** na documentação de exportação.

---

## 4. Marcos e calendário proposto

O planeamento atual está organizado em cinco marcos. As datas abaixo servem de base à validação conjunta; o **M1 já foi ultrapassado** e será reposicionado consoante a confirmação das prioridades.

| Marco | Descrição | Data-alvo | Estado |
|---|---|---|---|
| M1 | Sprint imediato | 15/06/2026 | **A reagendar** |
| M2 | Estabilização comercial & QC | 30/06/2026 | Em curso |
| M3 | Funcionalidades avançadas | 30/09/2026 | Planeado |
| M4 | Preparação upgrade Odoo 19 | 31/10/2026 | Planeado |
| M5 | Upgrade produção & fecho de projeto | 15/01/2027 | Planeado |

---

## 5. Estado atual

À data deste relatório, o sistema está em utilização corrente e com volume real de operação — a título de dimensão: cerca de **3 481 produtos** em catálogo (292 publicados no site), **214 encomendas de venda**, **233 oportunidades de CRM** e **132 projetos** geridos no Odoo.

Em concreto:

- as bases do sistema estão em produção e em utilização corrente (vendas, compras, produção, contabilidade e website em uso real);
- a frente de **estabilização comercial e financeira** está ativa: vários pontos já têm a base implementada (empréstimos, cartão de crédito, Intrastat) e estão em fase de conclusão/validação;
- as **funcionalidades avançadas** estão iniciadas: a parte técnica do WhatsApp já está preparada (a aguardar apenas a configuração junto da Meta) e a calculadora de transporte está em finalização;
- a **finalização do website em Odoo** é o ponto mais sensível no curto prazo, pela data-limite do Shopify; o site já tem parte do catálogo publicado;
- o **upgrade para Odoo 19** está enquadrado para o final do ano, dependente da vossa aprovação da janela.

---

## 6. Próximos passos

1. **Validação desta lista** pelo vosso lado (pontos em aberto, prioridades e correções);
2. Com base nessa validação, **formalização do planeamento e das datas** na nossa plataforma de gestão de projeto, para controlo de prazos;
3. Resolução das **decisões pendentes** assinaladas na secção 8, em particular as que têm impacto imediato (website/Shopify e WhatsApp/Meta);
4. Arranque/retoma das **sessões semanais de acompanhamento** como espaço de priorização contínua.

---

## 7. Riscos e pontos de atenção

- **Data-limite do Shopify:** a janela para publicar o site em Odoo é curta. Importa decidir e atuar com brevidade para evitar interrupção da presença online;
- **Aprovação de modelos pela Meta (WhatsApp):** o processo de aprovação pode demorar semanas. Quanto mais cedo arrancar a conta Meta Business e os modelos de mensagem, menor o risco de atraso;
- **Datas iniciais ultrapassadas:** alguns pontos do sprint imediato (M1) já passaram a data-alvo; o replaneamento conjunto é necessário para repor o calendário de forma realista;
- **Upgrade para Odoo 19:** as personalizações (visualizadores 3D e website) exigem adaptação e testes; recomenda-se executar o go-live numa semana de baixa atividade, após fecho de mês.

---

## 8. Decisões e inputs pendentes do vosso lado

| Decisão / input necessário | Impacto se não for decidido | Prazo sugerido |
|---|---|---|
| Publicação do site em Odoo e fim do Shopify | Risco de interrupção da presença online | Imediato |
| Configuração da Meta para WhatsApp (conta Meta Business + número dedicado + aprovação de modelos) | A parte técnica em Odoo já está pronta; isto é o único passo que falta para ativar a comunicação por WhatsApp | Logo que possível (lead time Meta) |
| Extração de dados do PHC para limpeza de contactos | Bloqueia a reconciliação de contactos | A acordar |
| Confirmação da lista de empréstimos/leasings históricos a migrar | Bloqueia o fecho da frente de empréstimos | Junho/2026 |
| Decisão de arquivo fotográfico (OneDrive/O365 vs. alojamento atual) | Define onde fica o arquivo fotográfico e o respetivo custo | 30/06/2026 |
| Go/no-go do upgrade para Odoo 19 e janela (dez/jan) | Define a ordem das melhorias e o calendário do final do ano | 30/06/2026 |

---

## 9. Pontos por validar

Para fechar o enquadramento e o planeamento, há pontos cujo enquadramento no âmbito protocolado (Ordem S00465) importa confirmar em conjunto. Assinalamo-los expressamente como **pontos por validar**:

- **(Por validar) Acompanhamento semanal contínuo** — o âmbito protocolado prevê 6 dias de suporte após o arranque; o acompanhamento semanal de forma continuada excede esse suporte protocolado, pelo que o seu enquadramento (eventual suporte recorrente dedicado) está por validar;
- **(Por validar) Empréstimos/leasings e cartão de crédito** — considerámos estes trabalhos enquadrados na frente de gestão de tesouraria do âmbito protocolado; o enquadramento fica por validar;
- **(Por validar) Automação de criação de projeto ao qualificar oportunidade (CRM)** — considerámos este automatismo enquadrado na frente de CRM do âmbito protocolado; o enquadramento fica por validar.

---

Ficamos a aguardar a vossa validação e ao dispor para qualquer esclarecimento adicional, bem como para agendar uma sessão conjunta de revisão, caso prefiram.

Com os melhores cumprimentos,

**Bruno Pinheiro**
Team Leader — Equipa Odoo
Parâmetro Global
