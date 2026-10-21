---
assunto: Passagem do EVOSTONE — o que te espera
para: <preencher: endereço do Pedro>
---

Pedro,

Bem-vindo de volta. Segue a passagem do EVOSTONE, de 14 a 16 de setembro.

O resumo está aqui: **https://claude.ai/artifact/GruTo6tuMthZVFZESbXbYh**

Está tudo também no repositório, no `brodoo`. Faz `pull` antes de olhares para o
que quer que seja — são 25 commits, e sem eles não tens nem o `PG_CONTEXT`, nem
os emails ao cliente, nem os guiões.

**Duas coisas antes de tudo o resto.**

A primeira é o orçamento. Estão lançadas 35,75 h das 36, e o dia 16 ainda nem
entrou. A fase de certificação e go-live — tarefas 7044 a 7053, todas em
Backlog — está orçamentada em 30 h. **Não há como responder ao Sr. Rui sobre
datas sem decidires isto primeiro.** Ele pediu a estimativa a 08, 09 e 11 de
setembro, e foi-lhe dito que a resposta vinha contigo.

A segunda é que a certificação portuguesa não está no sistema. O `l10n_pt`
instalado é só plano de contas e impostos. O «Odoo PT+» da Exo Software, que o
cliente comprou a 11/09 e já faturou, não está no repositório nem instalado. A
tarefa 7395 é esse fio.

**A Maria Dias está à espera desde segunda às 21:36.**

Respondeu ao nosso email anotando-o linha a linha, na tarefa 7041. Escreveu «não
entendo nada do que escreveu» em dois pontos — e tem razão em quatro coisas,
contra o que lhe dissemos. A mais incómoda: dissemos-lhe que local de carga,
local de descarga e matrícula eram desenvolvimento a orçamentar. Dois deles são
obrigação legal (DL 147/2003, art. 4.º n.º 4), há um quarto que nem foi pedido,
e vêm todos no módulo que ela já pagou. Orçamentá-los seria cobrar outra vez.

Digo-to assim porque se responderes sem isto, repetes o erro com a tua
assinatura.

Há ainda a tarefa 7431 — «Maria Dias Apoio Artigos / Faturação», com pedido de
urgência do cliente — parada em Backlog com 0 h alocadas. É a sessão que
destrava o stock e os preços ao mesmo tempo.

**Três coisas que ficaram à espera de uma palavra:**

- Que nome deve ficar no registo de autorização da escrita dos impostos da
  P00002 e P00001. O guião está pronto e ensaiado, os totais não mudam.
- Quem mudou o método de custeio da categoria Mercadoria na terça às 07:51, e se
  foi deliberado. É reversível só enquanto houver 0 existências.
- O host de staging, que muda a cada publicação no Odoo.sh.

**O que fica entregue e provado em produção:** os documentos, o remetente do
correio, o site, a receção, o IBAN, e dois defeitos do módulo do parceiro
anterior que impediam imprimir faturas e dar entrada de material. Bateria de
validação a 21/21. Os guiões estão em `guioes/`, com um README.

**O que não está provado:** oito dos 22 documentos à medida — as etiquetas e
listagens de chapa — não são testáveis sem stock real. E a maior parte da
configuração foi aplicada diretamente em produção, sem ensaio em staging.

Qualquer coisa, diz.
