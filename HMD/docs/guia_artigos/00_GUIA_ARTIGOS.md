Este guia é o ponto de partida para quem cria ou altera artigos no Odoo da HMD. Segue a ordem
em que as coisas acontecem no dia a dia: procurar, criar, configurar variantes, encomendar e,
um dia, arquivar.

Cada capítulo é curto e pode ser lido sozinho. Os capítulos que já existiam no Conhecimento
estão ligados aqui e não foram reescritos.

## O percurso de um artigo

| Passo | Capítulo |
|---|---|
| 1. Antes de criar: o artigo já existe? | [1. PROCURAR ANTES DE CRIAR]({{procurar}}) |
| 2. Dar o nome certo | [CRIAÇÃO DE PRODUTOS]({{kb43}}) — a regra de nomes da HMD |
| 3. Preencher o artigo | [2. CRIAR UM ARTIGO — CAMPOS MÍNIMOS]({{criar}}) |
| 4. Escolher a categoria | [CATEGORIAS DE PRODUTO]({{kb83}}) |
| 5. Acabamentos, tampos, tecidos | [3. ATRIBUTOS, VARIANTES E ACABAMENTOS]({{variantes}}) |
| 6. Imagens | [COLOCAR IMAGENS NOS ARTIGOS]({{kb44}}) |
| 7. Encomendar várias variantes de uma vez, nas compras | [GRELHA DE VARIANTES NAS COMPRAS]({{kb98}}) |
| 8. Retirar um artigo ou mudar um componente | [4. ARQUIVAR SEM PARTIR NADA]({{arquivar}}) |

## As cinco regras para levar daqui

1. **Procurar antes de criar.** Os 70 artigos duplicados encontrados em setembro não vieram de
   importações. Foram criados à mão, muitas vezes duas vezes no mesmo dia pela mesma pessoa.
2. **Um artigo serve para comprar e para vender.** Se já existe só para compras e passa a
   vender-se, marca-se **Vendas** no mesmo artigo. Não se cria outro.
3. **Um desenho diferente é um artigo diferente. Um acabamento que não muda o produto é uma variante.**
   E se uma opção só muda o preço (por exemplo, a categoria do tecido), é um atributo que **não cria variantes**.
4. **Sem fornecedor e sem custo, o Odoo não compra nem calcula bem.** O separador **Compras** e o
   campo **Custo** não são opcionais num artigo comprável.
5. **Arquivar ou mudar os atributos de um componente parte as listas de materiais em silêncio.**
   Antes, confirmar onde é usado. Depois, trocar nas listas e nas ordens abertas.

## Em definição

Há partes deste guia que dependem de decisões ainda em curso com a HMD e ficam assinaladas nos
capítulos:

- **Kits** (PLEASE, SERA, TATA) e **tampos como componente** — da tarefa de modelação dos artigos.
- **Quem cria artigos e a partir de onde** — a sugestão do Natalino de deixar de criar artigos a
  partir das compras. A grelha de variantes já não é um fator (fica nas compras e as vendas usam o
  configurador), por isso a decisão pode ser tomada.
- **Rotas e listas de materiais** (compra, subcontratação, fabrico ou kit) — capítulo a acrescentar
  quando a modelação dos artigos estiver fechada com a HMD.
- **Subcontratação** — do desenho dos fluxos de inventário.
- **Referência Interna** — se a HMD a quer usar, e com que formato.

*Guia escrito pela Parâmetro Global a 02/10/2026, com a configuração e os números da vossa base de
dados nessa data. Os ecrãs serão acrescentados; até lá, cada passo indica o caminho exato no menu.*
