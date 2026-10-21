# Guião de Apresentação do Protótipo — Virgin Details, Lda
**Para uso interno do consultor durante a reunião**  
**Consultor:** Pedro Coelho — Parâmetro Global  
**Cliente:** Daniela Martins — Virgin Details, Lda (Maia, Porto)  
**Instância:** [waterdetails.odoo.com](https://waterdetails.odoo.com)  
**Data prevista:** A definir  
**Duração estimada:** 90 minutos  

> **Nota:** Não existe template dedicado para guião de apresentação no framework PG. Este documento foi produzido adaptando o tom e estrutura de `TPL_PROPOSTA_TECNICA.md`.

---

## Preparação antes da reunião

- [ ] Entrar na instância com antecedência e confirmar que tudo carrega
- [ ] Ter `PROPOSTA_PROTOTIPO_CLIENTE.md` e `ANALISE_REQUISITOS.md` abertos para referência
- [ ] Preparar ecrã partilhado ou projetor com resolução ≥ 1280px
- [ ] Fechar notificações e abas desnecessárias
- [ ] Abrir os seguintes URLs em tabs separados, por ordem de uso:
  1. [waterdetails.odoo.com/odoo/crm](https://waterdetails.odoo.com/odoo/crm) — arranque da demo
  2. [waterdetails.odoo.com/odoo/inventory/products](https://waterdetails.odoo.com/odoo/inventory/products)
  3. [waterdetails.odoo.com/odoo/sales](https://waterdetails.odoo.com/odoo/sales)
  4. [waterdetails.odoo.com/odoo/purchase](https://waterdetails.odoo.com/odoo/purchase)

---

## Estrutura da reunião

| Bloco | Tema | Duração |
|---|---|---|
| 1 | Abertura — problemas atuais e o que o Odoo resolve | 10 min |
| 2 | Centralização — uma plataforma, toda a operação | 5 min |
| 3 | Vendas — do orçamento à encomenda confirmada | 15 min |
| 4 | Compras internacionais — Espanha e Itália | 10 min |
| 5 | Transformação de artigos — Bill of Materials | 7 min |
| 6 | Stock e inventário — fim do Excel | 7 min |
| 7 | Projetos — obras, custos e rentabilidade | 7 min |
| 8 | Faturação e contabilidade portuguesa | 7 min |
| 9 | Reporting e visão de gestão | 5 min |
| 10 | Mobilidade — a equipa comercial em campo | 3 min |
| 11 | Multiempresa e crescimento futuro | 5 min |
| 12 | Próximos passos e levantamento de questões | 10 min |

---

## Bloco 1 — Abertura: problemas atuais e o que o Odoo resolve (10 min)

### O que dizer

> "Daniela, antes de mostrar o protótipo, quero garantir que partimos do mesmo ponto. Percebemos que hoje a Virgin Details trabalha com o PHC GO para faturação, Excel para controlar stock, e uma ferramenta separada para tarefas. Cada área funciona no seu silo — e isso dificulta ter uma visão integrada do negócio."

> "O objetivo desta reunião é mostrar-lhe como seria ter uma única plataforma que liga tudo: o CRM, os orçamentos, as compras a Itália e Espanha, o stock, os projetos, a faturação, e o acesso em mobilidade. Tudo no mesmo sistema."

> "O que vai ver hoje em [waterdetails.odoo.com](https://waterdetails.odoo.com) foi construído com os vossos dados reais — os catálogos, as encomendas, os orçamentos que nos enviaram."

### Perguntas de abertura — validar contexto

- "Hoje, quando um comercial está fora e precisa de saber se tem stock disponível para responder a um cliente — como é que faz?"
- "Quando fecha um negócio, quantos sistemas diferentes tem de atualizar manualmente?"
- "Quando precisa de saber a rentabilidade de uma obra ou projeto — consegue calcular facilmente?"

> *(Ouvir as respostas — confirmam o problema e criam empatia para o que se vai mostrar a seguir.)*

---

## Bloco 2 — Centralização: uma plataforma, toda a operação (5 min)

**Ecrã:** [Dashboard principal do Odoo](https://waterdetails.odoo.com/odoo)

### O que mostrar

Mostrar o menu principal do Odoo com os módulos instalados:
- CRM · Vendas · Compras · Inventário · Contabilidade · Projetos

### O que dizer

> "Este é o ecrã principal. Cada módulo que vê aqui é uma área da vossa operação — e estão todos ligados entre si. Um orçamento criado em Vendas gera automaticamente uma necessidade de compra. Uma compra confirmada atualiza o stock. O stock informa o CRM. A entrega gera a fatura."

> "Em vez de atualizar manualmente o PHC, depois o Excel, depois a outra ferramenta — faz uma vez no Odoo e o sistema propaga a informação para onde ela precisa de ir."

> "E isto funciona em duas empresas ao mesmo tempo — a Virgin Details e a outra empresa do grupo. Cada uma com os seus números separados, mas com visibilidade consolidada para a gestão."

---

## Bloco 3 — Vendas: do orçamento à encomenda confirmada (15 min)

**Acesso:** Menu → CRM → Pipeline → (depois) Menu → Vendas → Pedidos

### 3a. Mostrar o pipeline CRM

**Abrir:** [waterdetails.odoo.com/odoo/crm](https://waterdetails.odoo.com/odoo/crm)

1. **Vista Kanban** — mostrar as 5 fases e as 7 oportunidades
   - Apontar: Novo Lead → Qualificado → Proposta Enviada → Em Negociação → Ganho
2. **Abrir "Bombas Hidráulicas Shark — Leiria"** (Bombas do Liz, fase Em Negociação)
   - Mostrar: cliente, valor estimado, responsável, histórico
   - Clicar "Orçamentos" → ver S00009 associado
3. **Abrir "Sistema Tratamento Águas — Funchal"** (Districthive, fase Proposta Enviada)
   - Mostrar ligação ao orçamento S00001 (~€35k)

### Talking point CRM

> "Hoje gerem o pipeline por email e telefone — não têm visibilidade de quantos negócios estão em cada fase, qual é o valor total em jogo, ou quais são os negócios que estão parados há demasiado tempo. Com o CRM do Odoo, toda a equipa vê o mesmo pipeline em tempo real."

### 3b. Mostrar um orçamento complexo

**Abrir:** Menu → Vendas → Pedidos → S00001 (Districthive)

1. Mostrar as linhas do orçamento: QuickOne 32 + 10× Minisol + 10× NS100 (~€35k)
2. Mostrar o cliente (Districthive, Funchal), condições e total com IVA
3. Mostrar o campo **Oportunidade** — ligado ao lead CRM
4. *"Este orçamento foi gerado a partir do documento real que nos enviaram."*

### 3c. Mostrar variantes de produto ao vivo

**Abrir:** Menu → Vendas → Pedidos → S00009 (Bombas do Liz)

1. Mostrar as linhas: Shark 75W Mono (€420), 100W Mono (€580), 150W Mono (€750)
2. *"Em vez de ter 6 produtos separados para as bombas Shark, tem um único produto com variantes. Quando cria um orçamento, seleciona a potência e o tipo de alimentação elétrica — o sistema calcula o preço certo automaticamente."*

### 3d. Criar um orçamento ao vivo (opcional)

- Menu → Vendas → Novo
- Selecionar cliente → Adicionar produto → Shark HASA
- *O selector de variante aparece: Potência + Alimentação*
- Mostrar que o preço preenche automaticamente
- Fechar sem guardar

### Talking points Vendas

- "O IVA de 23% é calculado automaticamente — não precisa de o adicionar manualmente."
- "Pode enviar o orçamento por email diretamente do Odoo, com o logo e os dados da Virgin Details."
- "Quando o cliente aprova, com um clique transforma o orçamento em encomenda confirmada. O sistema trata do resto."

### Perguntas de qualificação

- "Quando envia um orçamento, costuma dar um desconto global ou por linha? Tem preços diferentes por cliente?"
- "O cliente aprova normalmente por email ou assina o documento? Pensa em ter aprovação eletrónica?"

---

## Bloco 4 — Compras internacionais: Espanha e Itália (10 min)

**Acesso:** Menu → Compras → Pedidos

### O que mostrar

1. **Listar as 4 encomendas a fornecedores**
   - P00004 — Starplast (Itália) · P00007 — HASA (Espanha) · P00003 — Jeremias (Espanha) · P00002 — Sunerg (Itália)

2. **Abrir P00007 — HASA** (dropshipping Espanha)
   - Mostrar as linhas: Shark 75W Mono, 100W Mono, 150W Mono com preços de custo
   - Mostrar fornecedor: HASA - Hidráulica Alsina S.A. (Barcelona)
   - *"Esta encomenda vai diretamente de Espanha para o vosso cliente em Leiria — sem passar pelo armazém. É um dropshipping direto."*

3. **Abrir P00004 — Starplast** (receção em Portugal)
   - Mostrar produtos e prazos de entrega
   - Mostrar o botão **Receção** (sem clicar)
   - *"Esta encomenda vem de Itália para o vosso armazém na Maia. Quando chegar, registam aqui a receção — o stock atualiza automaticamente."*

4. **Mostrar o produto QuickOne 32 — tab Compras**
   - Menu → Inventário → Produtos → QUICKONE32-CF → tab Compras
   - Mostrar: Starplast como fornecedor, preço de custo (€7.200), prazo 21 dias
   - *"Cada produto tem o seu fornecedor configurado, com o preço de custo e o prazo de entrega que negociaram."*

### Talking points Compras

- "Com a rota MTO ativa, quando confirmam uma encomenda de cliente, o Odoo pode gerar automaticamente a proposta de encomenda ao fornecedor — sem ter de ir criar manualmente."
- "Têm fornecedores em Espanha que fazem dropshipping, e fornecedores em Itália que enviam para o vosso armazém. O Odoo gere os dois fluxos de forma diferente — e mantém tudo ligado à encomenda do cliente."
- "O sistema calcula a margem em tempo real: sabe o preço de compra a cada fornecedor e o preço de venda ao cliente."

### Perguntas de qualificação

- "Quando recebem mercadoria de Itália, fazem alguma inspeção ou conferência? Têm casos de devoluções a fornecedores?"
- "Os fornecedores espanhóis confirmam sempre o dropshipping por email? Há algum portal ou sistema deles que usem?"

---

## Bloco 5 — Transformação de artigos: Bill of Materials (7 min)

**Acesso:** (Mostrar no menu — módulo Fabrico — mesmo que não esteja totalmente configurado no protótipo)*

> *Nota para o consultor: O módulo Manufacturing (BoM) está instalado na instância mas não foi configurado com BoMs específicos no protótipo. Neste bloco, explicar o conceito e o valor, sem entrar em fluxo navegável detalhado.*

### O que dizer

> "Um dos processos que identificámos como importante para a Virgin Details é a transformação de produtos. Por exemplo, recebem um depósito da Starplast, montam uma tampa T32, um filtro de odores e um módulo de filtragem — e entregam ao cliente um produto completo."

> "No Odoo, isso chama-se Bill of Materials — uma lista de materiais. Define os componentes que entram e o produto final que sai. Quando processam a transformação, o sistema desconta os componentes do stock e adiciona o produto acabado."

> "Isto é importante para dois motivos: primeiro, sabem exatamente o custo real do produto final. Segundo, controlam os componentes disponíveis e evitam situações em que prometem uma entrega mas falta um acessório."

### Exemplos a mencionar para a Virgin Details

| Transformação | Componentes | Produto final |
|---|---|---|
| Cisterna com kit completo | Cisterna SEICC + Tampa T32 + Filtro NS100 | Kit Cisterna Subterrânea pronto a instalar |
| Bomba com caixa | Bomba Shark + Quadro elétrico + Acessórios | Estação de bombagem completa |
| Sistema pluvial | Cisterna IAP3000 + Bomba + Filtro | Sistema de recuperação de água completo |

### Perguntas de qualificação

- "Quais são as montagens ou kits mais frequentes que fazem antes de entregar ao cliente?"
- "Hoje como é que controlam os componentes que ficam — se têm peças de reposição em stock depois de montar?"

---

## Bloco 6 — Stock e inventário: fim do Excel (7 min)

**Acesso:** Menu → Inventário → Produtos / Movimentos

### O que mostrar

1. **Lista de produtos** com stock configurado
   - Mostrar as categorias, as variantes, os preços de custo
2. **Abrir um produto** — ex: SEICC-AG (cisternas)
   - Mostrar tab **Inventário** → Rotas: MTO + Comprar
   - *"Estas rotas dizem ao sistema que este produto não está em stock fixo — é encomendado ao fornecedor quando um cliente fizer um pedido."*
3. **Mostrar a diferença entre produtos com stock fixo vs. MTO**
   - Starplast (Itália) → podem ter stock físico no armazém
   - HASA/Jeremias (Espanha) → dropshipping, sem stock na Virgin Details

### O que dizer

> "Hoje controlam o stock num Excel. O problema do Excel é que não está ligado ao resto — quando enviam uma encomenda, têm de atualizar o Excel manualmente. Quando recebem mercadoria, idem. Quando há um erro, não sabem quando aconteceu nem quem o fez."

> "Com o Odoo, cada receção de mercadoria atualiza o stock automaticamente. Cada entrega desconta o stock. Cada encomenda a fornecedor reserva o stock. Em qualquer momento, sabem exatamente o que têm, onde está, e o que está prometido a clientes."

> "E quando crescerem e quiserem usar leitores de código de barras no armazém — o módulo está preparado para isso. Sem precisar de mudar de sistema."

### Perguntas de qualificação

- "Têm um armazém físico na Maia? Só um espaço de arrumação, ou um armazém operacional com muitos movimentos?"
- "Há artigos que mantêm em stock fixo (compram antes de ter encomenda) vs. artigos que só encomendamos quando o cliente pede?"

---

## Bloco 7 — Projetos: obras, custos e rentabilidade (7 min)

**Acesso:** Menu → Projeto

> *Nota para o consultor: O módulo Project está instalado. Pode mostrar a vista de projetos mesmo que não existam projetos de obra configurados no protótipo.*

### O que dizer

> "Muitas vezes, uma venda não é apenas um produto — é um projeto. Uma instalação de sistema de tratamento de águas no Funchal, um sistema fotovoltaico para um armazém em Lisboa. Cada um tem custos de transporte, deslocação, instalação, peças de substituição."

> "Com o módulo de projetos do Odoo, cada obra é um projeto. Têm visibilidade de todos os custos — materiais, mão de obra, deslocações, despesas. E sabem, no final, se o projeto foi rentável."

> "Ainda mais poderoso com a contabilidade analítica: cada custo é imputado ao projeto correto. Quando chega o final do mês, o relatório já está feito — quanto faturaram, quanto custou, qual foi a margem."

### Funcionalidades a mencionar

| Funcionalidade | O que faz |
|---|---|
| Projetos por obra | Cada instalação é um projeto com tarefas e fases |
| Custos diretos | Imputação de compras, despesas e tempos ao projeto |
| Despesas de equipa | Combustível, portagens, almoços — registados e aprovados no telemóvel |
| Margem por projeto | Receita - custos = rentabilidade em tempo real |
| Contabilidade analítica | Cada projeto tem conta analítica — relatórios automáticos |

### Perguntas de qualificação

- "A Virgin Details faz instalações diretamente, ou apenas vende e o cliente/instalador trata da instalação?"
- "Têm equipa em campo com despesas — combustível, portagens, deslocações? Como é que isso é gerido hoje?"

---

## Bloco 8 — Faturação e contabilidade portuguesa (7 min)

**Acesso:** Menu → Contabilidade (ou demonstrar a partir de uma encomenda confirmada)

### O que mostrar

1. **A partir de S00008** (Nextgreen, encomenda confirmada)
   - Mostrar o botão **Criar Fatura** (sem clicar se preferir não criar dados)
   - *"Com um clique, a encomenda confirmada torna-se uma fatura. O sistema já sabe o cliente, os produtos, os preços, o IVA."*
2. **Mencionar conformidade AT**
   - SAF-T exportável para entrega ao contabilista ou AT
   - Séries de faturação comunicadas à AT
3. **Condições de pagamento**
   - 30 dias / 60 dias / imediato / adiantamento
   - *"Pode definir condições diferentes por cliente — a Starplast fatura a 60 dias, o cliente paga a 30? O sistema controla os prazos e avisa-os dos pagamentos pendentes."*

### O que dizer

> "Hoje usam o PHC GO para faturar. O Odoo substitui-o completamente — e ainda liga a faturação ao stock, às compras e aos projetos. Deixam de ter de criar manualmente a fatura no PHC depois de ter processado a encomenda noutro sítio."

> "A localização portuguesa já está configurada — IVA 23%, plano de contas português, SAF-T. Se tiverem acordado pagamentos antecipados com alguns clientes, o sistema gere isso também."

> "A reconciliação bancária é automática — importam o extrato do banco e o Odoo faz o matching com os pagamentos registados. Poupam tempo e reduzem erros."

### Perguntas de qualificação

- "A Virgin Details emite as faturas em nome próprio, ou nalgumas situações é a Starplast ou a HASA que fatura diretamente ao cliente?"
- "Têm clientes que pagam antecipadamente (antes de receber os produtos)?"
- "Com que banco trabalham? Os extratos vêm em formato OFX ou CSV?"

---

## Bloco 9 — Reporting e visão de gestão (5 min)

**Acesso:** Menu → Contabilidade → Relatórios / ou Dashboards

### O que dizer

> "Uma das maiores frustrações que identificámos é a falta de visão integrada. Para saber como está o negócio, têm de consultar o PHC, abrir o Excel, ver a ferramenta de tarefas — e tentar juntar tudo na cabeça."

> "Com o Odoo, os relatórios são gerados automaticamente a partir dos dados que já introduziram. Não precisam de exportar para Excel para fazer um relatório — o relatório está sempre atualizado."

### Relatórios disponíveis

| Relatório | O que mostra |
|---|---|
| Pipeline CRM | Valor total por fase, taxa de conversão, negócios por comercial |
| Análise de vendas | Faturação por cliente, por produto, por marca, por período |
| Margem por produto | Diferença entre preço de venda e custo de compra |
| Conta corrente de clientes | Saldos pendentes, vencidos, por vencer |
| Conta corrente de fornecedores | O que devem à Starplast, HASA, Jeremias, Sunerg |
| Rentabilidade por projeto | Receita vs. custos vs. margem por obra |
| Balanço e DR | Demonstração de resultados e balanço em tempo real |
| SAF-T | Exportação para o contabilista ou AT |

> "E com a multiempresa, podem ter um relatório consolidado das duas empresas do grupo — ou ver cada uma separadamente."

---

## Bloco 10 — Mobilidade: a equipa em campo (3 min)

**Acesso:** Mostrar no telemóvel ou com browser a simular mobile*

### O que dizer

> "O Odoo é uma aplicação cloud. Funciona no computador, no tablet e no telemóvel — sem instalar nada, sem VPN."

> "Quando o comercial está com um cliente em Leiria e precisa de saber se têm stock da bomba Shark 100W — abre o telemóvel, consulta o stock em 10 segundos."

> "Quando fecha um negócio no local, cria o orçamento diretamente — o cliente recebe por email na hora, sem esperar que o comercial chegue ao escritório para o criar no computador."

### Funcionalidades móveis

- Consultar stock disponível em tempo real
- Criar e enviar orçamentos no local
- Ver histórico completo de um cliente (encomendas, faturas, comunicações)
- Acompanhar o estado de entregas e receções
- Registar despesas (combustível, portagens) com foto do recibo

---

## Bloco 11 — Multiempresa e crescimento futuro (5 min)

### O que dizer

> "A Virgin Details faz parte de um grupo de duas empresas. Hoje, se precisam de ver os números consolidados do grupo, é um trabalho manual. Com o Odoo multiempresa, os dois negócios estão no mesmo sistema — com separação total de documentos, stock e contabilidade, mas com visibilidade consolidada para a gestão."

> "Os utilizadores podem operar nas duas empresas com um único login. Um orçamento na empresa A pode gerar uma compra na empresa B. Os relatórios podem ser individuais ou consolidados."

> "E quando a empresa crescer — mais produtos, mais clientes, mais volume — a plataforma cresce com ela. Sem mudar de sistema. Sem migrar dados. Apenas ativar os módulos que fizerem falta."

### Roadmap de crescimento

| Quando necessário | Módulo a ativar |
|---|---|
| Agora (Fase 2) | Manufacturing (BoM) — transformação de artigos |
| Agora (Fase 2) | Multi-Company — segunda empresa do grupo |
| A médio prazo | Barcode — armazém com leitores |
| A médio prazo | Sign — aprovação eletrónica de orçamentos |
| Futuro | Helpdesk — suporte pós-venda |
| Futuro | e-Commerce — loja online para clientes B2B |

---

## Bloco 12 — Próximos passos e levantamento de questões (10 min)

### Questões de levantamento a colocar

Abordar obrigatoriamente as marcadas com ★:

| ★ | Pergunta | Tema |
|---|---|---|
| ★ | "A Virgin Details emite faturas em nome próprio, ou nalgumas situações é o fornecedor europeu que fatura diretamente?" | Modelo de faturação |
| ★ | "Qual é a segunda empresa do grupo? Tem atividade semelhante ou complementar?" | Multiempresa |
| ★ | "Quais os produtos que recebem fisicamente em armazém vs. os que fazem dropshipping direto de Espanha?" | Logística / Stock |
| ★ | "Quantas pessoas vão usar o sistema e que funções têm?" | Licenciamento |
| ★ | "Fazem transformação/montagem de produtos regularmente? Quais são os kits mais comuns?" | BoM |
| | "Têm pagamentos antecipados de clientes ou pagam sempre depois da entrega?" | Tesouraria |
| | "Com que banco trabalham? Os extratos chegam por OFX/SEPA?" | Reconciliação |
| | "Têm equipa em campo com despesas a registar?" | Mobilidade / Expenses |
| | "A Virgin Details faz instalações diretamente, ou apenas vende?" | Projetos |
| | "Têm algum requisito de aprovação interna antes de enviar um orçamento?" | Aprovações |

### Proposta de próximos passos

1. **Reunião de levantamento de requisitos** (2–3 horas)
   - Validar os pontos acima
   - Mapear processos reais passo a passo
   - Identificar dados a migrar do PHC GO e do Excel
   - Confirmar âmbito multiempresa

2. **Proposta comercial detalhada**
   - Âmbito Fase 1 + Fase 2
   - Orçamento por módulo e por fase
   - Plano de migração de dados

3. **Kick-off da implementação**
   - Arranque da Fase 1

### Mensagem de encerramento

> "O que construímos aqui serve para mostrar uma coisa simples: o Odoo já fala a linguagem da Virgin Details. Os vossos produtos, os vossos clientes, os vossos fornecedores europeus, o vosso fluxo comercial — tudo está aqui."

> "A implementação real vai ser mais aprofundada, adaptada exatamente ao modo como trabalham. O que preciso de vós é que nos contem como é o dia a dia — depois disso, dou-vos um orçamento rigoroso e um plano realista."

---

## Notas para o consultor

### Se a cliente perguntar sobre preços de implementação
Não dar valores nesta reunião.
> *"Preciso de terminar o levantamento antes de lhe dar um número que faça sentido. A proposta vem logo a seguir — normalmente em 5 a 7 dias úteis."*

### Se a cliente pedir funcionalidades não configuradas no protótipo
Ex: BoM específicos, multiempresa real, integração bancária.
> *"Não configurámos isso no protótipo, mas o Odoo suporta — já testámos em outros projetos. Vamos incluir no âmbito do levantamento."*

### Se a cliente questionar a segurança dos dados
> *"Este protótipo usa dados de demonstração — nunca os emails reais. A instância real será da Virgin Details, com acesso exclusivo. O Odoo SaaS corre em infraestrutura Odoo com certificação ISO 27001."*

### Se a cliente comparar com o PHC GO
> *"O PHC GO é uma solução de faturação e contabilidade — faz bem o que faz. O Odoo é uma plataforma de gestão completa que inclui a faturação, mas também o CRM, o stock, as compras, os projetos e a mobilidade. A diferença não é só a faturação — é ter tudo integrado num único sistema."*

### Pontos sensíveis a gerir
- **Preços no protótipo:** São indicativos de demonstração baseados nos documentos. Se a cliente notar diferenças, confirmar que os preços reais serão migrados/configurados na implementação.
- **Emails de demo:** Os contactos têm emails de demonstração, nunca os reais — intencional por razões de privacidade no protótipo.
- **BoM não configurado:** O módulo Manufacturing está instalado mas as listas de materiais específicas requerem levantamento formal.
- **Segunda empresa:** Não configurada no protótipo — requer levantamento da estrutura do grupo.

---

*Parâmetro Global — Consultoria Informática S.A.*  
*it.odoo@parametro.global*
