# Circuito de produção por artigo e estado de cada encomenda

- **Tarefa:** #7789
- **Para:** reunião geral de 15/10/2026
- **Data:** 09/10/2026
- **Versão:** 1.0 (rascunho para integrar no guião)
- **Base:** produção HMD, leitura de 09/10/2026 (nada foi alterado)

---

## 1. O que a HMD pediu

Analisar os artigos que já existem, perceber o circuito para produzir cada um (por exemplo, se é preciso encomendar componentes a fornecedores) e criar um projeto com as etapas de produção. O objetivo é a HMD ter um panorama do estado de cada encomenda, para saber responder quando o cliente pergunta.

## 2. Onde estamos hoje

| O que medimos | Valor | O que isto diz |
|---|---|---|
| Ordens de produção abertas | 86 (79 confirmadas, 6 em rascunho, 1 em curso) | Só uma está marcada como iniciada. O arranque da produção não está a ser registado no Odoo. |
| Ordens ligadas à venda de origem | 76 de 86 | O caminho venda → produção funciona na maioria dos casos. |
| Vendas confirmadas desde janeiro com projeto | 50 de 63 | Quase todas as encomendas têm um projeto. |
| Ordens abertas ligadas ao projeto | 3 de 86 | 65 das ordens pertencem a vendas que têm projeto, mas o projeto não as mostra. |
| Tarefas de projeto criadas desde agosto | 47, em 6 projetos; 46 sem prazo | As etapas dos projetos não estão a ser usadas para acompanhar a produção. |
| Listas de materiais com operações / ordens de trabalho | 0 / 0 | O Odoo não conhece etapas dentro do fabrico. |

**Em resumo:** a informação para saber o estado de uma encomenda existe (ordens de produção, compras, receções), mas está dispersa por vários documentos e o projeto não a mostra. As etapas que se desenhariam num projeto não têm hoje quem as mova.

## 3. O circuito por tipo de artigo

Cada artigo cai num de quatro circuitos. É a lista de materiais e as rotas do artigo que decidem, e é isso que o Odoo usa quando a venda é confirmada.

| Tipo | Lista de materiais | O que acontece quando a venda é confirmada | Marcos que se acompanham |
|---|---|---|---|
| **Compra** | nenhuma | Pedido de cotação ao fornecedor, que entrega o artigo completo | Encomendado → recebido → entregue ao cliente |
| **Subcontratação** | de subcontratação, com o fornecedor | Compra ao subcontratado; os componentes seguem para ele (reposição, se a HMD os envia; envio direto, se um fornecedor os entrega) | Componentes entregues ao subcontratado → artigo recebido → controlo de qualidade → entregue |
| **Fabrico** | de fabrico | Ordem de produção na HMD; os componentes são comprados | Componentes recebidos → em produção → controlo de qualidade → pronto → entregue |
| **Kit** | de kit | Desfaz-se nos componentes; cada um segue o seu circuito | O estado do kit é o do componente mais atrasado |

## 4. Três famílias para desenhar

Propomos uma família de cada circuito, escolhidas por já terem ordens abertas, para o desenho poder ser confirmado em encomendas reais. A escolha final é da Nina.

| Família | Tipo (lista da Nina, 28/09) | O que vemos na produção | Ordens abertas | A decidir |
|---|---|---|---|---|
| **LOLA** | Subcontratação | 6 listas de subcontratação e 2 subcontratados com circuitos diferentes (um entrega as mesas completas à HMD; o outro recebe o tampo em MDF) | 11 | LOLA SMALL sem decisão de rota; LOLA STONE com a lista vazia |
| **ISAC** | Fabrico | Circuito misto: casco (compra), estofo (subcontratado, com tecido por reposição), couro (compra) e caixa | 2 | Existem 3 listas iguais, duas delas de encomendas concretas |
| **SERA** | Kit | As listas atuais são de fabrico (pé, tampo, chapa de suporte, caixa), não de kit | 6 | Kit ou fabrico? É a mesma dúvida da modelação de artigos (#7492) |

Alternativas se a Nina preferir: BULL POUF (9 ordens, subcontratado PVM) ou DEWA (kit).

Para cada família, o desenho final é uma ficha de uma página, a preencher com a Nina:

| Passo | Quem faz | O que o Odoo cria | Marco registado | Quem o regista |
|---|---|---|---|---|
| | | | | |

## 5. Como acompanhar o estado de cada encomenda

O princípio é que o estado **lê-se** do que o Odoo já sabe, em vez de ser escrito à mão por alguém. Etapas movidas à mão não se mantêm: foi o que aconteceu nos projetos até agora.

**Opção A: configuração standard (proposta para começar).**
Um projeto por encomenda, como já existe, mas com as ordens de produção e as compras ligadas a ele. O projeto passa a mostrar as ordens e as compras da encomenda e o estado de cada uma. Para isso:

1. O projeto tem de estar na venda **antes de a confirmar**. Nesse caso o Odoo 18 passa-o às ordens de produção. Hoje isso não acontece (ver ponto 7).
2. As 65 ordens abertas já existentes são ligadas ao seu projeto numa atualização única de dados.
3. As etapas do projeto passam a ser poucas e iguais para todas as encomendas, e só para marcos que não vêm de outro documento (por exemplo, desenho aprovado ou expedição). Quais, decide a HMD.

Cobertura: **parcial**. Mostra as ordens e as compras de cada encomenda, mas não dá um indicador único do estado da encomenda.

**Opção B: indicador de estado por encomenda (customização leve).**
A opção A mais um estado calculado, a partir das ordens, compras, receções e controlo de qualidade, visível na venda e no projeto. Só faz sentido decidir depois de ver a opção A a funcionar nas três famílias. O esforço estima-se nessa altura.

**Recomendação:** começar pela opção A nas três famílias, com encomendas reais, e levar a decisão sobre a opção B à reunião seguinte.

## 6. Âmbito

**Incluído nesta fase**
- Ficha de circuito das três famílias piloto.
- Projeto por encomenda com ordens de produção e compras ligadas (opção A).
- Etapas mínimas e comuns do projeto.
- Acompanhamento do piloto em encomendas reais.

**Fora desta fase**
- Etapas dentro do fabrico (ordens de trabalho e centros de trabalho): hoje nenhuma lista tem operações, e registá-las é um trabalho à parte.
- Gestão de versões de listas de materiais (PLM): decidido a 07/10 que não é necessário agora.
- Artigos feitos à medida: tratados na tarefa #7787.
- Uma tarefa por linha de venda: a HMD decidiu não o fazer.

## 7. Pontos por validar

- [ ] Porque é que as ordens não herdam o projeto da venda. O Odoo só o faz se o projeto estiver na venda no momento da confirmação; na HMD o projeto parece ser ligado depois. Confirmar a sequência com a HMD.
- [ ] As três famílias piloto, com a Nina. Em particular SERA: kit ou fabrico.
- [ ] Que marcos a HMD quer ver no projeto e quem os regista.
- [ ] Se a HMD quer passar a marcar as ordens como iniciadas, e quem o faz.
- [ ] Quem, na HMD, responde ao cliente sobre o estado e onde o vai consultar.

## Base da análise

- Produção HMD (Odoo 18 Enterprise), leitura de 09/10/2026: ordens de produção, listas de materiais, vendas e tarefas de projeto.
- Análise ao catálogo de 06/10/2026 (quatro circuitos e a sua relação com rotas e listas) e mapa de subcontratação da tarefa #7428.
- Odoo 18.0: módulos `project_mrp`, `project_mrp_sale` e `sale_project` (a ordem de produção herda o projeto da venda na confirmação).
