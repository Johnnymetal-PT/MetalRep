# Levantamento — Módulo Projeto na HMD

> **Documento interno de trabalho.** Não é o guião para o cliente.
> Serve de base à tarefa **6609** `[PROJ] Guião à medida do módulo Projeto` e existe
> porque o guião final está **bloqueado** à espera de input da cliente.
>
> **Data:** 29/07/2026 · **Fonte:** leitura só-leitura da BD `HMD` (Odoo 18.0
> Enterprise on-premise) via XML-RPC · **Autor:** Parâmetro Global

Convenção da tarefa: `FACTO OBSERVADO` = medido na BD; `INFERÊNCIA` = conclusão
nossa a partir dos factos; `POR VALIDAR` = precisa de confirmação do cliente.

---

## 1. Porque este documento existe

A 6609 pede um guião do módulo Projeto com um exemplo ponta a ponta do processo da
HMD. A própria tarefa impõe uma dependência: a Nina ficou de enviar um documento
escrito com a necessidade da HMD e **2 exemplos concretos** da base de dados deles
(1:01:42), e a instrução é *"não arrancar o guião final antes de receber esse input"*.

`FACTO OBSERVADO` — a 29/07/2026 esse input **não chegou**: o chatter da 6609 tem
6 mensagens, todas notificações automáticas do sistema, e a tarefa **não tem anexos**.

O que segue é a parte que a tarefa autoriza entretanto: o levantamento das
capacidades standard, cruzado com o que está realmente configurado na BD deles.

---

## 2. O que está instalado — e o que não está

`FACTO OBSERVADO`

**Instalado:** `project`, `project_enterprise`, `project_todo`, `sale_project`,
`project_mrp`, `project_purchase`, `project_account`, `project_sale_expense`,
`documents_project`, `knowledge`.

**Não instalado:** `hr_timesheet`, `sale_timesheet`, `planning`, `project_forecast`,
`project_timesheet_holidays`, `industry_fsm`, `hr_timesheet_attendance`.

### 2.1 Bloqueio material: as folhas de horas não existem

A 6609 pede explicitamente que o guião cubra *"registo de folhas de horas"*, e foi
isso que o Bruno levantou em reunião (55:49). Mas:

`FACTO OBSERVADO` — `hr_timesheet` está `uninstalled`. O campo `allow_timesheets`
**não existe** em `project.project` nesta base de dados. Não há como registar horas
em tarefas.

`INFERÊNCIA` — não é possível documentar esta parte do guião sem primeiro instalar
o módulo. Documentar um ecrã que a cliente não tem seria pior do que não documentar.

**Decisão necessária** (ordem do framework: *standard já instalado → módulo standard
adicional → Studio → custom*): `hr_timesheet` é **módulo standard**, logo cabe no 2.º
nível — não é desenvolvimento. As opções são:

1. Instalar `hr_timesheet` e documentar as folhas de horas como pedido;
2. Retirar as folhas de horas do âmbito do guião e dizê-lo à cliente.

A opção 1 tem consequências que exigem enquadramento antes de avançar: acrescenta o
menu de horas a todos os projetos, implica definir custo/hora por colaborador (há já
um `TUTORIAL_CUSTO_HORA_COLABORADOR_HMD` no repositório) e cria expectativa de
registo diário de horas por toda a equipa. Não é uma instalação neutra.

---

## 3. As fases globais de projeto não são as que a documentação assume

`FACTO OBSERVADO` — `project.project.stage` tem **6 fases**:

| seq | fase | fold |
|---|---|---|
| 0 | NOVO | |
| 1 | ORÇAMENTAÇÃO | |
| 2 | Não ganhos | sim |
| 3 | EM PRODUÇÃO | |
| 4 | CONCLUÍDO | |
| 5 | INTERNO HMD | |

A tarefa **5670** (`Reformular fases projeto HMD — 3 fases globais + fases tarefa +
4 templates`) propunha reduzir isto a *Novo / Em Progresso / Concluído*.

`FACTO OBSERVADO` — a 5670 está em `state = 1_canceled`. Está na coluna
*Sprint Complete* do kanban, o que a faz parecer concluída, mas foi **cancelada**.

`INFERÊNCIA` — a reformulação nunca foi executada. Isto contradiz dois artefactos:

- a descrição da própria 6609, que lista a 5670 entre as *"tarefas já concluídas a consultar"*;
- o `docs/TUTORIAL_PROJETO_TEMPLATE_HMD.md`, **já entregue à cliente**, que descreve o
  projeto-modelo como *"resultado da reformulação de fases — 3 fases globais + fases de tarefa"*.

