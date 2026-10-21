{
    'name': 'PG Tecidos - Customizacao por Variantes em MO',
    'version': '18.0.1.0.6',
    'summary': 'Replica a BoM por MO, ajusta consumos de tecido e cria componentes derivados conforme a descricao de variantes da venda.',
    'description': """
PG Tecidos - Customizacao por Variantes em MO (HMD)
====================================================

a) Objetivo de negocio
----------------------
Os moveis HMD sao personalizados linha a linha na venda: cor de
tecido, cor dos pes, tipo de acabamento, ARO, ponteira, tamanho.
Quando a Ordem de Producao e criada, a BoM standard "mae" do produto
nao chega - precisa de ser duplicada por MO, com:
  - componentes especificos por variante (ex.: o componente generico
    "Tecido" passa a chamar-se "Tecido X cor Azul" se a venda disser
    "TECIDO: Azul");
  - quantidades de tecido ajustadas conforme a tabela de
    aproveitamento ("pg_price_table" - 10 colunas de 1 a 10 unidades);
  - fornecedor automatico pre-atribuido aos componentes recem-criados
    (fornecedor de tecidos generico, polidor para acabamentos).

Este modulo le a descricao de variantes da venda, faz parsing por
regex e termos esperados, e ajusta a BoM antes de criar a MO.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `mrp`, `stock`, `product`, `mail`.
- DEPENDENCIA IMPLICITA (NAO declarada em `depends`): este modulo le
  os campos `price_1` ... `price_10` do `product.template` que sao
  declarados pelo modulo `pg_price_table`. Em pratica, instalar
  ambos em conjunto. Em upgrade, declarar a dependencia formalmente.
- Fornecedores especificos tem de existir em `res.partner` com nomes
  EXATOS:
    - "-Fornecedor de tecidos a definir" (hifen inicial, exatamente)
    - "Polidor C/Arte Mobiliario, Lda"
  Se algum nao existir, o `_assign_vendor_to_product` emite warning
  e o componente fica sem fornecedor.
- A linha de venda tem de trazer descricao de variantes no formato
  texto linha-a-linha:
      TECIDO COSTAS FRENTE + ASSENTO: Azul Royal
      TECIDO COSTAS TRAS: Cinza
      ACABAMENTO: Lacado mate
      ARO: Negro
  Termos esperados (vide `expected_terms` em mrp_production.py):
  ACABAMENTO, ACABAMENTO com Ponteira, TECIDO COSTAS FRENTE +
  ASSENTO, TECIDO COSTAS TRAS, TECIDO CIMA, TECIDO BAIXO, TECIDO,
  ARO, SIZE, FINISH, ALTERACAO COR DOS PES.

c) Como funciona (tecnico)
--------------------------
1. `mrp.production` override de `create`
   (`models/mrp_production.py`):
   a) Procura uma `sale.order.line` que combine com o produto da MO -
      usa para obter `product_qty` esperada e fallback para a
      descricao de variantes.
   b) Faz parsing da descricao em `parsed_terms` (linha-a-linha,
      split em ':'); normaliza nomes de chave em UPPER.
   c) Mapeia para `expected_terms` por substring match.
   d) Reconstroi `product_description_variants` no formato canonico.
   e) Procura a BOM "mae" do produto template (mais antiga -
      `create_date asc`) e identifica cada linha de BoM por substring
      no nome do componente (ex.: "tecido cima").
   f) Duplica a BoM (`copy()`), atribui codigo = nome do SO,
      escala `product_qty` da BoM ao qty pedido.
   g) Para componentes nao-tecido, escala `line.product_qty *=
      product_qty` (regra atual).
   h) Para componentes de tecido, le a tabela `price_1..10` do
      proprio componente e calcula
      `total = price_<qty_index> * product_qty`.
   i) Para cada linha que case com um termo no nome do componente
      original (ex.: nome "Tecido cima"), cria/reutiliza um
      `product.template` com nome resultante da substituicao da
      placeholder pelo valor da variante (ex.: "Tecido cima" + valor
      "Azul Royal" -> "Azul Royal cima"). Copia campos custom
      `price_*` e atribui fornecedor.
   j) Atribui a BoM duplicada a MO criada.

2. `mrp.workorder`: campo `product_description_variants` related da
   producao (so para mostrar nas WO).

3. `stock.move` override:
   - Adiciona `partner_id` (Endereco de destino / Fornecedor)
     computed: procura o supplierinfo do produto. Tornar editavel +
     sincronizar para `supplierinfo` no write.
   - `_update_supplier_info` cria/atualiza supplierinfo a partir do
     partner_id da move.

4. `stock.rule._run_manufacture` override:
   - Procura a BoM por variante; fallback ao template.
   - Define `location_src_id` (com fallback ao stock global se a
     regra nao tiver).
   - Cria a MO com `procurement_group_id` ligado ao procurement.

5. `mrp.bom.line`: campo computed `product_template_attachment_ids`
   (mirror read-only dos anexos do produto - para visualizar fichas
   da BoM line).

6. Data (`data/groups.xml`): cria grupos "Basic User" e "Power User"
   herdando de um grupo selector. Sem uso ainda (sem ACL/rules
   associadas) - infraestrutura preparada para futuros perfis.

d) Passo a passo de utilizacao
------------------------------
1. Garantir que `pg_price_table` esta instalado (campos price_*).
2. Instalar `pg_tecidos` na BD HMD.
3. Confirmar que existem fornecedores com os nomes EXATOS exigidos
   (ver Pre-requisitos).
4. Em Vendas, na linha de venda, escrever a descricao de variantes
   no formato canonico (ver Pre-requisitos).
5. Confirmar a venda. A MO e criada (via procurement standard).
6. Abrir a MO: confirmar que:
     - `product_description_variants` esta preenchido em formato
       canonico;
     - a BoM e uma copia (codigo = nome do SO);
     - os componentes "Tecido X" tem nomes substituidos pelo valor
       da variante;
     - as quantidades de tecido estao ajustadas conforme a tabela.

e) Exemplo pratico
------------------
SO S00050, linha:
    Produto: "Sofa Modelo Lara"
    Descricao:
        TECIDO COSTAS FRENTE + ASSENTO: Azul Royal
        TECIDO COSTAS TRAS: Cinza Pedra
        ACABAMENTO: Lacado mate Branco
    Qty: 4

A BoM mae do "Sofa Modelo Lara" tem componentes:
  - Estrutura (1 un)
  - Tecido (2.5 m por unidade, conforme price_1=2.5)
  - Tecido costas tras (1.2 m por unidade)
  - Pes (4 un)
  - Acabamento

Apos criar a MO:
  - BoM duplicada com code = "S00050".
  - "Estrutura" qty = 1 * 4 = 4 un.
  - "Tecido" (mapeado a TECIDO COSTAS FRENTE + ASSENTO): nome muda
    para "Azul Royal Tecido" e qty = price_4 do componente * 4.
  - "Tecido costas tras" (mapeado a TECIDO COSTAS TRAS): nome
    "Cinza Pedra costas tras" e qty equivalente.
  - "Pes" qty = 4 * 4 = 16 un (escala geral).
  - Componentes derivados tem fornecedor automatico
    "-Fornecedor de tecidos a definir".

f) FAQ / Resolucao de problemas
-------------------------------
P: A MO foi criada mas a BoM nao foi duplicada. Porque?
R: O `_search_oldest_bom` nao encontrou BoM com
   `product_tmpl_id == product.product_tmpl_id`. Verificar que existe
   uma BoM (de qualquer tipo `normal`) para o produto template.

P: Os tecidos ficaram com qty 0. Porque?
R: O componente do tecido na BoM mae nao tem a tabela `price_1..10`
   preenchida. Preencher no produto template do componente, nao no
   produto acabado.

P: Erro "Nenhuma BoM encontrada" no stock.rule. Solucao?
R: A rota de fabrico do produto nao tem BoM por variante nem por
   template. Criar BoM com tipo `normal`.

P: Os componentes duplicados nao tem fornecedor. Porque?
R: Os nomes dos fornecedores estao hardcoded
   ("-Fornecedor de tecidos a definir",
   "Polidor C/Arte Mobiliario, Lda"). Confirmar que existem com nome
   EXATO em Contactos.

P: A descricao da variante na venda tem espacos/caps diferentes do
   esperado. Resolve sozinho?
R: O parser normaliza chaves em UPPER e faz substring match com
   `expected_terms`. Variacoes (TECIDO vs Tecido) sao toleradas;
   typos (TECDIO) NAO sao.

P: Encomendei 25 unidades, a tabela so tem 10. Que valor e usado?
R: `min(int(qty) - 1, 9)` -> usa `price_10` para qualquer qty >= 10.
   Igual a `pg_price_table`.

P: Estou a re-criar a MO e os produtos derivados ja existem. Cria
   duplicados?
R: Nao. `_duplicate_and_assign_to_bom` procura por nome existente;
   se houver mais que um, desativa os extra (`active=False`) e
   reutiliza o mais recente.

P: O `stock.move.partner_id` apareceu na view. Para que serve?
R: E o "endereco de destino" / fornecedor do componente. Permite
   editar e o `write` propaga para o supplierinfo. Util quando o
   fornecedor real do componente derivado ainda nao esta definido.

P: Os grupos "Basic User" / "Power User" criados nao aparecem em
   lado nenhum. Estao a uso?
R: Nao. Infraestrutura preparada (data/groups.xml) sem ACL/regras
   associadas ainda. Remover se nao for usar, ou ligar a casos de
   uso concretos.

g) Pontos de atencao / avisos
-----------------------------
- DEPENDENCIA NAO DECLARADA: o modulo le `price_1..10` do
  `pg_price_table`. Em proxima atualizacao, adicionar
  `pg_price_table` em `depends`.
- HARDCODED:
    - lista `expected_terms` em PT;
    - mapping termo <-> substring no nome do componente;
    - nomes dos fornecedores (`-Fornecedor de tecidos a definir`,
      `Polidor C/Arte Mobiliario, Lda`);
    - `delay = 7` dias em supplierinfo criados.
- DEPENDENCIA implicita em `mrp.production.product_description_variants`
  (o `_inherit` declara este campo em pg_tecidos, mas o standard
  tambem tem campo homonimo - validar nao colidir em upgrade).
- O `_run_manufacture` override pode entrar em conflito com a
  pipeline standard de procurements. Se o cliente instalar OCA
  modulos que tambem fazem override, validar a ordem.
- `_apply_consumption_values` so cobre termos TECIDO* (TECIDO COSTAS
  TRAS, TECIDO COSTAS FRENTE + ASSENTO, TECIDO CIMA, TECIDO BAIXO,
  TECIDO). ACABAMENTO, ARO, etc. nao entram nesta fase - so se cria
  o produto derivado em `_duplicate_and_assign_to_bom`.
- O `stock.move.product_id` esta re-declarado como `required=True` -
  no standard ja e required, mas a re-declaracao explicita garante
  o comportamento. Validar em upgrade.
- Em produccao com varias MOs por minuto, os `_logger.info`
  abundantes podem encher o log; baixar para DEBUG quando o feature
  estabilizar.
- SUBCONTRATACAO: o `create` da MO ignora MO de subcontratacao
  (`subcontractor_id` ou BoM tipo `subcontract`) e a BoM "mae" so e
  escolhida entre BoM `normal`. Antes disto (ate 18.0.1.0.0) cada
  rececao de subcontratacao duplicava a lista de subcontratacao e
  MO normais podiam ficar com listas de subcontratacao.
- PROJETO (18.0.1.0.2 a .4; a .3 acrescenta o fallback pela venda do grupo e
  regista o projeto na nota do chatter da MO; a .4 impede que a troca da
  lista pela cópia por encomenda apague o projeto, porque o `project_mrp`
  recalcula `project_id` quando `bom_id` muda): o `_run_manufacture` desta extensao nao chama o
  super, pelo que a MO nunca herdava o projeto da venda. Passa agora o
  `project_id` dos valores do procurement. Efeito: com `project_mrp_account`
  os consumos da MO lancam-se nas contas analiticas do projeto.
- SUBCONTRATACAO (18.0.1.0.5/.6): a MO de subcontratacao (criada na rececao) passa a
  trocar o componente de tecido generico pelo da linha de venda de origem
  (rececao -> movimentos de destino -> `sale_line_id`), antes do `action_confirm`
  do standard; a saida de reposicao herda o artigo trocado. Se o valor for C.O.M.
  (tecido do cliente), usa o artigo 'TECIDO C.O.M.' (copia do generico, sem
  rotas e nao comprável) para nunca gerar compra. Falhas ficam no log e nao
  bloqueiam a rececao. A tabela de aproveitamento (price_1..10) NAO se aplica aqui.
- Risco em upgrade Odoo 19: regex/string matching contra nomes de
  componentes e fragil. Mudancas de nomenclatura na BD partem a
  logica silenciosamente.
""",
    'depends': ['mrp', 'stock', 'product', 'mail'],
    'data': [
        'views/pg_tecidos_view.xml',
        'data/groups.xml',
    ],
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
