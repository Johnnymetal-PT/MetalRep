Quando se encomenda a um fornecedor um artigo com variantes (por exemplo, o SERA DINING D100, com 7
acabamentos e 16 tampos), o Odoo mostra uma **grelha**: uma tabela com todas as combinações, onde se
escrevem as quantidades nas células, tudo de uma vez. Cada célula preenchida gera uma linha na
encomenda.

**Nas compras não há nada a configurar:** a grelha aparece sempre, em todos os artigos com variantes.

## Como usar

1. **Compras › Encomendas › Notas de encomenda**, abrir ou criar a encomenda.
2. Em **Adicionar um artigo**, escrever o nome do **modelo** (por exemplo, `MIRA D900X420`), não o de
   uma variante.
3. Abre-se a janela **Selecione as variantes de produto**. Preencher as quantidades nas células e
   clicar em **Confirmar**.
4. Para corrigir depois, clicar no **lápis** ao lado do artigo, na linha (**Editar Configuração**). A
   grelha volta a abrir com as quantidades já lançadas.

> 📷 *Ecrã: a janela «Selecione as variantes de produto» com uma grelha de acabamentos.*

Se ao escrever o nome aparecer logo uma variante e não abrir a grelha, o artigo não tem atributos com
escolha: tem uma variante só e não há nada para escolher.

## Como se lê a grelha

- **Colunas:** os valores do **primeiro** atributo do artigo (a primeira linha no separador
  **Atributos e Variantes**).
- **Linhas:** todas as combinações dos restantes atributos.
- **Células sem campo:** combinações que não existem, por serem variantes arquivadas ou exclusões
  definidas no atributo. Não é erro.

A ordem dos atributos conta. Num artigo com `Finish (8) × Tampo (13)` a grelha tem 8 colunas e 13
linhas. Se o Tampo estiver em primeiro, ficam 13 colunas e 8 linhas, o que é mais largo e mais difícil
de ler. Para mudar a ordem, no separador **Atributos e Variantes**, arrastar a linha do atributo pela
pega à esquerda. Em primeiro lugar, o atributo com menos valores (normalmente o acabamento).

## Casos particulares

- **Atributos que não criam variantes** (por exemplo, a **Categoria do tecido**, com **Criação de
  variantes = Nunca**): aparecem na grelha como os outros. O valor escolhido fica escrito na descrição
  da linha e não se cria uma variante nova.
- **Atributos dinâmicos** (**Criação de variantes = Dinamicamente**, por exemplo, o Puxador): a grelha
  mostra todas as combinações possíveis. A variante só é criada quando se confirma a quantidade.
- **Poucas variantes na lista não quer dizer grelha pequena:** a grelha é feita a partir dos valores
  dos atributos, e não das variantes que já existem.

## Preço do fornecedor por variante

Cada variante pode ter o seu custo. No separador **Compras** do artigo, na lista de **Fornecedores**, a
coluna **Variante do Artigo** diz a que variante se aplica cada preço. Ver
[2. CRIAR UM ARTIGO]({{criar}}).

## E nas vendas?

Na HMD, as vendas usam o **configurador de produto**: escolhe-se uma combinação de cada vez, num
assistente. Foi a opção escolhida em outubro de 2026, porque raramente se introduzem quantidades em
massa num orçamento.

Existe, por artigo, a alternativa **Entrada de grade no pedido** (**Atributos e Variantes › Seleção
de variante de venda**), que mostra a mesma grelha nos orçamentos. Não está em uso. Se um dia fizer
sentido para um artigo, é só mudar esse campo, e pode-se voltar atrás quando se quiser, sem afetar
preços, variantes nem documentos já feitos.

## Quando pedir ajuda

- A grelha abre com centenas de linhas: o artigo provavelmente tem atributos a mais.
- A grelha mostra combinações que não existem: falta uma exclusão no atributo.
- A grelha não abre numa encomenda a fornecedor, num artigo com variantes: não devia acontecer.
