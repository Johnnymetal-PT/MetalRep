{
    'name': 'PG Sale by Square Meter',
    'version': '19.0.1.1.0',
    'author': 'Parametro Global',
    'category': 'Sales',
    'summary': 'Venda a metragem: comprimento e largura na linha, com a quantidade derivada da área.',
    'description': """
PG Sale by Square Meter
=======================

a) Objetivo de negócio
----------------------
Vender tecido e material cortado à medida. O vendedor introduz o comprimento e
a largura na linha da encomenda e o preço é calculado sobre a área real, não
sobre unidades.

Cobre a tarefa 6564 ("a quantidade em m² não passa corretamente para a fatura").

b) Pré-requisitos
-----------------
- Módulo standard `sale`.
- As colunas `comprimento`, `largura` e `area` já existem na base migrada da
  V17, com dados. Os nomes são mantidos de propósito — ver alínea (g).

c) Como funciona
----------------
- `area` é calculada e gravada a partir de `comprimento` × `largura`.
- `product_uom_qty` — a quantidade da linha — passa a **derivar da área**: o
  módulo acrescenta a área às dependências do cálculo standard da quantidade.
- A fatura não é tocada. O standard já copia a quantidade da encomenda para a
  fatura; corrigida a quantidade, a fatura fica correcta por consequência.

d) Passo a passo de utilização
------------------------------
1. Numa encomenda, escolher o artigo na linha.
2. Preencher o comprimento e a largura. A área e a quantidade actualizam-se.
3. Confirmar e faturar normalmente.

e) Exemplo prático
------------------
Tecido a 60,00 EUR/m², 2,0 m × 1,4 m. A área dá 2,8 e a quantidade da linha
fica 2,8; o subtotal é 168,00 EUR e a fatura sai com 2,8 de quantidade.

f) FAQ / Resolução de problemas
-------------------------------
- "Alterei a quantidade à mão e ela ficou":
  É intencional — o campo é editável. Volta a ser recalculada assim que o
  comprimento ou a largura mudarem.
- "Uma encomenda antiga tem a quantidade errada":
  Ver alínea (g): as linhas herdadas não são corrigidas automaticamente.

g) Pontos de atenção
--------------------
- **A correcção de fundo face à V17** é a quantidade passar a ser derivada em
  vez de escrita. Na V17 a área era copiada para a quantidade por um
  sincronismo que só corria no `create` e num `write` que tocasse nas
  dimensões. Qualquer outro caminho — importação, alteração em massa, API —
  deixava a quantidade desactualizada, e a fatura, que copia fielmente a
  quantidade da encomenda, saía errada. Em produção há **18 linhas** nesse
  estado, das quais 17 partilham o mesmo instante de alteração (um evento de
  massa de 18-05-2026). O caso mais recente, de 21-07-2026, foi faturado com
  quantidade 1 em vez de 2,8 m², numa fatura lançada.
- **As linhas herdadas não são corrigidas.** O `post_init_hook` apenas as lista
  no log. Reescrever a quantidade de uma linha com fatura lançada mexeria em
  documentos contabilísticos já emitidos; a decisão é caso a caso.
- **Nomes de campo sem prefixo `pg_`**, por excepção justificada: as colunas já
  existem na base migrada com dados em 64 linhas, e renomeá-las obrigaria a uma
  migração sem ganho.
- **Dimensões fora de escala são recusadas.** Comprimento ou largura acima do
  máximo definido em Vendas > Definições (20 m por omissão) dão erro, com a
  conversão para metros sugerida na mensagem. O limite é generoso de propósito:
  na produção, das 60 linhas com dimensões plausíveis a maior tem 5,4 m,
  enquanto as quatro fora de escala (267, 220, 220 e 80 m) são centímetros
  escritos como metros. A 0 desliga a validação.
- Face à V17 foram removidos: o override de `_compute_amount`, desnecessário
  agora que a quantidade está correcta e o cálculo standard a usa; e o override
  de `_convert_to_tax_base_line_dict`, método que **já não existe** em v19 (o
  cálculo de impostos foi reescrito) e que portanto era código morto.
    """,
    'depends': ['sale'],
    'data': [
        'views/sale_order_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
