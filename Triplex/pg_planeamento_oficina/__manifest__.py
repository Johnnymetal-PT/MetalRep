# -*- coding: utf-8 -*-
{
    'name': 'pg Planeamento Oficina',
    'version': '17.0.2.1.0',
    'summary': 'Painel de planeamento da oficina (CEO/Administração) em tempo real, substituindo o Excel',
    'description': """
pg Planeamento Oficina
======================

Objetivo de negócio
-------------------
Dar à Administração/CEO um painel único, em tempo real, para acompanhar a oficina
(Oficinna22): que encomendas estão em curso, em que estado de produção, que componentes
faltam por fornecedor (tecido, casco, inox, polidor, embalagem), e a previsão de faturação
por semana. Substitui o ficheiro Planeamento_Oficinna22.xlsx, mas com dados sempre atuais.

Pré-requisitos
--------------
- Módulos: `sale_management`, `sale_stock`, `mrp`, `account`.
- Classificar os FORNECEDORES: preencher o campo "Tipo de Fornecedor" (x_supplier_type) em
  res.partner com tecido/casco/polidor/inox/embalagem. É isto que alimenta as colunas de
  componentes do painel.
- Os componentes de BOM têm de ter fornecedor (seller_ids) para serem classificados.
- O posto de trabalho de corte deve ter "CORTE" no nome para a coluna Corte funcionar.
- Campo Studio `x_studio_semana` na sale.order (opcional) para agrupar por semana.

Como funciona
-------------
- `pg.planeamento.line`: uma linha por `sale.order.line`, com campos quase todos calculados
  a partir da venda + ordens de fabrico + movimentos de componentes (estado da encomenda,
  estado do corte, estado de cada componente, datas, semana, faturação, totais).
- `sale.order.line.create()`: ao criar uma linha de venda, cria automaticamente a linha de
  planeamento correspondente.
- `stock.move`: campos calculados `x_supplier_type`/`x_vendor_id` derivados do fornecedor
  do produto (primeiro seller com tipo definido) — usados para classificar componentes.
- `res.partner`: campo `x_supplier_type` (categoria do fornecedor).
- `post_init_hook` `_post_init_backfill`: ao instalar, cria as linhas de planeamento para
  todas as linhas de venda já existentes.

Passo a passo de utilização
---------------------------
1. Após instalar, classificar os fornecedores em Contactos -> "Tipo de Fornecedor".
2. Garantir que os componentes dos produtos têm o fornecedor correto associado.
3. Abrir o menu "Planeamento Oficina" — as linhas das encomendas aparecem e atualizam-se
   automaticamente à medida que vendas e ordens de fabrico evoluem.
4. Filtrar/agrupar por estado, semana, fornecedor, etc.; abrir a encomenda a partir da linha.

Exemplo prático
---------------
Uma encomenda confirmada com OF em curso aparece com Estado "Em Produção"; se o tecido ainda
não foi rececionado, a coluna Tecido mostra "Falta" com o nome do fornecedor; quando o
movimento do tecido fica "done", passa a "Recebido".

FAQ / Resolução de problemas
----------------------------
- P: A coluna de um componente mostra "N/A".
  R: Não há movimento desse tipo de fornecedor na OF — confirmar a classificação do fornecedor
     (x_supplier_type) e os sellers dos componentes.
- P: A coluna "Corte" está vazia.
  R: A OF não tem ordem de trabalho num posto cujo nome contenha "CORTE".
- P: A "Semana" não aparece.
  R: A venda não tem o campo Studio `x_studio_semana` preenchido.
- P: Instalei e não vejo encomendas antigas.
  R: O backfill corre no post_init; reinstalar/atualizar o módulo volta a executá-lo.

Pontos de atenção
-----------------
- As ordens de fabrico são associadas por correspondência de `origin` com o nome da venda.
- Vários campos dependem de campos custom/Studio (x_supplier_type, x_studio_semana).
- É um painel de leitura/gestão; não substitui os documentos de venda/produção.
""",
    'category': 'Manufacturing',
    'author': 'Parametro Global',
    'license': 'LGPL-3',

    # `pg_mrp_people_count` fornece o número de pessoas por registo de tempo e as
    # horas-pessoa apuradas. É este módulo que as consome e apresenta no painel, daí a
    # dependência ser nesta direcção: o planeamento conhece a recolha, não o contrário.
    'depends': ['sale_management', 'sale_stock', 'mrp', 'account', 'purchase_stock',
                'pg_mrp_people_count'],

    'data': [
        'security/pg_planeamento_security.xml',
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
        'views/pg_planeamento_views.xml',
        'views/pg_planeamento_menus.xml',
        'report/pg_planeamento_report.xml',
        'report/pg_planeamento_xlsx.xml',
    ],

    'post_init_hook': '_post_init_backfill',

    'installable': True,
    'application': True,
}
