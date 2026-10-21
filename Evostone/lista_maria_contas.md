---
assunto: EVOSTONE — proposta de contas: seis categorias de artigo e nove elementos de imobilizado
para: Maria Dias — endereço a confirmar
---

Boa tarde Maria,

Segue a proposta de contas que anunciámos. Está construída sobre o plano SNC que o Odoo instala, e o que lhe pedimos é confirmação — ou correcção — e não que a construa de raiz.

**Categorias de artigo**

Uma nota que simplifica muito isto. No plano moçambicano, a distinção entre nacional e estrangeiro, e o regime de IVA, estavam **dentro do próprio código de conta**: havia uma conta «Mercadoria MN IVA 16%» e outra «Mercadorias ME Isento». No SNC essa distinção não é feita pela conta — é feita pela **posição fiscal** e pela taxa. Por isso as seis categorias resolvem-se com duas contas de compra e duas de venda.

| Categoria | Conta moçambicana actual | Compra (SNC) | Venda (SNC) |
|---|---|---|---|
| Mercadoria Nacional | 21111 Mercadoria MN IVA 16% | **311** Mercadorias | **711** Mercadorias |
| Mercadoria Externo | 21123 Mercadorias ME Isento | **311** Mercadorias | **711** Mercadorias |
| Matéria-prima Nacional | 212111 Matérias primas MN IVA 16% | **312** Matérias-primas, subsidiárias e de consumo | **712** Produtos acabados e intermédios |
| Matéria-prima Externo | 212123 Matérias primas ME Isento | **312** | **712** |
| Matérias auxiliares Nacional | 212211 Matérias auxiliares MN IVA 16% | **312** | **712** |
| Matérias auxiliares Externo | 212222 Matérias auxiliares ME N/Ded | **312** | **712** |

As contas **311** e **711** são as que a própria localização portuguesa do Odoo assume por omissão para a empresa. Isso significa que as duas categorias de mercadoria não precisam de conta própria: herdam-na. Só as quatro de matérias precisam de indicação, e todas com o mesmo par.

Se preferir separar matérias-primas de matérias subsidiárias em contas distintas, diga-nos — o SNC agrega-as na 312, mas podem criar-se subcontas.

**Elementos de imobilizado**

Aqui há duas coisas a decidir, e a primeira é mais importante do que a segunda.

*Primeira: os valores.* Os montantes de aquisição vieram do sistema moçambicano e estão hoje apresentados em euros sem terem sido convertidos. Somados dão 3 701 279,94, o que a uma taxa da ordem de 70 MZN/EUR corresponderia a cerca de 52 900 euros. Precisamos do valor de aquisição correcto, em euros, de cada elemento — ou da taxa que devemos aplicar, se preferir que a conversão seja feita por nós.

*Segunda: a classificação.* A proposta abaixo é nossa e as três últimas linhas são discutíveis.

| # | Descrição | Valor actual | Aquisição | Imobilizado | Depreciação acumulada | Gasto de depreciação |
|---|---|---|---|---|---|---|
| 7 | Empilhadeira | 3 248 000,00 | 2023-03-01 | **433** Equipamento básico | **4383** | **6423** |
| 66 | Impressora de etiquetas | 218 391,42 | 2024-11-30 | **435** Equipamento administrativo | **4385** | **6425** |
| 5 | Computador | 37 300,00 | 2022-01-01 | **435** | **4385** | **6425** |
| 68 | Portátil | 22 000,00 | 2024-07-14 | **435** | **4385** | **6425** |
| 3 | Contador de notas | 10 800,00 | 2021-01-01 | **435** | **4385** | **6425** |
| 2 | Topzstone azul 30mm polido/mesa | 91 282,50 | 2020-09-01 | **437** Outros ativos fixos tangíveis | **4387** | **6427** |
| 1 | Travertino creme resina/tampo de mesa | 39 584,33 | 2020-09-01 | **437** | **4387** | **6427** |
| 4 | Mesas de granito | 25 921,69 | 2021-03-01 | **437** | **4387** | **6427** |
| 6 | Expositor | 8 000,00 | 2023-01-01 | **437** | **4387** | **6427** |

Dois pontos onde a nossa proposta é discutível, e onde seguimos o que nos disser:

- A **empilhadeira** foi classificada em equipamento básico (433) e não em equipamento de transporte (434), por não ser um veículo de estrada. Se a vossa prática for a outra, mudamos.
- As **peças de pedra e o expositor** parecem ser material de exposição em showroom. Classificámo-los em outros ativos fixos tangíveis (437). Se forem tratados como equipamento administrativo, ou se algum deles não deve estar em imobilizado, diga-nos.

Nenhum dos nove tem depreciações registadas, pelo que qualquer correcção de valor ou de classificação é feita sem reprocessamentos.

Fico ao dispor.
