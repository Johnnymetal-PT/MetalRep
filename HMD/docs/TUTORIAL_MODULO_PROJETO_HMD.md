# Tutorial — Usar o módulo Projeto no processo de venda da HMD

> Guia à medida do processo da HMD, construído a partir do documento
> **`Processo venda HMD.pdf`** enviado pela Nina em 29/07/2026 e do exemplo real
> indicado por ela, o projeto **Casa Ardor Tuscany**.
>
> Responde ao que ficou combinado na reunião de 27/07/2026: o que fazer **depois** de
> criar o projeto — delegação de tarefas, acompanhamento e onde ver o estado.
> Começa onde o tutorial de criação de projeto a partir do modelo acaba.
>
> Ambiente: Odoo 18.0 Enterprise · verificado na base de dados da HMD a 29/07/2026.

---

## 1. Antes de mais: o que o módulo Projeto é, e o que não é

O módulo Projeto é o **local onde a informação de uma encomenda se junta e onde se vê
quem está a fazer o quê**. Tem acesso à informação das outras aplicações — vendas,
compras, produção — mas **não traz automatismos com elas**.

Concretamente:

- O Odoo **não** move uma tarefa de etapa porque a encomenda entrou em produção.
- O Odoo **não** cria tarefas sozinho quando se confirma uma venda.
- Quem move as tarefas entre etapas são **as pessoas**.

Confirmámos na base de dados que não existe nenhuma automação configurada sobre tarefas
ou projetos — o comportamento é o padrão do Odoo. Vale a pena saber isto de início,
porque define o que se pode esperar do módulo e o que depende do hábito da equipa.

---

## 2. O vosso processo, e onde cada coisa vive no Odoo

Mapa entre as 4 fases do vosso documento e as aplicações do Odoo.

| A vossa fase | Onde vive no Odoo | O projeto serve para |
|---|---|---|
| **1.** CRM — contacto do cliente, dúvidas, desenhos, criação de produtos | CRM (oportunidade) → Produtos | Guardar o pedido original e as referências; uma tarefa por artigo ou divisão |
| **2.** Pedidos de orçamento a fornecedores e elaboração da proposta | **Compras** (pedidos de cotação) → Vendas (orçamento) | Ver num só lugar o que está pedido e o que falta |
| **3.** Proposta aceite, sinal pago, passagem para o backoffice | Vendas (encomenda confirmada) → Compras (encomendas a fornecedor) | **A passagem de informação:** mudar o responsável da tarefa e a etapa |
| **4.** Produção, controlo de qualidade, expedição | Produção / Qualidade / Inventário | Acompanhar o estado artigo a artigo até à expedição |

### Sobre a fase 2 — uma sugestão

No vosso documento escrevem que é importante *"monitorizar a quem já foi pedido
orçamento, que orçamentos já foram respondidos e se é necessário insistir"*.

Essa informação já existe, e **de forma mais completa, na aplicação Compras**: os
pedidos de cotação registam a quem foram enviados, quando, e o que voltou respondido,
sem ninguém ter de o anotar.

Notámos que alguns projetos criaram etapas de tarefa como `PRODUTOS A PEDIR COTAÇÃO`,
`A AGUARDAR ORÇAMENTO/INFO FORNECEDOR`, `ORCAMENTOS ENVIADOS` e `ORCAMENTOS RECEBIDOS`.
Faz todo o sentido como solução, mas obriga a manter a informação em dois sítios, que
tendem a desalinhar-se. A sugestão é: seguir os fornecedores em **Compras**, e no
projeto manter **uma** tarefa por artigo que avança de etapa.

---

## 3. O exemplo, ponta a ponta: Casa Ardor Tuscany

O projeto que a Nina indicou. Dados verificados na base de dados:

- Gestora: **Nina Hedderich** · Cliente: **CASA ARDOR SRL**
- **42 tarefas** · 23/03/2026 a 22/05/2026 · fase global **CONCLUÍDO**
- Encomenda associada: **`NE A/00053`**, 68 760,85 €
- Etapas: `Novo → DESENHO TECNICO FEITO → ENVIADO À CLIENTE → APROVADO POR CLIENTE →
  EM ORÇAMENTAÇÃO → EM PRODUÇÃO → CONTROLO DE QUALIDADE → EXPEDIDO`

