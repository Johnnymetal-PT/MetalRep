{
    'name': 'PG Tabela Dinamica de Aproveitamento de Tecido em MO',
    'version': '18.0.1.0.0',
    'sequence': 1,
    'summary': 'Aplica a quantidade de tecido por unidade conforme tabela 1..10 do produto.',
    'description': """
PG Tabela Dinamica de Aproveitamento de Tecido em MO (HMD)
==========================================================

a) Objetivo de negocio
----------------------
Na producao HMD, o consumo de tecido por unidade NAO e linear: ao
produzir 1 unidade consome-se mais tecido do que ao produzir 5 (por
aproveitamento). A consultora levou a tabela "Aproveitamento de Tecido"
(10 colunas - de 1 a 10 unidades) para o backoffice do produto. Este
modulo le essa tabela ao criar uma Ordem de Producao e ajusta
automaticamente a quantidade de "Tecido de Fornecedor" no movimento de
materia-prima.

NOTA SOBRE O NOME: os campos chamam-se `price_*` mas guardam QUANTIDADES
de tecido (m/unidade), nao precos. O nome do modulo "Price Table" e
herdado de um spike inicial - na pratica e uma "consumption table".
Renomear envolveria migracao de dados; manter como esta e documentar.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `mrp` e `stock` (dependencia declarada).
- IMPORTANTE: tem de existir um produto com nome EXATO
  "Tecido de Fornecedor" usado nas BOMs do produto que se manufactura.
  O override usa o nome literal para deteccao - se o produto for
  renomeado, o override deixa de aplicar.
- A tabela de aproveitamento (`price_1` a `price_10`) deve estar
  preenchida no produto template. Linhas vazias devolvem 0.

c) Como funciona (tecnico)
--------------------------
1. `product.template` (`models/product_template.py`): adiciona 10
   campos Float (`price_1` ... `price_10`) renderizados como tabela
   HTML horizontal na aba "Aproveitamento de Tecido".

2. `mrp.production.create` override (`models/mrp_production.py`):
   - Para cada MO criada, obtem `product_qty` e o `product.template`.
   - Le `consumption_table = [price_1, ..., price_10]`.
   - Escolhe o valor da coluna `qty - 1` (com clamp ao maximo 10).
   - Aplica o resultado em `vals['product_uom_qty']`. NOTA: esta linha
     existe mas o campo `product_uom_qty` nao e standard em
     `mrp.production` (e em `stock.move`). Em pratica, o efeito util
     vem do loop seguinte:
   - Apos criar a MO, percorre `move_raw_ids` e quando encontra um
     movimento cujo `product_id.name == 'Tecido de Fornecedor'`,
     escreve o valor calculado em `move.product_uom_qty`.
3. O `_logger` informa cada passo - util para diagnosticar quando o
   override nao aparenta aplicar (verificar Settings > Technical >
   Logging ou log do servidor).

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_price_table` na BD HMD.
2. Em Inventario > Artigos abrir o produto a manufaturar (o produto
   acabado, nao o tecido).
3. Aba "Aproveitamento de Tecido": preencher as 10 celulas com a
   quantidade de tecido por unidade quando a producao for 1, 2, 3, ...,
   10 unidades respetivamente. Exemplo: 1 un => 1.20 m; 2 un => 1.05 m
   cada; ...
4. Garantir que a BOM desse produto inclui uma linha com o produto
   "Tecido de Fornecedor".
5. Criar uma Ordem de Producao (manualmente ou por planeamento).
6. Confirmar que o `stock.move` de tecido fica com a quantidade da
   coluna correspondente (`min(product_qty, 10)`).

e) Exemplo pratico
------------------
Produto "Sofa Cliente A":
  - price_1 = 3.20
  - price_2 = 3.00
  - price_3 = 2.85
  - ... (decrescentes por aproveitamento)
  - price_10 = 2.30

MO com `product_qty = 1`: tecido = 3.20 m.
MO com `product_qty = 3`: tecido = 2.85 m por unidade (coluna 3).
MO com `product_qty = 7`: tecido = price_7 m.
MO com `product_qty = 25`: tecido = price_10 m (clamp ao maximo).

f) FAQ / Resolucao de problemas
-------------------------------
P: Criei uma MO mas a quantidade de tecido nao foi alterada. Porque?
R: Verificar que o produto materia-prima na BOM tem o NOME EXATO
   "Tecido de Fornecedor" (case-sensitive, sem espacos extra). O
   override compara `move.product_id.name == 'Tecido de Fornecedor'`.

P: Posso ter mais de um tecido na BOM e aplicar a tabela a ambos?
R: Nao por defeito. Atualmente so o produto chamado "Tecido de
   Fornecedor" e alterado. Para suportar varios, evoluir o filtro
   (ex.: usar uma tag/categoria em vez de nome).

P: O modulo tambem trata o consumo no Plano de Producao?
R: So no `create` da MO. Se a MO for criada via outro fluxo (replan,
   merge), o override volta a aplicar. Mas alteracoes manuais
   posteriores nao sao revertidas.

P: A tabela atual chega a 10. E se a HMD vender lotes de 20?
R: O codigo aplica `min(int(qty) - 1, 9)`, ou seja, mais de 10
   unidades usa sempre o `price_10`. Aceitavel se a curva de
   aproveitamento ja estabilizou. Senao, evoluir o modelo (lista em
   vez de 10 campos fixos).

P: O nome do campo e `price_*` - guarda preco?
R: NAO. Apesar do nome, guarda quantidade de tecido por unidade. O
   nome foi herdado de um spike - renomear envolve migrar dados.

g) Pontos de atencao / avisos
-----------------------------
- HARDCODED: nome do produto materia-prima "Tecido de Fornecedor".
- HARDCODED: a tabela tem 10 colunas. Mais que isso clamp ao 10.
- NOMENCLATURA ENGANOSA: `price_*` guarda quantidades, nao precos.
- O `_logger` esta em nivel INFO. Em producao com muitas MOs pode
  poluir o log; ponderar baixar para DEBUG.
- Overlap potencial com `pg_tecidos`: tambem mexe em movimentos de
  tecido em MO. Verificar ordem de instalacao e qual o efeito final
  desejado antes de instalar ambos.
- Os primeiros campos do manifest tinham `author='Your Name'` - foi
  consolidado para Parametro Global / HMD na proxima atualizacao.
""",
    'category': 'Manufacturing',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['mrp', 'stock'],
    'data': [
        'views/product_template_views.xml',  # Aba "Aproveitamento de Tecido" no produto.
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
