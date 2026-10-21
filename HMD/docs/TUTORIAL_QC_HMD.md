# Tutorial — Controlo de Qualidade (QC) no Odoo 18 (HMD)

> Guia completo para configurar e usar o módulo **Qualidade** do Odoo 18.
> O módulo é poderoso mas pouco intuitivo de configurar — este guia segue a
> ordem certa: primeiro perceber as peças, depois configurar, depois usar no
> dia-a-dia.

## Índice
1. [As 4 peças do módulo](#1-as-4-peças-do-módulo)
2. [Configuração inicial (uma vez)](#2-configuração-inicial-uma-vez)
3. [Pontos de Controlo — o que dispara as verificações](#3-pontos-de-controlo)
4. [Tipos de teste explicados](#4-tipos-de-teste-explicados)
5. [Verificações de Qualidade — automáticas e espontâneas](#5-verificações-de-qualidade)
6. [Alertas de Qualidade — quando algo corre mal](#6-alertas-de-qualidade)
7. [Filtros e vistas guardadas + kanban](#7-filtros-e-vistas-guardadas--kanban)
8. [Data da verificação, filtros por data e calendário](#8-data-da-verificação-filtros-por-data-e-calendário)
9. [Verificações em várias etapas (várias visitas)](#9-verificações-em-várias-etapas)
10. [Fluxo do dia-a-dia HMD](#10-fluxo-do-dia-a-dia-hmd)
11. [Boas práticas](#11-boas-práticas)
12. [Resumo](#12-resumo)

---

## 1. As 4 peças do módulo

O módulo Qualidade assenta em quatro conceitos. Perceber isto evita 90% da
confusão:

| Peça | O que é | Onde |
|---|---|---|
| **Ponto de Controlo** (*Control Point*) | A **regra**: "neste produto/operação, faz esta verificação". É o que **gera automaticamente** as verificações. | Qualidade → Pontos de Controlo de Qualidade |
| **Verificação** (*Quality Check*) | A **tarefa concreta** a fazer (passou/reprovou, medir, tirar foto…). Pode nascer de um ponto ou ser criada à mão. | Qualidade → Verificações de Qualidade |
| **Alerta** (*Quality Alert*) | O **problema** levantado quando algo falha. Tem equipa, fase, causa-raiz e ações corretivas. | Qualidade → Alertas de Qualidade |
| **Equipa** (*Quality Team*) | Quem trata das verificações e alertas. | Qualidade → Configuração → Equipas |

> Regra mental: **Ponto = regra automática**; **Verificação = o que se faz**;
> **Alerta = o que correu mal**.

---

## 2. Configuração inicial (uma vez)

Antes de criar pontos de controlo, prepara a base em **Qualidade → Configuração**:

1. **Equipas de Qualidade** — cria pelo menos uma (ex.: `Qualidade HMD`).
   Define quem recebe e trata as verificações/alertas.
2. **Fases de Alerta** (*Alert Stages*) — confirma as fases do kanban de alertas
   (ex.: *Novo → Em curso → Resolvido*). A última fase deve estar marcada como
   "concluída".
3. **Causas-raiz** e **Etiquetas** (opcional) — para classificar alertas
   (ex.: causa `Defeito de fornecedor`, etiqueta `Risco`).

> Estes passos fazem-se uma única vez. Depois mexe-se raramente.

---

## 3. Pontos de Controlo

O **Ponto de Controlo** é o coração da automação: define **quando** e **sobre o
quê** o Odoo cria uma verificação.

**Criar:** Qualidade → Pontos de Controlo de Qualidade → **Novo**.

Campos-chave:

| Campo | Para quê |
|---|---|
| **Título** | Nome da verificação (ex.: `Inspeção visual à receção`) |
| **Produtos / Categoria de produto** | A que produtos se aplica (deixa em branco/categoria para abranger muitos) |
| **Tipo(s) de operação** | **Quando** dispara: *Receções* (compras), *Fabrico* (MRP), *Entregas*, etc. **Tem de ser o tipo de operação exato** (cada armazém/operação é distinta). |
| **Frequência de Controlo** | *Todos* (gera **sempre**), *Aleatoriamente*, *Periodicamente* ou ***A pedido*** (**não** gera automático — cria-se à mão). |
| **Control per** (*Controlo por*) | *Operação* (1 verificação por receção), *Produto* (1 por produto) ou *Quantidade* (1 por quantidade registada). |
| **Equipa** | Quem fica responsável |
| **Tipo de teste** | O que se faz na verificação (ver secção 4) |
| **Instruções / Nota** | O que o operador deve verificar |

**Exemplo HMD:** Ponto `Inspeção à receção` → produtos da categoria *Tecidos* →
operação *Receções* → tipo de teste *Pass-Fail* → equipa *Qualidade HMD*.
A partir daí, **cada receção desses produtos gera automaticamente uma
verificação** para a equipa tratar.

> `IMPORTANTE` — **Quando é que uma receção gera VQ automaticamente?** A
> verificação é criada **ao confirmar o recebimento** (quando fica *Pronto*),
> e **só** se um Ponto de Controlo casar nas **3 condições**:
> 1. **Tipo de operação** igual ao da receção (ex.: "HMD Sarcol: Recebimentos" —
>    se o ponto estiver noutro tipo de receção, não dispara);
> 2. **Produto ou Categoria** que inclua o artigo (ou ambos em branco = todos);
> 3. **Frequência de Controlo = *Todos*** (se estiver em ***A pedido***, **não**
>    gera sozinho — tem de se criar pelo botão de verificação a pedido).
>
> Se um recebimento novo não gerou VQ, é quase sempre uma destas 3 que não bate.

### Distinguir artigos de compra (receções) de produtos de venda (fabrico/entrega)
As VQs das **receções** incidem sobre os **artigos de compra**; as que vêm de
**Fabrico (MRP)** ou **Entrega** incidem sobre os **produtos de venda**. Não há um
campo "compra vs venda" — a distinção faz-se com **pontos separados**:
- um ponto para **Receções**, restrito às **categorias dos artigos de compra**
  (componentes/matérias);
- outro ponto para **Fabrico** (ou **Entregas**), restrito à **categoria do
  produto acabado/de venda**.

O **tipo de operação** é o discriminador principal; a **categoria de produto**
afina o âmbito. (As encomendas de cliente não criam VQ diretamente — surgem via
o **Fabrico** ou a **Entrega** que delas resultam.)

---

## 4. Tipos de teste explicados

> **Importante — tipo de teste ≠ aprovar/reprovar.**
> **Todas** as verificações terminam sempre num **resultado Aprovado/Reprovado**
> (é o veredicto, igual para todas). O **tipo de teste** define apenas **o que se
> regista antes** de dar esse veredicto. Por isso, "Pass-Fail" não é redundante:
> é o tipo "**não registo nada extra, só dou o veredicto**".

O tipo de teste define o que o operador faz na verificação:

| Tipo | O que regista (antes de Aprovar/Reprovar) | Quando usar |
|---|---|---|
| **Pass - Fail** | Nada extra — só o veredicto | Inspeção visual simples (defeito sim/não) |
| **Tirar uma Foto** | **1 fotografia** (apenas uma) | Registo rápido de 1 imagem |
| **Medir** | Um **valor** dentro de um intervalo (mín/máx) | Dimensões, tolerâncias |
| **Instruções** | Lê instruções e confirma | Verificações guiadas sem dados |
| **Folha de trabalho** (*worksheet*) | Preenche um **formulário personalizado** | Verificação rica: **várias fotos** + dados estruturados |
| **Folha de cálculo** | Preenche uma folha de cálculo | Verificações com cálculos |

Em produção (MRP) há ainda tipos de fabrico: **Registar materiais consumidos**,
**Registar produção**, **Imprimir etiqueta**.

### Tirar uma Foto vs Folha de trabalho (decisão HMD)

- **Tirar uma Foto** guarda **apenas 1 fotografia** — é o limite deste tipo.
- A **Folha de trabalho** é um **formulário à medida** (template) que pode ter
  **vários campos de foto** + medições, observações, checkboxes. Fica guardada e
  abre-se pelo **botão (smart button)** na verificação. É o tipo por defeito do
  ponto de receção em armazém.

> **Recomendação HMD:** para registar **mais do que uma foto** ou uma verificação
> estruturada, usar a **Folha de trabalho** (não o "Tirar uma Foto"). A folha de
> trabalho é configurada por ponto de controlo (Configuração → Modelos de folha de
> trabalho / no próprio ponto).

---

## 5. Verificações de Qualidade

As verificações aparecem em **Qualidade → Verificações de Qualidade**. Há duas
formas de existirem:

### a) Automáticas (a partir de um Ponto de Controlo)
Geradas **ao confirmar** a operação definida no ponto (ex.: quando a receção fica
*Pronto*) — desde que o ponto case nas 3 condições da secção 3 (operação,
produto/categoria, frequência = *Todos*). Na **validação** da receção, o Odoo
apresenta as verificações pendentes para resolver. É o modo recomendado para o
que é recorrente.

### b) Espontâneas / manuais (no terreno)
Quando se deteta algo que **não estava previsto num ponto**, cria-se uma
verificação à mão:

1. Em **Verificações de Qualidade**, carrega em **Novo**.
2. Escolhe o **produto** (e receção/lote, se aplicável), a **equipa** e o
   **tipo de teste** (ex.: *Tirar uma Foto* + nota).
3. Regista o resultado (foto / passou-reprovou) e **guarda**.

> **Nota:** para tornar isto rápido no terreno (telemóvel/tablet), está prevista
> uma melhoria HMD (atalho de criação rápida) — entretanto, o fluxo acima já
> funciona em standard a partir do browser.

### Resultado de uma verificação
Em cada verificação, o operador marca **Passou** / **Reprovou** (ou regista
medida/foto). Se **reprovar**, deve-se **abrir um Alerta** (secção 6) a partir do
botão respetivo.

---

## 6. Alertas de Qualidade

Quando uma verificação falha (ou se deteta um problema), abre-se um **Alerta**:
é o mecanismo de acompanhamento até à resolução.

**Criar:** a partir de uma verificação reprovada (botão de alerta) ou em
Qualidade → Alertas de Qualidade → **Novo**.

Campos úteis:
- **Equipa** e **Fase** (kanban: *Novo → Em curso → Resolvido*);
- **Causa-raiz** (ex.: defeito de fornecedor, manuseamento);
- **Ação corretiva** e **Ação preventiva** (o que se fez e o que evita repetir);
- **Etiquetas** e **Prioridade**.

> O kanban de alertas (arrastar entre fases) dá a visão de "o que está por
> resolver" à equipa de qualidade.

---

## 7. Filtros e vistas guardadas + kanban

Para chegar com um clique ao que interessa, usa filtros guardados nas
**Verificações de Qualidade**.

### Como guardar uma vista favorita
1. Na barra de pesquisa, usa **Filtros** e **Agrupar por** até a lista estar como
   queres (ex.: filtro **Estado = A fazer**; agrupar por **Fornecedor**).
2. **Favoritos → Guardar pesquisa atual**.
3. Dá um **nome** (ex.: `QC Pendentes`) e marca, se fizer sentido:
   - **Usar por defeito** (abre logo nesta vista);
   - **Partilhar com todos os utilizadores** (recomendado para a equipa).

### As três vistas a criar (operacional HMD)

| Nome | Filtro | Agrupar por | Para quê |
|---|---|---|---|
| `QC Pendentes` | Estado = *A fazer* | — | Ver o que falta verificar |
| `QC por Tipo` | — | **Tipo** | Distribuir por tipo de verificação |
| `QC por Fornecedor` | (opcional: pendentes) | **Fornecedor** | Avaliar qualidade por fornecedor |

### Kanban
Troca a vista de **lista** para **kanban** (canto superior direito) e **Agrupar
por → Estado** para ver colunas *A fazer / Aprovado / Reprovado*. Podes guardar
o kanban como favorito tal como acima.

---

## 8. Data da verificação, filtros por data e calendário

A data de cada verificação é o campo **"Data de Controlo"** (*Checked Date*,
`control_date`).

`IMPORTANTE` — Este campo é **preenchido automaticamente** no momento em que
marcas **Aprovado/Reprovado**. É **editável** — podes **corrigi-lo a posteriori**
para a data real da inspeção.

- **Ver a data na lista:** ativa a coluna **"Checked Date"** pelo menu de colunas
  (ícone ⚙ no canto da lista).
- **Filtrar/agrupar por data:** Filtros / Agrupar por → **Data de Controlo**.

⚠️ **Calendário e data planeada (limitações do standard):**
- **Não existe vista de calendário nas Verificações de Qualidade** em standard — a
  vista de calendário **só existe nos Alertas de Qualidade** (pela data de
  atribuição). É o comportamento nativo.
- **Não existe "data planeada"** na verificação: a `Data de Controlo` só fica
  preenchida **depois** de marcado o veredicto, logo não serve para planear o que
  **falta fazer** (ex.: "que verificações tenho esta semana").

> `MELHORIA HMD (em curso)` — Para planeamento (saber as verificações da semana,
> planear idas à produção e alertas pela data prevista do fornecedor), vamos
> acrescentar uma **Data Planeada** na verificação e uma **vista de calendário**
> das verificações, com base para **alertas automáticos** por essa data.

⚠️ **Visitas em datas diferentes:** se a peça foi vista num dia (ex.: 14/5) mas só
marcas o veredicto noutro dia, a Data de Controlo fica com a data em que marcaste,
**não a da visita**. Se a data da visita é importante, marca o veredicto **no dia
da visita** ou **edita** a Data de Controlo para a data real.

---

## 9. Verificações em várias etapas (ex.: a mesma peça em várias visitas)

Quando uma peça é vista **várias vezes** (no fornecedor, na receção…) ao longo do
tempo — como aconteceu no caso "OSLO ESPECIAL" — o desenho recomendado é:

1. **Uma verificação (QC) por inspeção formal** — uma por visita/etapa que mereça
   veredicto. Cada uma com a sua **Data de Controlo**, foto(s)/folha de trabalho e
   Aprovado/Reprovado. Assim consegues **filtrar e ver a progressão** por data.
2. **Um Alerta de Qualidade** aberto no primeiro defeito, que acompanha o problema
   pelas **fases** (Novo → Em curso → Resolvido) com a **ação corretiva** — é o
   sítio próprio para o "fio condutor" até estar resolvido.

> **Porque não só o chatter?** Registar tudo no chatter de uma única verificação
> funciona, mas é **texto livre**: não dá para filtrar nem reportar por data/etapa.
> A combinação **QC por visita + Alerta** dá rastreio estruturado.

**Notas:**
- Uma **verificação espontânea** (criada à mão) é **independente** e **não
  interfere** com a verificação gerada pelo ponto de controlo — coexistem.
- Criar **mais do que uma QC** para a mesma peça em etapas diferentes é **correto**
  e recomendado (não é duplicação indevida).

---

## 10. Fluxo do dia-a-dia HMD

1. **Receção/Fabrico** dispara verificações automáticas (dos pontos de controlo).
2. O operador abre **`QC Pendentes`** e trata a lista: marca Passou/Reprovou,
   tira foto quando aplicável.
3. Se algo **reprovar** → abre **Alerta** com causa-raiz e ação corretiva.
4. No terreno, se aparecer algo não previsto → cria **verificação espontânea**.
5. A equipa acompanha os **alertas** no kanban até *Resolvido*.

---

## 11. Boas práticas

- **Começa simples:** 2-3 pontos de controlo bem definidos valem mais do que 20
  confusos. Cresce conforme a necessidade.
- **Usa categorias de produto** nos pontos (em vez de produto a produto) para
  abranger muitos artigos com uma só regra.
- **Várias fotos → Folha de trabalho:** para registar mais do que uma foto ou uma
  verificação estruturada, usar a **Folha de trabalho** (o "Tirar uma Foto" só
  guarda 1 imagem).
- **Uma QC por visita** quando a peça é inspecionada em várias etapas; um **Alerta**
  para o fio condutor do problema.
- **Alerta = sempre que reprova:** não deixar reprovações sem alerta, senão
  perde-se o acompanhamento.
- **Vistas partilhadas:** cria as vistas favoritas uma vez e partilha com a
  equipa — evita que cada pessoa refaça filtros.
- **Não precisa de programação:** pontos, verificações, alertas, equipas e vistas
  são tudo configuração standard, sem risco.

---

## 12. Resumo

1. **Ponto de Controlo** = regra que gera verificações automáticas (produto +
   operação + tipo de teste).
2. **Tipo de teste ≠ veredicto:** todas acabam em Aprovado/Reprovado; o tipo só
   define o que se regista. Para **várias fotos**, usar **Folha de trabalho**.
3. **Verificação** = a tarefa concreta; pode ser automática ou **espontânea**.
   Para a mesma peça em várias visitas → **uma QC por visita + um Alerta**.
4. **Data de Controlo** (preenchida ao marcar o veredicto, **editável**) = filtro
   por data. **Calendário só nos Alertas**; data planeada nas verificações é
   melhoria HMD em curso.
5. **Alerta** = acompanhamento quando reprova; **vistas guardadas + kanban** =
   chegar ao que está pendente.

---

### Nota técnica (para a equipa Parâmetro, não para o cliente)
Modelos: `quality.point`, `quality.point.test_type` (instructions / passfail /
measure / picture / worksheet / spreadsheet + tipos MRP), `quality.check`
(`control_date` = data; `picture` = 1 foto, binário), `quality.alert` (+ stage/team).
Folha de trabalho: `quality_control_worksheet` adiciona `worksheet_template_id` ao
ponto/check; a folha é um **modelo dinâmico** (`worksheet_template_id.model_id.model`,
ex.: `x_quality_worksheet_...`) ligado via `x_quality_check_id`.

**Galeria (`pg_quality_gallery`):** atualmente lê só `quality.check.picture` (tipo
"Tirar Foto"). **Decisão HMD: as fotos passam a estar na folha de trabalho** → a
galeria tem de ler o(s) campo(s) de imagem da folha. **Bloqueado até o template da
folha estar definido** (preciso do nome técnico do modelo da folha e do(s) campo(s)
de imagem, ou de acesso à BD para introspeção). O smart button QC nas compras
(`pg_purchase_quality_button`) já está feito.
