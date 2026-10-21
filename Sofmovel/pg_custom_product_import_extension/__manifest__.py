{
    'name': 'PG Custom Product Import Extension Kave',
    'version': '17.0.1.0.2',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Importacao em massa de produtos Kave Home a partir de Excel (cria, atualiza, reativa e arquiva).',
    'description': """
PG Custom Product Import Extension Kave
=======================================

a) Objetivo de negocio
----------------------
Sincronizar o catalogo "Kave Home" no Odoo a partir do ficheiro Excel oficial
da Kave. O wizard:
- Cria produtos novos com tag "Kave" e categorias proprias.
- Atualiza produtos existentes Kave (matching por `default_code` ou barcode).
- Reativa produtos Kave arquivados que voltem a aparecer no ficheiro.
- Arquiva produtos Kave ativos que deixaram de constar no ficheiro
  ("archive missing pass").
- Garante IVA de venda, publica no website com best-effort (tolera falhas
  controladas), gere stock, supplierinfo, orderpoints e acessorios.

Pensado para correr em base de dados grande, com retries em deadlocks, logs
estruturados e email de resumo no final.

b) Pre-requisitos
-----------------
- Modulos: `base`, `product`, `sale`, `web`.
- Bibliotecas Python: `pandas`, `psycopg2`, `openpyxl` (lido por pandas).
- Configuracao no Odoo:
  - Tag "Kave" (`product.tag`) - criada automaticamente se nao existir.
  - Categorias "Produtos Kave" em `product.category` (sob "All"),
    `product.public.category` (sob "Todas") e `pos.category` - criadas
    automaticamente.
  - Fornecedor `res.partner` com `name = 'Kave Home'` - tem de existir
    antes da importacao (rebenta com UserError caso contrario).
  - Rotas de stock obrigatorias:
    - "Comprar"
    - "BRAGA: Supply Product from FREAMUNDE"
    - "SEIXAL: Supply Product from FREAMUNDE"
  - Localizacoes obrigatorias por warehouse:
    "FRE/Stock", "BRA/Stock", "SEI/Stock".
  - IVA de venda: tenta primeiro `account.tax` com id 1567; senao escolhe a
    primeira sale tax da empresa alvo (id 2) ou shared.
  - Campos Studio usados: `x_studio_cdigo_de_barras`, `x_studio_quantidade_em_stock`,
    `x_studio_stock_em_7_dias`, `x_studio_stock_em_15_dias`,
    `x_studio_stock_em_30_dias`, `x_studio_preo_antes_desconto`,
    `x_studio_desconto_aplicado_1`, `x_studio_data_estimada_de_entrega`.
- Empresa alvo: ID hardcoded = 2.
- Localizacao para quants iniciais: ID hardcoded = 54 ("KAV/Stock").

c) Como funciona
----------------
- `models/product_import_kave_wizard.py`:
  - `purchase.order.line` ganha `x_studio_largura` e `x_studio_comprimento`.
  - `product.import.kave.wizard` (TransientModel) com `action_import`:
    1. Le XLSX com pandas, normaliza colunas obrigatorias e valores numericos
       em formato PT (1.234,56).
    2. Faz preload de todos os templates Kave por `default_code` ou
       `x_studio_cdigo_de_barras` e respetivos `supplierinfo`, locations,
       orderpoints e quants - para evitar N+1 querys.
    3. Para cada linha:
       a. Faz match em caches Kave (barreira: `_ensure_kave_only` impede
          escrever em produtos nao-Kave).
       b. Se for Kave arquivado, reativa e tenta publicar (best-effort).
       c. Pesa pesos compostos com separador "#" (`peso_cada_volume`).
       d. CREATE ou WRITE com `_write_with_retries` em savepoint para tolerar
          deadlocks/lock timeouts (lock_timeout=1s, statement_timeout=120s).
       e. Garante IVA de venda antes de publicar.
       f. `_apply_publish_best_effort` faz downgrade de erros conhecidos
          (sem stock unico, sem IVA) para warning + `website_published=False`.
       g. Atualiza acessorios por agrupamento de `Program`, supplierinfo
          (preco, desconto, EUR, fornecedor Kave Home), quants em loc 54,
          `sale_delay` (com base em data estimada ou em stock progressivo)
          e orderpoints por warehouse.
    4. `_archive_missing_kave_products`: arquiva produtos Kave ativos cujo
       `default_code` nao aparece no ficheiro. Faz primeiro sem detach, e em
       caso de erro repete com `_detach_product_from_promotions_best_effort`
       para soltar de programas de loyalty/promocoes.
    5. `send_success_email`: envia mail HTML para o utilizador atual com
       resumo, tabelas de erros, warnings e amostra de falhas a arquivar.
- `models/product_import_kave_job.py`:
  - `product.import.kave.job` (modelo persistente) com states
    queued/running/done/failed. O cron `cron_process_jobs` esta como
    placeholder e marca queued -> failed (a implementacao real do worker
    assincrono e trabalho futuro). [PONTO POR VALIDAR] se ainda e necessario.

d) Passo a passo de utilizacao
------------------------------
1. Garantir os pre-requisitos (fornecedor Kave Home, rotas, IVA, localizacoes).
2. Menu Inventario / Importacoes / Importar Produtos Kave (ver
   `views/product_import_menu.xml`).
3. Carregar o XLSX Kave (estrutura indicada nas colunas obrigatorias).
4. Executar. Acompanhar progresso no log do servidor (linhas com
   "Kave import progresso", "Archive attempt", etc.).
5. Receber email no fim com sumario, erros, warnings e amostra de falhas a
   arquivar.

e) Exemplo pratico
------------------
- Linha XLSX:
  - Code = "KAVE-001", EAN = 5601234567890, Program = "Sofa LISBOA",
    Description = "Sofa 3 lugares", Stock = 4, Purchase Price = 250,00 EUR,
    Discount = 10%, Recommended Retail Price = 690, Suggested Retail Price = 599,
    Weight Package = "12.5#18#9", Stock Blue/Red/Grey = 0/2/5,
    Estimated Date = 30/06/2026.
- Resultado:
  - Template KAVE-001 criado/atualizado, com tag Kave, categorias Kave,
    list_price 599, compare_list_price 690 (mostrara desconto),
    weight = 39.5 kg, volume_qty = 3, peso_cada_volume = "12.5 / 18 / 9",
    sale_delay calculado a partir da Estimated Date.
  - Stock 4 em KAV/Stock, supplierinfo Kave Home com preco 250 e desconto 10%.
  - Orderpoints criados em BRA/Stock, SEI/Stock e FRE/Stock.
  - Produto publicado se tiver IVA de venda.

f) FAQ / Resolucao de problemas
-------------------------------
- "UserError: Fornecedor 'Kave Home' nao encontrado":
  Criar primeiro o `res.partner` Kave Home.
- "UserError: Rota 'Comprar' nao encontrada / Rotas de supply nao encontradas":
  Configurar as rotas com os nomes exatos.
- "Email de resumo nao chegou":
  O utilizador que correu o wizard tem de ter `email` configurado. Caso
  contrario o log diz: "Nao foi possivel enviar email: utilizador sem email".
- "Linhas com erro 'Coluna obrigatoria em falta'":
  Conferir colunas: Code, EAN Code, Program, Description, Stock,
  Purchase Price, Discount, Nett Purchase Price, Recommended Retail Price,
  Suggested Retail Price, Weight Package, Stock Blue, Stock Red, Stock Grey,
  Estimated Date (dd/mm/yyyy).
- "Produto deveria publicar mas nao publica":
  Ler o warning na seccao "Publicacao" no email. Sem IVA de venda nao publica.
- "Archive pass falha com deadlocks":
  O processo ja tem retries; em ultimo recurso correr fora de horas. Falhas
  vao com sample de ate 60 produtos no email.

g) Pontos de atencao
--------------------
- IDs hardcoded: empresa = 2, localizacao KAV/Stock = 54, fallback IVA id 1567.
  Migracoes a outras BD precisam reescrever estes valores.
- Convive com [[pg_custom_product_import_extension_2]] (variante Sofmovel) mas
  cada um trata uma tag (Kave vs Sofmovel) e nao concorrem.
- Skips de automacao usados durante massa: `skip_product_log`,
  `skip_supplier_tax_update`, `tracking_disable`, `mail_notrack`,
  `mail_create_nosubscribe`, `mail_auto_subscribe_no_notify` - melhoram
  throughput mas pressupoem que outros modulos respeitem estas flags.
- `_detach_product_from_promotions_best_effort` quebra liaisons com loyalty
  para libertar o produto; e best-effort e nunca rebenta o wizard.
    """,
    'depends': ['base', 'product', 'sale', 'web'],
    'data': [
        'views/product_import_menu.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
