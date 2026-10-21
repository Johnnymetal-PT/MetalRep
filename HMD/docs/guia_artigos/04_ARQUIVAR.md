Arquivar um artigo é fácil e não dá erro nenhum. É precisamente esse o problema: o Odoo deixa
arquivar um componente que está numa lista de materiais ou numa ordem de fabrico aberta, e só se
dá por isso quando a peça não chega.

## O que acontece por trás

- **Arquivar** esconde o artigo das pesquisas e das sugestões de compra. Mas as **listas de
  materiais** e as **ordens de fabrico** que já o usavam continuam a apontar para ele.
- **Mudar os atributos de um componente** (acrescentar ou retirar um acabamento, passar a
  dinâmico) faz o Odoo **arquivar as variantes antigas e criar novas**. As listas e as ordens ficam
  com as antigas.
- Uma ordem de fabrico com um componente arquivado **reserva um artigo que ninguém vai comprar**,
  porque já não aparece nas pesquisas nem nas sugestões de compra.

**Na HMD, a 02/10/2026:** 80 linhas de listas de materiais apontam para componentes arquivados, e
há **27 movimentos em 23 ordens de fabrico abertas** a consumir componentes arquivados. Em
setembro corrigiram-se 35; os novos apareceram com alterações feitas depois.

## Antes de arquivar ou de mudar os atributos de um componente

1. **No artigo, ver o botão Usado em**, no topo do formulário. Mostra as listas de materiais onde o
   componente entra. Se o botão não aparece, o artigo não está em nenhuma lista.
2. **Ver as ordens de fabrico abertas:** **Manufatura › Operações › Ordens de Produção**
   ([abrir]({{base}}/odoo/action-623)), pesquisar por **Componente** com o nome do artigo, e deixar
   o filtro **Tarefas a realizar**.
3. **Ver o stock:** se há quantidades em armazém, decidir primeiro para onde vão.
4. **Ver vendas e compras em aberto** com o artigo.

> 📷 *Ecrã: formulário de um componente com o botão «Usado em».*
> 📷 *Ecrã: Ordens de Produção, pesquisa por Componente com o filtro Tarefas a realizar.*

## Depois de arquivar ou de mudar os atributos

1. **Em cada lista de materiais** encontrada no passo 1: trocar a linha para o artigo ou a variante
   que fica.
2. **Em cada ordem de fabrico aberta** do passo 2: trocar o componente na ordem. Se a ordem já
   estiver reservada, anular a reserva antes de trocar.
3. Confirmar no artigo novo que o botão **Usado em** mostra as mesmas listas.

## Desfazer

Um artigo arquivado volta com o filtro **Arquivados** → abrir → **Desarquivar**. As listas e as
ordens que apontavam para ele voltam a funcionar.

## Resumo

- [ ] **Usado em** visto.
- [ ] Ordens de fabrico abertas vistas.
- [ ] Stock decidido.
- [ ] Depois: listas e ordens trocadas para o artigo que fica.

Quando a mudança envolver muitos artigos de uma vez (uma família inteira), peçam-nos a auditoria
das listas de materiais antes e depois: apanha os casos que não se veem no ecrã.
