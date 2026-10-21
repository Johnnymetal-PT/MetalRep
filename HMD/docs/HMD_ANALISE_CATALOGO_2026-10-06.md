# Análise ao catálogo — categorias, rotas e listas de materiais

- **Para:** Nina Hedderich (HMD)
- **De:** Parâmetro Global
- **Data:** 06/10/2026
- **Base:** produção HMD, leitura de 06/10/2026 (nada foi alterado)

---

## Em resumo

O catálogo tem **1682 artigos ativos** (8717 variantes). Só **234** têm lista de materiais, em **375 listas**: 287 de fabrico, 79 de subcontratação e 9 kits.

Há três pontos que explicam as dúvidas sobre rotas, listas de materiais e categorias:

1. **Um terço do catálogo está numa só categoria**, e a maior parte não são artigos acabados.
2. **Todos os artigos acabados herdam a rota «Reposição por pedido»**, incluindo os que lá estão por engano.
3. **Em 199 artigos, a rota e a lista de materiais não coincidem**: o Odoo faz uma coisa e a lista diz outra.

---

## 1. Categorias

| Categoria | Artigos | Variantes | O que é |
|---|---|---|---|
| 01 PRODUTOS ACABADOS | 961 | 7 354 | Mobiliário para vender |
| — Estantes, Prateleiras e armários | **541** | 1 535 | **Ver abaixo** |
| — Mesas, consolas e secretárias | 246 | 5 560 | |
| — Sofás e cadeirões | 89 | 108 | |
| — Cadeiras, bancos e poufs | 38 | 59 | |
| — Camas, Acessórios, sem subcategoria | 47 | 92 | |
| 02 COMPONENTES | 286 | 604 | Acabamento 37, Estofo 98, Metal 31, Tampos 65, sem subcategoria 55 |
| 04 TECIDOS | 114 | 337 | |
| 06 EMBALAGENS | 238 | 238 | |
| 05 MATERIAIS | 66 | 167 | |
| 07 SERVIÇOS, 99 diversos | 17 | 17 | |

### A categoria «Estantes, Prateleiras e armários» não contém estantes

São **541 artigos**, e **339 são só de compra** (nunca se vendem). A maioria (219) foi criada em julho de 2025. Pelos nomes, são estruturas, bases, aros, pés, tampos e aplicações (PLEASE 87, NEGRONI 32, TAMPO 24, LOLA 19…), e há até um item de leasing.

Estes 339 parecem pertencer a **02 COMPONENTES**, nas suas subcategorias.

### Porque é que isto importa: as rotas herdam-se

Uma rota posta numa categoria aplica-se a **todas as suas subcategorias** (é assim no Odoo). A categoria **01 PRODUTOS ACABADOS** tem a rota **«Reposição por pedido (sob demanda)»**, por isso tudo o que está debaixo dela a herda, incluindo os 339 componentes.

Na prática, isso significa que a necessidade desse componente gera uma compra ou uma produção própria, em vez de sair do stock. Se for o que querem, está certo. Se não, é a consequência de ter os componentes na categoria errada.

---

## 2. Rotas e listas de materiais

### As quatro situações

| O artigo é… | Lista de materiais | Rota no artigo | Rotas nos componentes |
|---|---|---|---|
| **Compra** — o fornecedor entrega o artigo completo | nenhuma | **Comprar** | — |
| **Subcontratação** — o fornecedor monta com componentes nossos | **Subcontratação**, com o fornecedor | **Comprar** | Se lhe enviamos o componente: «Reposição sob demanda para subcontratação». Se um fornecedor entrega a outro: «Envio direto sob demanda para subcontratação». Se o subcontratado compra por si: nenhuma |
| **Fabrico** — a HMD monta | **Fabrico** | **Fabrico** | **Comprar** |
| **Kit** — vende-se junto, sai separado | **Kit** | **nenhuma** (o kit não tem rota própria) | a rota de cada componente |

«Reposição por pedido» junta-se à de cima quando o artigo é feito ou comprado só por encomenda.

### Onde a rota e a lista não coincidem — 199 artigos

| | Situação | Artigos | O que acontece |
|---|---|---|---|
| **A** | Tem rota **Fabrico**, mas não tem lista de fabrico | **128** | Cada necessidade do artigo gera uma **ordem de fabrico vazia**, sem componentes e sem erro |
| **B** | Tem lista de **fabrico**, mas não tem rota Fabrico | **46** | A lista **nunca é usada**: o artigo é comprado, ou a venda falha por não haver rota |
| **C** | Tem lista de **subcontratação**, mas não tem rota Comprar | **23** | A venda não gera a encomenda ao subcontratado |
| **D** | É **kit**, mas tem rota Fabrico (DEDAL SIDE, DEWA CONSOLE) | **2** | Funciona, porque o kit se desfaz antes, mas contradiz a regra «um kit não tem rota» |

Alguns destes casos podem ser intencionais, por exemplo artigos ainda em desenvolvimento. A lista completa segue em anexo — **HMD_catalogo_rotas_vs_listas_2026-10-06_com_proposta.csv** — já pré-preenchida com a classificação que nos enviou a 28/09. Em 95 artigos vai sugerido o **tipo certo** e uma proposta de correção, e basta confirmar ou corrigir. Ficam em branco 104: 80 que não estão na sua lista, 23 que parecem componentes e 1 por decidir (Fabrico ou Kit).

### Outros pontos que se veem nos números

- **Embalagens:** 18 das 238 caixas têm rota de «Envio direto», o que faz o fornecedor enviá-las diretamente, por encomenda. A 18/09 combinámos que as caixas não deviam ter rota de subcontratação, porque o Sérgio as junta de duas em duas semanas. A confirmar.
- **Sem fornecedor:** 269 artigos compráveis não têm fornecedor, incluindo 51 dos 66 «05 MATERIAIS».
- **Duas listas ativas para o mesmo artigo:** 85 artigos têm mais de uma lista ativa. O Odoo escolhe só uma.
- **33 listas sem componentes.**

---

## 3. Proposta

1. **Mudar os 339 componentes de «Estantes» para as subcategorias de 02 COMPONENTES.** Preparamos a lista com a subcategoria sugerida; só precisamos que a confirme. Convém verificar antes que as contas e o método de custo das duas categorias são iguais, para a mudança não alterar valores.
2. **Rever os 199 artigos da lista em anexo.** Cruzámos a classificação que enviou a 28/09 (45 compra e subcontratação, 17 fabrico, 7 kit) com os artigos: 95 vão pré-preenchidos para confirmar, e só faltam os 104 em branco.
3. **Corrigir as rotas e as listas** conforme a tabela das quatro situações. Fazemos nós, depois da sua confirmação.
4. **Uma sessão de trabalho de 45 a 60 minutos** para decidir as caixas, os componentes dos subcontratados e os 8 PLEASE de três atributos.

*Este documento tem a leitura de 06/10/2026. Os artigos e as listas estão a mudar, por isso os números têm de ser vistos de novo antes de qualquer correção.*
