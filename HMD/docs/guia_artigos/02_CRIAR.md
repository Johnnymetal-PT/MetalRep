Criar um artigo leva dois minutos. O que cada campo faz depois — numa venda, numa compra, numa
ordem de fabrico ou no stock — é o que este capítulo explica.

**Onde:** **Vendas › Artigos › Artigos** ([abrir]({{base}}/odoo/action-367)), ou
**Compras › Artigos › Artigos** ([abrir]({{base}}/odoo/action-388)) → **Novo**.

> 📷 *Ecrã: formulário de artigo novo, separador Informação Geral.*

## Os campos mínimos

| Campo | Onde | O que desencadeia | Se ficar mal |
|---|---|---|---|
| **Nome** | topo | É por ele que toda a gente procura. | Ver a [regra de nomes]({{kb43}}). |
| **Vendas** / **Compras** | caixas por baixo do nome | Fazem o artigo aparecer nos orçamentos e nas encomendas a fornecedor. | Desmarcado, o artigo não aparece onde é preciso — e é aí que se cria um duplicado. |
| **Tipo de Artigo** | Informação Geral | **Bens** para tudo o que é físico; **Serviço** para aplicações, transporte, mão-de-obra; **Combo** não se usa na HMD. | Um serviço marcado como bem entra em stock. |
| **Rastrear inventário** | Informação Geral, ao lado do tipo | Liga o controlo de quantidades em armazém. | Sem ele, não há stock nem reservas para este artigo. Hoje está ligado em 659 artigos. |
| **Categoria do Artigo** | Informação Geral | Decide as contas, o método de custo e, em várias categorias, a rota. | Ver [CATEGORIAS DE PRODUTO]({{kb83}}). |
| **Preço de Venda** | Informação Geral | Preço de partida no orçamento. | — |
| **Custo** | Informação Geral | Valor do stock e base da margem. | **986 artigos compráveis estão com custo 0** — o valor em armazém e as margens desses artigos saem errados. |
| **Fornecedores** | separador **Compras** | Diz ao Odoo a quem comprar, a que preço e em quanto tempo. Se cada variante tem um custo diferente, a lista tem uma linha por variante, na coluna **Variante do Artigo** (ver abaixo). | Sem fornecedor, o Odoo **não gera a compra**: dá erro a pedir para completar a lista de fornecedores. Hoje há **269 artigos compráveis sem fornecedor**. |
| **Rotas** | separador **Inventário** | Diz como o artigo chega: comprado, fabricado, subcontratado ou enviado diretamente. | Ver abaixo. |

## Preço do fornecedor por variante

Cada variante pode ter o seu custo. No separador **Compras**, na lista de **Fornecedores**, a coluna
**Variante do Artigo** diz a que variante se aplica cada preço. Uma linha sem variante vale para todas.

Se a coluna não aparecer, ativa-se no seletor de colunas, no ícone à direita do cabeçalho da lista.

> 📷 *Ecrã: separador Compras de um artigo com a coluna «Variante do Artigo» visível.*

O **preço de venda** funciona de outra forma: o valor extra de cada opção é um valor fixo e só altera
o preço de venda. O custo de compra é o da lista de fornecedores.

## As rotas na HMD

No separador **Inventário**, em **Rotas**, podem escolher-se:

| Rota | Quando usar |
|---|---|
| **Comprar** | O artigo compra-se a um fornecedor. Precisa de **Fornecedores** preenchido. |
| **Fabrico** | O artigo faz-se a partir de uma **Lista de Materiais**. Sem lista, não há o que fabricar. |
| **Reposição por pedido (sob demanda)** | Cada venda gera a sua própria compra ou fabrico, em vez de sair do stock. Combina-se com **Comprar** ou **Fabrico**. |
| **Reposição sob demanda para subcontratação** / **Envio direto sob demanda para subcontratação** | O artigo é feito por um subcontratado, a quem se enviam os componentes. |
| **Envio Direto** | O fornecedor entrega diretamente ao cliente. |

**A categoria já traz rota.** A **Reposição por pedido (sob demanda)** vem herdada da categoria em
**01 PRODUTOS ACABADOS**, **01 / Estantes, Prateleiras e armários**, **02 COMPONENTES / Acabamento**,
**02 COMPONENTES / Tampos** e **04 TECIDOS**. Num artigo dessas categorias não é preciso marcá-la
outra vez — basta acrescentar **Comprar** ou **Fabrico**.

> 📷 *Ecrã: separador Inventário de um artigo com as rotas Comprar e Reposição por pedido.*

## Antes de guardar

- [ ] **Vendas** e/ou **Compras** marcados conforme o uso real.
- [ ] **Categoria** certa (é ela que traz contas e rota).
- [ ] Se é comprável: **Fornecedor** com preço, e **Custo** preenchido.
- [ ] Se é fabricado: a **Lista de Materiais** existe ou vai ser criada a seguir.
- [ ] Se tem acabamentos ou tampos: ver primeiro [3. ATRIBUTOS, VARIANTES E ACABAMENTOS]({{variantes}}).

## Em definição

- **Kits** (PLEASE, SERA, TATA) e artigos **subcontratados**: a forma de os montar está a ser
  fechada com a HMD e entra neste capítulo quando estiver decidida.
- **Referência Interna**: hoje 81% dos artigos não a têm. Se a HMD quiser passar a usá-la, a regra
  entra aqui.