**Ação:** corrigir o tutorial entregue, ou executar a 5670. Não deixar as duas versões a coexistir.

---

## 4. As fases de tarefa estão sem governo

`FACTO OBSERVADO`

- **252** fases de tarefa (`project.task.type`) na base de dados;
- **108 delas (42%)** chamam-se apenas **"Novo"** ou **"New"**;
- **146** projetos no total.

`INFERÊNCIA` — cada projeto criado automaticamente traz consigo a sua própria fase
"Novo", e nada as consolida. Há também fases claramente pontuais criadas à mão:
`DINN 6 GAVETAS`, `ESTANTE LINHA`, `encontrar app`, `1`, `artigos`, `calculo preços`,
`costureira`, `limpeza`, `trolha`, `casa monica`, `fazer em moledo`, `livro boas vindas`.

Isto é relevante para o guião: **não existe hoje um processo padrão** a que o guião
possa apontar. O guião tem de *propor* um, não descrever o que está.

---

## 5. O projeto-modelo está praticamente vazio

`FACTO OBSERVADO` — o projeto **`Client Project Template`** (id 374) tem as 7 fases
bem desenhadas:

`ARTIGOS → PRECISA DESENHO TÉCNICO → DESENHO TÉCNICO FEITO → DESENHO APROVADO PELO CLEINTE → ARTIGO EM PRODUÇÃO → CONTROLO DE QUALIDADE → EXPEDIDO`

Mas tem **1 única tarefa**: `ARTIGO`, sem responsável, sem prazo, parada na fase
*DESENHO APROVADO PELO CLEINTE* (o erro ortográfico está na base de dados).

`INFERÊNCIA` — duplicar este modelo hoje **não poupa trabalho**: dá 7 fases e uma
tarefa órfã na fase errada. O `TUTORIAL_PROJETO_TEMPLATE_HMD.md` afirma que o modelo
*"tem as fases **e as tarefas-tipo** já organizadas"* e que *"o grosso do trabalho já
vem feito do modelo"* — não corresponde ao estado atual.

Isto explica diretamente a frase da Nina, *"há coisas que estamos a descobrir sozinhos"*:
seguiram o tutorial e o modelo não entregou o que o tutorial prometia.

**Ação:** povoar o modelo com as tarefas-tipo antes de qualquer formação sobre ele.
É trabalho pequeno e desbloqueia o valor do tutorial já entregue.

---

## 6. Disciplina de utilização — os números que sustentam a recomendação

`FACTO OBSERVADO`

| Métrica | Valor |
|---|---|
| Tarefas no total | 429 |
| **Sem responsável atribuído** | **231 (53%)** |
| **Sem prazo** | **408 (95%)** |
| Projetos criados desde 01/05/2026 | 26 |
| **Desses, com zero tarefas** | **20 (76%)** |

`INFERÊNCIA` — estes números são o argumento mais forte do guião. A Nina quer
*"não falhar nada desde a criação do pedido do cliente"* (56:17), mas mais de metade
das tarefas não tem ninguém responsável e praticamente nenhuma tem data. Nenhum painel
resolve isto: é disciplina de preenchimento, não configuração.

Os 76% de projetos vazios também respondem à pergunta dela em 57:23 (*ver um resumo do
que está a acontecer no projeto*): a maioria dos projetos criados a partir de
orçamento/CRM fica como casca vazia, portanto não há nada para resumir.

---

## 7. O processo real da HMD, reconstruído a partir da base de dados

Este é o achado mais útil do levantamento, e **substitui parcialmente** os exemplos
que faltam da Nina.

`FACTO OBSERVADO` — vários projetos reais convergiram, sem coordenação, para
pipelines muito parecidos:

| Projeto | Fases |
|---|---|
| Client Project Template (374) | ARTIGOS → PRECISA DESENHO TÉCNICO → DESENHO TÉCNICO FEITO → APROVADO PELO CLIENTE → ARTIGO EM PRODUÇÃO → CONTROLO DE QUALIDADE → EXPEDIDO |
| Casa Ardor Tuscany (272) | Novo → DESENHO TÉCNICO FEITO → ENVIADO À CLIENTE → APROVADO POR CLIENTE → EM ORÇAMENTAÇÃO → EM PRODUÇÃO → CONTROLO DE QUALIDADE → EXPEDIDO |
| Sofitel Presidential Palace Malabo (300) | ARTIGOS → DESENVOLVIMENTO → PEDIDO DE ORÇAMENTO → ENCOMENDAS A FORNECEDOR → PRODUÇÃO → LOGÍSTICA → CONCLUÍDA |
| Sofitel Dublin (398) | Novo Pedido → Orçamentação → Manufatura → Montagem → Entregue |
| Banco Mira Decor Walter (396) | Novo Pedido → Desenho técnico → Pedido de Orçamento → Enviado ao cliente → Entregue |
| Caixa Amostras (212) | New Orders → Material Sourcing → Manufacturing → Assembling → CLIENTES A PEDIR → Delivered |
| Produtos Novos (361) | PRODUTOS NOVOS → ENVIO ORÇAMENTOS → PRODUÇÃO → Montagem → Entregue |