**Estas etapas estão bem desenhadas** e correspondem exatamente ao vosso documento
escrito: os desenhos vão a aprovação do cliente antes de se pedirem orçamentos aos
fornecedores. Não há aqui nada a corrigir no desenho do processo.

### Como está a distribuição das tarefas hoje

| Etapa | Tarefas |
|---|---|
| Novo | 9 |
| DESENHO TECNICO FEITO | 0 |
| ENVIADO À CLIENTE | 1 |
| APROVADO POR CLIENTE | 0 |
| EM ORÇAMENTAÇÃO | 0 |
| EM PRODUÇÃO | 0 |
| CONTROLO DE QUALIDADE | 0 |
| **EXPEDIDO** | **32** |

> No kanban a coluna *Novo* mostra 8 cartões e não 9: uma das tarefas
> (`ESQUEMA SOFA ROLO`) é **subtarefa** de outra, e as subtarefas aparecem dentro da
> tarefa-mãe em vez de terem cartão próprio.

A leitura é: as tarefas ficam em *Novo* e depois aparecem em *Expedido*, sem passar
pelas etapas do meio.

**Isto é o padrão mais comum em qualquer arranque de Odoo, e tem uma explicação
simples:** a tarefa é criada no início, quando há tempo para a organizar, e é fechada
no fim, quando o artigo sai. No meio, quem está a trabalhar tem a informação na cabeça
e não precisa do Odoo para saber onde está — por isso o passo de arrastar o cartão
parece dispensável.

**O que se ganha em fazê-lo:** as etapas do meio são a única forma de o kanban
responder à pergunta *"em que ponto está esta encomenda?"* sem ir à encomenda — que é
precisamente o que a Nina levantou na reunião. Cada cartão movido é informação que
deixa de ser preciso pedir a alguém.

Dois outros pontos visíveis na mesma vista, ambos com solução fácil:

- As tarefas em *Expedido* já não têm responsável e mostram prazos antigos em vermelho
  (*"Há 38 dia(s)"*). Não afeta o trabalho feito, mas faz o kanban parecer atrasado
  quando não está. Fechar a tarefa em *Expedido* resolve.
- Há **duas lógicas de nomes** no mesmo projeto: divisões da casa (`BAR`,
  `MOM'S BEDROOM`, `LARGE GUEST BEDROOM`) e produtos (`LOLA DINING`,
  `PRIMARY SUITE BED`, `MEL ARMCHAIR`). Ambas funcionam; convém escolher uma — ver §7.

---

## 4. Os vossos 3 objetivos: o que o Odoo dá e o que depende da equipa

### Objetivo 1 — informação num só local, acessível a todos

**Já funciona hoje, sem configuração.** Cada tarefa tem:

- **Descrição** para o pedido, medidas e acabamentos;
- **Anexos** para desenhos técnicos e imagens de referência;
- **Conversa (chatter)** com todo o histórico de emails e comentários;
- ligação ao **cliente** e à **encomenda**.

**O que depende da equipa:** que a informação seja posta na tarefa. Um desenho que fica
no email de uma pessoa não está acessível a todos, e não há configuração que o
substitua.

### Objetivo 2 — cada pessoa percebe o seu papel

**O Odoo dá:** campo **Responsáveis**, **Data-limite**, **subtarefas** para partir
trabalho grande, e **atividades** para pedir uma ação concreta a alguém com prazo
(têm já dois tipos criados por vocês: *Fazer Desenho Técnico* e *Concluído*).

**Onde está hoje**, para referência:

| | |
|---|---|
| Tarefas na base de dados | 430 |
| Com responsável atribuído | 199 (46%) |
| Com data-limite | 21 (5%) |

Estes dois campos são o que alimenta os filtros pessoais — *As minhas tarefas*, a vista
de calendário, os avisos de prazo. Cada tarefa que ganha um responsável passa a
aparecer na lista dessa pessoa; cada data-limite preenchida passa a aparecer no
calendário e no Gantt. É a alteração com maior retorno imediato, e não custa nada além
do gesto.

