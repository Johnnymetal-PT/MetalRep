Um mesmo modelo — uma mesa SERA, um sofá BULL — vende-se com vários acabamentos, tampos ou
tecidos. O Odoo tem três formas de representar uma opção, e escolher a errada é o que fez a HMD
chegar a mais de 10 000 variantes.

## A regra de partida

**Um desenho diferente é um artigo diferente.** Um acabamento que não muda o produto é uma
**variante**, e não um artigo novo. É a regra que a HMD já segue desde setembro de 2026.

## A pergunta que decide

> **Quando esta opção muda, o que muda na folha de preços?**

| Se muda… | Então a opção é… | Exemplo |
|---|---|---|
| **só o preço** | um atributo que **não cria variantes** | Categoria do tecido (CAT I a V): muda o valor do tecido, não muda o que se compra. |
| **o que se compra ou fabrica** | um atributo que **cria variantes**, com uma linha na lista de materiais por valor | Acabamento: Carvalho Natural compra uma peça, Microcimento compra MDF mais a aplicação. |
| **o artigo todo, com processo próprio** | um **artigo separado** | HOOK e HOOK BRASS (fabricados com fornecedores diferentes); FROG WOOD e FROG MICROCIMENTO. |

## Criação de variantes

Em **Vendas › Configuração › Artigos › Atributos** ([abrir]({{base}}/odoo/action-179)), cada atributo
tem o campo **Criação de variantes**:

| Opção | O que faz | Quando usar |
|---|---|---|
| **Instantaneamente** | Cria todas as combinações logo que o atributo é posto no artigo. | Poucas opções, todas vendidas e com stock. |
| **Dinamicamente** | Só cria a variante quando é encomendada. | Muitas combinações possíveis, poucas vendidas — a maior parte dos artigos à medida. |
| **Nunca** | Não cria variantes; o valor escolhido fica escrito na linha da venda. | Opções que só mudam o preço, como a **Categoria do tecido**. |

**Exemplo na HMD:** o BULL DINING CHAIR tem 1 variante e a **Categoria do tecido** em **Nunca**. É o
padrão a seguir para estofos.

> 📷 *Ecrã: Atributos › Categoria do tecido, com Criação de variantes = Nunca.*

## Preço extra por opção

O **valor extra** de cada opção (em **Atributos e Variantes** do artigo → **Configurar**) é sempre um
**valor fixo em euros**, nunca uma percentagem. Um acréscimo em percentagem exigia desenvolvimento,
e a HMD decidiu não o fazer (agosto de 2026).

## Cuidados

- **Mudar os atributos de um artigo que é componente arquiva as variantes antigas.** As listas de
  materiais e as ordens de fabrico abertas continuam a apontar para as variantes arquivadas, sem
  aviso. Ver [4. ARQUIVAR SEM PARTIR NADA]({{arquivar}}) antes de mexer.
- **A ordem dos atributos conta para a grelha:** o primeiro atributo fica nas colunas. Ver
  [GRELHA DE VARIANTES]({{kb98}}).
- **Esconder uma variante no site:** o Odoo 18 só publica ao nível do artigo. Fica resolvido com a
  passagem para o Odoo 19.

## Em definição

- **Kits:** os PLEASE, SERA e TATA vão passar a kit (tampo e base como componentes). A forma
  final — e o que acontece aos tampos que hoje são atributo — entra aqui quando a modelação
  estiver fechada com a HMD.
- **Tampos como componente da lista de materiais**, em vez de atributo do artigo vendável.