`INFERÊNCIA` — a espinha comum é consistente e é o processo da HMD:

**Pedido do cliente → Desenho técnico → Aprovação do cliente → Orçamentação /
Compras → Produção → Controlo de qualidade → Expedição**

~~`POR VALIDAR` com a Nina: se `Orçamentação` vem antes ou depois da aprovação do
desenho.~~ **RESOLVIDO em 29/07/2026** com o documento `Processo venda HMD.pdf`
enviado pela Nina: os desenhos vão a aprovação do cliente (ponto 1c) **antes** de se
pedirem orçamentos aos fornecedores (ponto 2a). Logo a ordem do **Casa Ardor está
correta** e é o Banco Mira o caso desalinhado.

Nota: `PRODUTOS NOVOS` (361) é o projeto mais saudável da base — 19 tarefas, a maioria
com responsável. Serve de segundo exemplo real. Contém também três tarefas que parecem
tarefas-tipo esquecidas num projeto vivo (`Fazer o desenho`, `Pedir Orçamento`,
`Calcular Preço de venda`) — são boas candidatas a tarefas-tipo do modelo.

---

## 8. O que é standard e responde ao que a cliente pediu

Mapeamento do pedido (55:49 — delegação, registo de horas, acompanhamento) às
capacidades disponíveis **nesta** base de dados:

| Necessidade | Standard disponível | Estado na HMD |
|---|---|---|
| Delegar tarefas a um responsável | campo *Responsáveis* na tarefa | existe; **usado em 47% das tarefas** |
| Prazos e alertas | *Data-limite* + vista de calendário/gantt (`project_enterprise`) | existe; **usado em 5% das tarefas** |
| Etapas por departamento | fases de tarefa por projeto | existe, mas sem padrão (252 fases) |
| Subtarefas | nativo em Odoo 18 | disponível, sem uso relevante |
| Atividades e lembretes | `mail.activity` | 8 tipos, 2 criados pela HMD (`Fazer Desenho Técnico`, `Concluído`) |
| Registo de horas | `hr_timesheet` | **não instalado** — ver §2.1 |
| Resumo do estado do projeto | kanban de projetos por fase global + agrupamentos | existe; limitado pelos 76% de projetos vazios |
| Modelos de projeto | duplicação de projeto | `is_template` **não existe** em Odoo 18; o método é duplicar, como no tutorial |
| Ligação venda → projeto | `sale_project` | instalado; ligação produto↔projeto feita na tarefa 4313 |

---

## 9. O que **não** é automático — a advertência do Bruno tem suporte factual

O Bruno avisou a cliente (57:45–1:00:26) que o módulo Projeto não reflete
automaticamente as etapas operacionais. Isto confirma-se:

`FACTO OBSERVADO` — existem **19 automações** (`base.automation`) na base de dados e
**nenhuma** atua sobre `project.task` ou `project.project`.

`INFERÊNCIA` — nada move tarefas entre fases. Se as fases espelharem departamentos
(gabinete técnico, compras, produção, expedição, montagem), a movimentação é
**100% manual**. O guião deve dizer isto de forma inequívoca, e os números da §6
mostram que a disciplina necessária ainda não existe — o que reforça a recomendação
de **template inicial simples**, não de pipeline ambicioso.

---

## 10. Decisões necessárias antes de escrever o guião

1. **Folhas de horas** — instalar `hr_timesheet` ou retirar do âmbito? (§2.1)
2. **Tarefa 5670** — executar a reformulação das fases globais, ou corrigir a
   documentação já entregue que a pressupõe? (§3)
3. **Povoar o `Client Project Template`** com tarefas-tipo antes da formação. (§5)
4. **Validar a espinha do processo** com a Nina, em especial a posição da
   orçamentação. (§7)

Os pontos 1 e 2 mexem em âmbito e devem ser confirmados com o Bruno Pinheiro; o
projeto está em fase de fecho.

---

## 11. Input do cliente — RECEBIDO em 29/07/2026

A dependência está **satisfeita**. Após insistência na thread da tarefa 6609 (14:43),
a Nina respondeu às 14:50 com:

