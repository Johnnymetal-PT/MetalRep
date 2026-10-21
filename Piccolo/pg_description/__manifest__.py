# -*- coding: utf-8 -*-
{
    'name': 'PG Description Enhancements',
    'version': '17.0.1.1.0',
    'summary': 'Limpa e formata a descricao das linhas SO/carrinho: tira termos excluidos, extrai info entre parenteses, ajusta TECIDO CIMA / TECIDO BAIXO conforme uso, injeta line breaks no carrinho.',
    'author': 'Parametro Global',
    'website': 'https://www.parametro.pt',
    'category': 'Sales',
    'depends': [
        'sale',
        'website_sale',
    ],
    'description': """
PG Description Enhancements
===========================

a) Objetivo de negocio
----------------------
A descricao das linhas SO da Piccolo (gerada pelo configurador de
variantes) e verbosa e contem termos uteis para o backoffice mas
ruido para o cliente final. Este modulo:
- Limpa termos excluidos ("Categoria A", "Mesmo Tecido", "Sem"...).
- Extrai informacao entre parenteses (ex.: "(Linho Bege, Cat. A)") e
  inclui so o relevante.
- Normaliza nomes "TECIDO CIMA/BAIXO" para "TECIDO" quando so um e
  usado.
- Injeta ``<br/>`` antes de termos chave para o template do carrinho.

b) Pre-requisitos
-----------------
- Modulos ``sale`` e ``website_sale``.
- Termos suportados (HARDCODED na lista interna ``terms``):
  ACABAMENTO, TECIDO COSTAS FRENTE + ASSENTO, TECIDO COSTAS TRAS,
  TECIDO, TECIDO CIMA, TECIDO BAIXO, ARO, ALTERACAO COR DOS PES,
  TIPO DE PE, DIMENSOES DO COLCHAO, FURACAO PARA TOMADA COM CAIXA
  CERTIFICADA.

c) Como funciona
----------------
- ``models/sale_order_line.py``:
  - ``cart_processed_description`` (Html, stored, computed): versao
    HTML com line breaks para o template do carrinho. Quita o nome
    do produto e injeta ``<br/>`` antes de cada termo da lista.
  - ``_process_name_field(name)``: helper que faz a limpeza
    principal:
    1. Extrai conteudo entre parenteses (``\\(.*?\\)``).
    2. Split por virgula e filtra contra
       ``excluded_terms = {"Categoria A..E", "Cliente", "Cat. A..E",
       "Matte", "Brilho | Lacado ou Verniz", "Mesmo Tecido", "Sem",
       "Sem Ponteiras"}``.
    3. Remove o conteudo entre parenteses do nome.
    4. Se ``TECIDO COSTAS FRENTE + ASSENTO`` aparece sem
       ``TECIDO COSTAS TRAS`` -> renomeia para ``TECIDO``.
    5. Idem para ``TECIDO CIMA`` -> ``TECIDO`` se nao ha
       ``TECIDO BAIXO``.
    6. Junta termos validos + bracketed validos por ``\\n``.
  - Override de ``create``/``write``/``@api.onchange``: aplica
    ``_process_name_field`` ao campo ``name`` sempre que e
    setado/editado.
  - Override de ``SaleOrder.write``: quando o estado vira ``sent`` ou
    ``sale``, re-processa **todas** as linhas (caso o utilizador
    tenha bypassado os hooks).
  - Override de ``SaleOrder.action_confirm``: sincroniza ``move.name``
    com ``line.name`` para coerencia entre SO e Picking.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Criar SO; ao adicionar produtos a descricao e processada
   automaticamente.
3. No carrinho do website, ``cart_processed_description`` mostra
   o texto formatado.
4. Confirmar SO -> stock.move recebe o ``name`` ja limpo.

e) Exemplo pratico
------------------
Input: ``"Cadeira X (Linho Bege, Cat. A, Mesmo Tecido)\\nTECIDO
COSTAS FRENTE + ASSENTO: Linho Bege"``
- Bracketed extraido: ``["Linho Bege", "Cat. A", "Mesmo Tecido"]``.
- Filtrado contra excluded: ``["Linho Bege"]``.
- Removido bracketed do nome: ``"Cadeira X\\nTECIDO COSTAS FRENTE +
  ASSENTO: Linho Bege"``.
- ``TECIDO COSTAS FRENTE + ASSENTO`` sem ``TECIDO COSTAS TRAS`` ->
  passa a ``TECIDO``.
- Resultado final: ``"Cadeira X\\nTECIDO: Linho Bege\\nLinho Bege"``.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Linha SO continua com termos excluidos"* -> o termo nao consta
  da lista ``excluded_terms``. Acrescentar manualmente no helper.
- *"<br/> nao aparece no carrinho"* -> a vista do carrinho nao
  esta a renderizar ``cart_processed_description`` (campo Html).
  Validar que o template QWeb consome este campo.
- *"Erro 'TIPO DE PE: DIMENSOES DO COLCHAO:'"* -> falta uma virgula
  na lista interna ``terms`` (line ~58). E um BUG conhecido:
  ``'TIPO DE PÉ:'`` esta sem virgula a seguir, vira string
  concatenada com o termo seguinte. **Validar antes de confiar
  100%** nestes dois termos.

g) Pontos de atencao / avisos
-----------------------------
- BUG conhecido (acima): falta virgula entre ``'TIPO DE PÉ:'`` e
  ``'DIMENSÕES DO COLCHÃO:'`` na lista ``terms`` do compute. Os
  dois termos sao concatenados como uma so string. Manter
  literalmente ate confirmar com o cliente.
- O state ``automation_trigger`` e adicionado ao Selection do
  ``sale.order.state`` - usado por automation rules externas.
  Renomear/remover sem mexer nas rules pode partir fluxos.
- ``action_confirm`` propaga ``line.name`` para ``move.name`` (sync).
  Em fluxos onde queremos o ``move.name`` literal do BoM, isto
  sobrescreve - validar.
- Override de ``create`` chama ``_process_name_field`` ANTES do
  super; se outro modulo tambem override o name no create, ordem
  importa.
""",
    'data': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