> Dica: se não se souber ainda quem vai fazer, atribuir a quem decide. Vale mais do que
> deixar vazio, porque assim a tarefa aparece a alguém.

### Objetivo 3 — registo das alterações e análise no fim

**Já funciona hoje, automaticamente.** Cada mudança de etapa, de responsável e de prazo
fica registada na conversa da tarefa, com autor e data. É isso que permite, no fim,
reconstituir todo o percurso de uma encomenda sem ninguém ter tomado notas.

Para a parte da análise de **esforço** — quanto tempo levou cada fase — é preciso o
registo de horas, que não está ativo. A secção seguinte explica como o ativar e usar,
se quiserem.

---

## 5. Registo de horas (folhas de horas) — como ativar e usar

Não está ativo na vossa base de dados. Como é a peça que falta para o objetivo 3, fica
aqui explicado por inteiro, para poderem decidir com conhecimento.

### 5.1 O que é preciso instalar

Uma só opção, e **todas as dependências já estão instaladas** na vossa base
(*Colaboradores*, *Custo Horário do Colaborador*, *Contabilidade Analítica*):

> **Definições → Projeto → secção *Gestão de Tempo* → ativar *Folhas de Horas***
> (a opção diz *"Track time spent on projects and tasks"*)

Guardar. O Odoo instala o módulo e recarrega. **Convém fazê-lo fora de horas de maior
atividade**, porque a instalação de um módulo reinicia a aplicação por alguns
instantes.

### 5.2 O que aparece depois

- Uma aplicação nova, **Folhas de Horas**, com uma grelha semanal por pessoa;
- Em cada **tarefa**, um separador para lançar horas e três campos novos:
  **Tempo Gasto**, **Tempo Restante** e **Tempo Total Gasto** (tarefa + subtarefas);
- Em cada **projeto**, o total de horas e o acesso às folhas de horas do projeto;
- O campo **Horas Alocadas**, que já existe hoje nas tarefas, passa a ter par: o Odoo
  compara alocado com gasto e calcula o restante automaticamente.
  (Hoje está preenchido em 3 das 430 tarefas.)

### 5.3 Como se lança horas

Três formas, todas standard:

1. **Na tarefa** — separador das horas, indicar data, descrição e duração;
2. **Na app Folhas de Horas** — grelha da semana, escolher projeto e tarefa e escrever
   as horas por dia. É a forma mais rápida para quem lança no fim do dia;
3. **Cronómetro** — botão de iniciar/parar na própria tarefa, para quem prefere marcar
   em tempo real.

### 5.4 Custo por hora (opcional, mas é o que dá valor à análise)

O campo **Custo Horário** já existe na ficha de cada colaborador
(*Colaboradores → ficha → separador de RH*), e está a **0,00** nos 6 colaboradores.

Preenchendo-o, cada hora lançada passa a ter custo, e o projeto passa a mostrar o
custo real da mão de obra por encomenda — que cruzado com o valor da venda dá a
margem efetiva. Sem ele, ficam só as horas, o que já responde ao objetivo 3.

> Há um tutorial vosso sobre este tema: **Custo/hora do colaborador**.

### 5.5 O que isto exige da equipa

Sejamos claros, porque é o fator que decide se vale a pena: **o registo de horas só dá
resultado se for feito com regularidade.** Uma semana esquecida não se recupera com
fiabilidade. Na prática significa cada pessoa dedicar dois a três minutos por dia, ou
dez minutos no fim da semana.

A escala ajuda: são **6 colaboradores e 7 utilizadores internos**, não uma equipa
grande. E pode começar-se por um subconjunto — por exemplo, só o gabinete técnico, ou
só um projeto-piloto — e alargar depois.

### 5.6 O que passam a poder responder

- Quantas horas levou esta encomenda, e em que fase se concentraram;
- Que tipo de encomenda consome mais tempo do que o orçamentado;
- Qual foi a margem real, depois da mão de obra;
- Quanto tempo estimar num pedido parecido no futuro — que é literalmente o objetivo 3
  do vosso documento: *"utilizar a informação para futuros pedidos similares"*.

---

## 6. O dia-a-dia: o que fazer com uma tarefa

