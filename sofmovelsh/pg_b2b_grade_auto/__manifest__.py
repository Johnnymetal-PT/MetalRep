{
    'name': 'PG B2B Grade Auto',
    'version': '19.0.1.0.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Atribui automaticamente o escalão do cliente a partir da faturação; o desconto vem da lista de preços do escalão.',
    'description': """
PG B2B Grade Auto
=================

a) Objetivo de negócio
----------------------
O cliente profissional deve subir de escalão à medida que a faturação cresce, e
o desconto do escalão deve aplicar-se sozinho. A tabela de escalões e as
percentagens têm de ser geridas pela Sofmovel, sem intervenção de programação.

Este módulo acrescenta **apenas** o cálculo automático. Tudo o resto — a tabela
de escalões, a ligação de cada escalão a uma lista de preços, a atribuição ao
cliente e a aplicação do desconto ao preço — é o módulo standard `partnership`.

b) Pré-requisitos
-----------------
- Módulos standard `partnership` (traz o `crm` e o `sale`) e `account`.
- **A funcionalidade "Listas de preços" tem de estar ligada** em Vendas >
  Definições. Sem ela o Odoo devolve lista vazia à entrada
  (`product/models/product_pricelist.py`, `_get_partner_pricelist_multi`) e nada
  funciona — sem dar erro.
- Cada escalão automático precisa de ter uma lista de preços associada; caso
  contrário o cliente muda de escalão e o desconto não muda.

c) Como funciona
----------------
- `models/res_partner_grade.py`: acrescenta ao escalão `pg_auto_assign` (entra
  ou não no cálculo) e `pg_min_invoiced` (faturação a partir da qual se aplica).
- `models/res_partner.py`: `pg_grade_auto` marca quem adere; `pg_invoiced_total`
  e `pg_grade_computed_on` guardam o resultado do último cálculo.
  `_pg_recompute_grades` soma a faturação e escreve o escalão; escrever o
  escalão faz o `partnership` aplicar a lista de preços.
- `data/ir_cron.xml`: agendador diário, **desligado de origem**.

Medida usada: faturas de cliente **lançadas** (`out_invoice` e `out_refund`,
`state = posted`), valor **sem impostos**, em moeda da empresa, com as notas de
crédito a subtrair (`amount_untaxed_signed`). A soma é por **entidade
comercial**, para que faturas emitidas a contactos da empresa contem para a
empresa.

d) Passo a passo de utilização
------------------------------
1. Ligar as listas de preços em Vendas > Definições.
2. Criar uma lista de preços por escalão, cada uma com uma regra de desconto
   sobre todos os artigos.
3. Em CRM > Configuração > (nome dado aos parceiros) > Levels: em cada escalão,
   escolher a lista de preços, ligar "Atribuir automaticamente" e preencher a
   faturação mínima.
4. Nos clientes que aderem ao programa, ligar "Escalão automático".
5. Correr uma vez à mão pela acção "B2B: recalcular escalão por faturação" sobre
   uma selecção pequena, e confirmar o resultado.
6. Só depois activar o agendador.

e) Exemplo prático
------------------
Escalões a 0, 1 500, 5 000 e 15 000, ligados a listas de -10%, -15%, -20% e
-25%. Um cliente com 6 200 EUR facturados fica no escalão dos 5 000 e passa a
comprar com -20%: a lista aparece-lhe na ficha e o preço sai já descontado no
orçamento seguinte. Quando passar os 15 000 sobe sozinho no cálculo seguinte.

f) FAQ / Resolução de problemas
-------------------------------
- "Mudei o escalão e o preço não mudou":
  Confirmar que o escalão tem lista de preços e que a funcionalidade de listas
  está ligada.
- "O cálculo não mexeu em ninguém":
  Ou nenhum escalão tem "Atribuir automaticamente", ou nenhum cliente tem
  "Escalão automático". Ambos são desligados de origem, de propósito.
- "Ninguém desce de escalão":
  É o comportamento por omissão (histórico completo). Ver alínea (g).
- "Um cliente tinha uma lista negociada e perdeu-a":
  Escrever o escalão sobrepõe a lista. Ver alínea (g).

g) Pontos de atenção
--------------------
- **Nada disto está em código.** Faturação mínima no próprio escalão;
  percentagem na lista de preços; base, janela, ligar/desligar e periodicidade
  em CRM > Definições. Acrescentar ou retirar um escalão é criar ou apagar um
  registo.
- **O agendamento não é reimplementado.** Os campos das definições são um
  espelho do `ir.cron` standard: a periodicidade traduz-se para
  `interval_number`/`interval_type` e o próximo apuramento para `nextcall`.
  Quem preferir continua a poder editar a acção planeada directamente, e o
  ecrã de definições reflecte o que lá estiver. Uma combinação escolhida à mão
  que não corresponda a nenhuma das periodicidades da lista aparece em branco,
  sem ser alterada.
- **O dia do ciclo vem do "próximo apuramento".** O Odoo soma o intervalo ao
  `nextcall`, o que preserva o dia do mês. Para apurar no dia 1, basta que essa
  data caia num dia 1.
- **Janela de tempo.** Está a `0`, o que soma o histórico completo e reproduz a
  V17. Com histórico completo **ninguém desce de escalão**, porque um acumulado
  nunca diminui — e um apuramento periódico só pode promover. A `12` passa a
  janela móvel de um ano e o escalão acompanha o volume nos dois sentidos. A
  periodicidade e a janela decidem-se em conjunto.
- **Base do cálculo.** Por omissão faturas emitidas. A opção "encomendas
  confirmadas" reproduz o critério da V17, que contava a venda antes de
  facturar. Nessa opção o valor vem na moeda da encomenda e não é convertido —
  exacto em empresa de moeda única, que é o caso.
- **Faturação, não encomendas.** A V17 somava encomendas confirmadas, o que
  contava vendas ainda não faturadas. Esta é uma mudança deliberada de critério,
  a confirmar com o cliente.
- **Listas negociadas à mão.** Se um cliente aderente tiver uma lista própria
  diferente da do escalão, o cálculo sobrepõe-na. Para casos negociados, deixar
  "Escalão automático" desligado, ou usar um escalão sem "Atribuir
  automaticamente".
- **Na descida para sem escalão**, o módulo retira a lista que o escalão
  anterior tinha posto — e só essa. Uma lista atribuída à mão não é tocada.
- O agendador está **desligado de origem**: com a tabela por preencher, uma
  execução mudaria o escalão de toda a base de uma vez.
- Só entidades comerciais são avaliadas; contactos filhos são ignorados e o
  facto fica no log.
- Face ao `pg_b2b_discounts` da V17, desaparecem: as listas "Combined" por
  cliente, as percentagens no código, o desconto escrito na linha da encomenda
  e o campo `x_studio_fidelizado` (substituído por `pg_grade_auto`).
    """,
    'depends': ['partnership', 'account'],
    'data': [
        'data/ir_cron.xml',
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
}
