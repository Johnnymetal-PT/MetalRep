# -*- coding: utf-8 -*-
{
    'name': 'Product Variant Internal Reference',
    'version': '17.0.1.0.0',
    'summary': 'Atribui automaticamente referencias internas (default_code) a variantes de produto criadas dinamicamente.',
    'author': 'Parametro Global',
    'category': 'Inventory/Management',
    'depends': ['product'],
    'data': [],
    'description': """
PG Internal Reference
=====================

a) Objetivo de negocio
----------------------
Garantir que toda a variante de produto fica com um codigo interno
(``default_code``) consistente, evitando esquecer de atribuir manualmente
quando aparecem variantes novas. O codigo segue o padrao
``<base>-<contador 5 digitos>`` (ex.: ``ABC-00007``).

b) Pre-requisitos
-----------------
- Modulo standard ``product`` instalado.
- A primeira variante do template tem de ter ``default_code`` preenchido
  manualmente. E desse codigo que se extrai o prefixo ``<base>`` (parte
  antes do primeiro ``-``).

c) Como funciona
----------------
- Override de ``product.product.create`` em
  ``models/product_product.py``.
- Quando uma variante e criada sem ``default_code``:
  1. Procura a primeira variante do mesmo ``product_tmpl_id`` que ja
     tenha um ``default_code`` (ordenada por id ascendente).
  2. Usa a parte antes do primeiro ``-`` desse codigo como prefixo base.
  3. Lista os ``default_code`` existentes desse template, extrai o
     contador final (depois do ultimo ``-``) e calcula
     ``max(counter) + 1``.
  4. Atribui ``"<base>-<counter:05d>"`` a nova variante.
- Tambem expoe ``assign_default_codes_to_all_variants()`` para
  reprocessar variantes existentes do mesmo template a que falte codigo.
- Erros sao apanhados num ``try/except`` e logados (nao bloqueiam o
  ``create``) - intencional para nao impedir criacao de variantes via
  configurador.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo.
2. Num template novo: criar manualmente a primeira variante com o
   codigo ``BASE-00001`` (ou similar).
3. A partir dai, todas as variantes geradas (via configurador, import,
   atributos dinamicos) recebem ``BASE-00002``, ``BASE-00003``, etc.

e) Exemplo pratico
------------------
Template "Cadeira Y" com a primeira variante codificada como
``CAD-00001``. Ao adicionar um atributo "Cor = Azul" via configurador,
a nova variante e criada com ``default_code = CAD-00002``
automaticamente.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Nova variante sem codigo"* -> verificar se existe ao menos uma
  variante com ``default_code`` no template; sem isso, o log avisa
  "No base default_code found" e a variante fica sem codigo.
- *"Codigo com hifen no meio do prefixo"* (ex.: ``ABC-XYZ-00001``)
  o algoritmo so faz split no primeiro ``-`` para o prefixo e no ultimo
  ``-`` para o contador, por isso pode ficar mal numerado. Evitar
  prefixos com ``-`` internos.

g) Pontos de atencao / avisos
-----------------------------
- O override de ``create`` corre **para todas** as ``product.product``
  da BD - desligar este modulo se houver outro fluxo a tomar conta da
  numeracao.
- Em caso de race condition (criacao simultanea de variantes), pode
  haver colisao no contador. Em pratica, no fluxo Piccolo isto nao tem
  ocorrido porque a criacao e quase sempre sequencial via wizard/import.
""",
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