1. **Criar a tarefa** com um nome claro (ver §7) e o cliente preenchido.
2. **Atribuir responsável.**
3. **Pôr data-limite** quando houver compromisso com o cliente.
4. **Pôr a informação na tarefa:** descrição e desenhos em anexo.
5. **Mover a tarefa de etapa quando o estado real muda.** No kanban é arrastar o cartão.
6. **Ao mudar de fase, mudar também o responsável** se o trabalho passou para outra
   pessoa. É assim que fica registada a passagem do comercial para o backoffice que
   referem na fase 3 do vosso processo.
7. **Usar atividades** para pedir algo concreto a alguém com prazo, em vez de o pedir
   por email.
8. **Fechar a tarefa** quando o artigo é expedido.

---

## 7. Duas escolhas que valem a pena fazer

### Número de etapas

O Casa Ardor tem 8 etapas e estão a ser usadas 3. Há dois caminhos, ambos válidos:

**Opção A — aproximar as etapas do que se usa.** Por exemplo
`Novo → Em curso → Controlo de qualidade → Expedido`. Menos detalhe, mas o kanban
reflete a realidade sem esforço adicional.

**Opção B — manter as 8 e criar o hábito de as percorrer.** Mais informação e melhor
acompanhamento, à custa de disciplina diária.

**A nossa sugestão é começar pela A** e evoluir para a B quando o hábito estiver
criado. Um kanban com 4 etapas todas usadas dá mais informação útil do que um com 8 em
que 5 estão vazias — e é mais fácil de manter.

### Nome das tarefas

- **Por artigo** (`LOLA DINING D150`) — melhor para acompanhar produção, controlo de
  qualidade e expedição, porque é o artigo que passa por essas fases;
- **Por divisão** (`MOM'S BEDROOM`) — melhor para conversar com o cliente.

Se precisarem das duas leituras, a forma indicada é **uma tarefa por divisão com
subtarefas por artigo**, em vez de as duas ao mesmo nível.

---

## 8. Onde ver o resumo do estado

A pergunta da Nina em reunião — ver o que se passa sem ir à encomenda:

- **Projeto → Projetos** (kanban): todos os projetos por fase global (`NOVO`,
  `ORÇAMENTAÇÃO`, `EM PRODUÇÃO`, `CONCLUÍDO`, `INTERNO HMD`, `Não ganhos`).
- **Dentro do projeto** (kanban de tarefas): o estado artigo a artigo.
- **Projeto → Tarefas**, agrupando por *Projeto* ou por *Responsáveis*: a carga de cada
  pessoa em todos os projetos.
- **Calendário e Gantt**: ficam úteis à medida que as tarefas tiverem datas.
- **Folhas de horas** (se ativarem): horas por projeto, por pessoa e por período.

> Dica de arrumação: dos 26 projetos criados desde 01/05/2026, 20 não têm nenhuma
> tarefa — são projetos gerados automaticamente a partir de orçamentos que não
> avançaram. Arquivá-los deixa o kanban de projetos mais legível, e não se perde nada:
> ficam sempre recuperáveis pelo filtro de arquivados.

---

## 9. Checklist

- [ ] Toda a tarefa tem **responsável**
- [ ] Tarefas com compromisso ao cliente têm **data-limite**
- [ ] Desenhos e referências estão **anexados à tarefa**
- [ ] A tarefa **muda de etapa** quando o estado real muda
- [ ] Ao passar do comercial para o backoffice, **muda o responsável**
- [ ] O seguimento de orçamentos a fornecedores está em **Compras**
- [ ] Uma só **lógica de nomes** por projeto
- [ ] Projetos sem tarefas que não vão avançar estão **arquivados**

---

## 10. Três decisões vossas

1. **Aproximar as etapas do uso (A) ou criar o hábito das 8 (B)?**
2. **Ativar o registo de horas?** A §5 tem tudo o que é preciso. Se quiserem, podemos
   ativá-lo e acompanhar as primeiras semanas.
3. **Arquivar os projetos sem tarefas?** São 20 desde maio.

Estamos disponíveis para uma sessão curta sobre a base de testes, a percorrer uma
encomenda de ponta a ponta com o vosso próprio processo.