- **`Processo venda HMD.pdf`** — o processo de venda em 4 fases e os 3 objetivos com a
  app Projeto (transcrito na §12);
- **2 capturas de ecrã** do kanban do Casa Ardor;
- o exemplo indicado: **Projeto Casa Ardor Tuscany** (id 272), gestora Nina Hedderich,
  cliente CASA ARDOR SRL, 42 tarefas, 23/03/2026 a 22/05/2026, encomenda associada
  `NE A/00053` de 68 760,85 €. (O link que enviou aponta para a ação 912, *Tasks*, com
  filtro *As minhas tarefas* — é a vista de tarefas, não o projeto.)

## 12. O processo da HMD nas palavras do cliente

Do `Processo venda HMD.pdf`:

1. **CRM — contacto do cliente.** Pedido por email ou em feira: lista de produtos,
   quantidades, acabamento, desenhos técnicos ou imagens de referência. A equipa tira
   dúvidas e reúne informação por produto para pedir orçamentos e elaborar proposta.
   Se necessário, envia desenhos ao cliente para confirmar. Criam-se os produtos para
   fazer as solicitações de cotação e preparar a ordem de venda.
2. **Elaboração de proposta.** Pedem-se orçamentos a vários fornecedores — *"é
   importante registar toda a informação enviada e recebida e conseguir facilmente
   monitorizar a quem já foi pedido orçamento, que orçamentos já foram respondidos e
   se é necessário insistir"*. Reunidos os custos, elabora-se o orçamento. Proposta
   enviada, aguarda feedback; pode ser aceite ou não.
3. **Proposta aceite e confirmação de encomenda.** Cliente aprova e paga sinal.
   *"Nesta fase é muito importante a passagem de informação da equipa comercial para o
   backoffice"* — garantir que as encomendas a fornecedor são colocadas corretamente e
   não há componentes em falta. Confirmar prazos e planear datas de conclusão e QC.
4. **Produção, controlo de qualidade e expedição.** Fornecedor entrega → QC antes de
   embalar. Cliente recebe proforma para pagar o restante antes da expedição. Com tudo
   pronto e embalado, marca-se a expedição.

**Os 3 objetivos declarados:**

1. Toda a informação do pedido e dos produtos **num só local, acessível a todos**;
2. Facilitar o controlo e gestão de tarefas — *"cada pessoa percebe o seu papel"*;
3. Manter registo de qualquer alteração e, no fim, **analisar o processo completo**,
   detetar falhas e melhorias e reutilizar para pedidos similares.

## 13. O que as capturas da Nina revelam

`FACTO OBSERVADO` — no kanban do Casa Ardor que ela própria enviou:

| Etapa | Tarefas |
|---|---|
| Novo | 8 |
| DESENHO TECNICO FEITO | **0** |
| ENVIADO À CLIENTE | 1 |
| APROVADO POR CLIENTE | **0** |
| EM ORÇAMENTAÇÃO | **0** |
| EM PRODUÇÃO | **0** |
| CONTROLO DE QUALIDADE | **0** |
| EXPEDIDO | **32** |

`INFERÊNCIA` — as tarefas saltam de *Novo* diretamente para *Expedido*. As cinco
etapas intermédias, que são precisamente as que dariam o acompanhamento do objetivo 2,
**não são usadas**. As tarefas em *Expedido* perderam responsável e mostram prazos
vencidos em vermelho (*"Há 38 dia(s)"*), sinal de que não foram atualizadas ao longo
do caminho. Há ainda duas lógicas de nomenclatura misturadas no mesmo projeto:
**divisões** da casa (`BAR`, `MOM'S BEDROOM`) e **produtos** (`LOLA DINING`,
`PRIMARY SUITE BED`).

Este é o ponto central do guião: o problema não é falta de funcionalidade, é o
percurso das tarefas não estar a ser feito. Dizê-lo com cuidado — a Nina enviou estas
capturas a mostrar como usam, não a pedir crítica.

## 14. Nota sobre a fase 2 do processo dela

O acompanhamento de *"a quem já foi pedido orçamento e quem já respondeu"* **não é
trabalho do módulo Projeto** — é de **Compras** (pedidos de cotação). O módulo
`project_purchase` está instalado e liga as duas coisas. Vários projetos da HMD já
improvisaram isto como etapas de tarefa (`PRODUTOS A PEDIR COTAÇÃO`, `A AGUARDAR
ORÇAMENTO/INFO FORNECEDOR`, `ORCAMENTOS ENVIADOS`, `ORCAMENTOS RECEBIDOS`). O guião
deve redirecionar isto para Compras em vez de o replicar em etapas.
