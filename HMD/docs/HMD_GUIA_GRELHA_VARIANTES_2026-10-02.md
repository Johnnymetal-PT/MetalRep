# Guia — Grelha de variantes nas compras e nas vendas

- **Para:** Natalino Castro, Sérgio Pinto e Nina Hedderich (HMD)
- **De:** Parâmetro Global
- **Data:** 02/10/2026
- **Onde se aplica:** Odoo de produção
- **Faz parte de:** guia de criação e manutenção de artigos (#7494)

---

## Para que serve

Um artigo com variantes (ex.: SERA DINING D100, com 7 acabamentos e 16 tampos) pode ser
encomendado de duas formas:

- **Configurador** — escolhe-se uma combinação de cada vez, num assistente. Três acabamentos
  diferentes são três passagens pelo assistente.
- **Grelha** — abre-se uma tabela com todas as combinações e escrevem-se as quantidades nas
  células, tudo de uma vez. O Odoo cria uma linha por cada célula preenchida.

## Nas encomendas a fornecedor: já está sempre ligada

**Nas compras não há nada a configurar.** Sempre que se escolhe um artigo com variantes numa
encomenda a fornecedor, o Odoo abre a grelha. A opção do artigo descrita mais abaixo só se
aplica às vendas.

1. **Compras › Encomendas › Notas de encomenda**, abrir ou criar a encomenda.
2. Em **Adicionar um artigo**, escrever o nome do **modelo** (ex.: `MIRA D900X420`), não o
   de uma variante.
3. Abre-se a janela **Selecione as variantes de produto**. Preencher as quantidades nas células
   e clicar em **Confirmar**.
4. Para corrigir depois, clicar no **lápis** ao lado do produto, na linha (**Editar
   Configuração**). A grelha volta a abrir com as quantidades já lançadas.

Se ao escrever o nome aparecer logo a variante e não abrir a grelha, o artigo não tem atributos
com escolha: tem uma variante só e não há nada para escolher.

## Nos orçamentos: depende do artigo

Nas vendas, cada artigo diz se abre o configurador ou a grelha.

### Ver ou mudar o modo de um artigo

1. **Vendas › Artigos › Artigos**, abrir o artigo.
2. Separador **Atributos e Variantes**.
3. Em **Seleção de variante de venda**, escolher:
   - **Configurador de produto** — o assistente, uma combinação de cada vez;
   - **Entrada de grade no pedido** — a grelha.
4. Guardar.

Se a secção **Seleção de variante de venda** não aparecer, o artigo não tem atributos com
escolha, e a opção não se aplica.

A mudança é só no modo de introdução das linhas. Não altera preços, variantes, existências nem
documentos já feitos, e pode-se voltar atrás a qualquer momento.

### Usar a grelha num orçamento

1. No orçamento, em **Adicionar um artigo**, escrever o nome do modelo.
2. Preencher as quantidades nas células e **Confirmar**.
3. Para corrigir, voltar a escolher o mesmo artigo noutra linha, ou abrir a configuração da linha:
   a grelha mostra o que já está lançado.

## Como se lê a grelha

- **Colunas** — os valores do **primeiro** atributo do artigo (a primeira linha no separador
  **Atributos e Variantes**).
- **Linhas** — todas as combinações dos restantes atributos.
- **Células sem campo** — combinações que não existem: variantes arquivadas ou exclusões
  definidas no atributo. Não é erro, é o Odoo a impedir uma combinação que não se vende.

Por isso a ordem dos atributos conta. Num artigo com `Finish (8) × Tampo (13)` a grelha tem 8
colunas e 13 linhas. Se o Tampo estiver em primeiro, ficam 13 colunas e 8 linhas, o que é mais
largo e mais difícil de ler. Para mudar a ordem, no separador **Atributos e Variantes**,
arrastar a linha do atributo pela pega à esquerda.

**Regra prática:** em primeiro lugar, o atributo com menos valores ou o que se escolhe primeiro
(normalmente o acabamento).

## Em que artigos vale a pena

| Artigo | Modo nas vendas |
|---|---|
| Dois atributos com escolha, até cerca de 20 linhas na grelha (ex.: SERA, TATA, DEDAL, MOON) | **Grelha** |
| Um só atributo com escolha (ex.: PUDIM ARMCHAIR, só Categoria do tecido) | Grelha ou configurador — a grelha fica com uma linha só, também serve |
| Três atributos com escolha (ex.: PLEASE ROUND, Finish × Rim × Tampo) | **Configurador**, por agora — a grelha teria mais de 100 linhas |
| Sem atributos com escolha | Não se aplica |

## Casos particulares

- **Atributos que não criam variantes** (ex.: **Categoria do tecido**, com **Criação de variantes
  = Nunca**). Aparecem na grelha como os outros. O valor escolhido fica escrito na descrição da
  linha e não se cria uma variante nova.
- **Atributos dinâmicos** (**Criação de variantes = Dinamicamente**, ex.: Puxador). A grelha
  mostra todas as combinações possíveis, mesmo as que ainda não foram encomendadas. A variante
  é criada quando se confirma a quantidade.
- **Um artigo com poucas variantes na lista de Variantes não tem por isso uma grelha pequena.** A
  grelha é feita a partir dos valores dos atributos, não das variantes que já existem.
- **Impressão.** O PDF do orçamento ou da encomenda mostra as quantidades também em grelha, para
  os artigos que a usam.

## Quando pedir ajuda

- A grelha abre com centenas de linhas — o artigo provavelmente devia estar no configurador, ou os
  atributos precisam de ser revistos.
- A grelha mostra combinações que não existem — falta uma exclusão no atributo.
- A grelha não abre numa encomenda a fornecedor num artigo que tem variantes — isto não devia
  acontecer, porque nas compras a grelha está sempre ligada.
