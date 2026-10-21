{
    'name': 'PG Etiquetas',
    'version': '19.0.1.0.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Etiquetas de artigo A5, 5x8 e ZPL, com preço antes do desconto (substitui os relatórios Studio da V17).',
    'description': """
PG Etiquetas
============

a) Objetivo de negócio
----------------------
A Sofmovel etiqueta a mercadoria na recepção, em três formatos: A5 e 5x8 em papel
e ZPL em impressora térmica nas lojas. A etiqueta tem de mostrar o preço a cobrar
e, quando o artigo está em promoção, **o preço anterior riscado** — é o que prova
o desconto a quem está na loja, e é o que o website já faz com o preço riscado.

Cobre as tarefas 6570 (nova etiqueta com valor pós-desconto face ao valor antes do
desconto) e a parte de código da 6571 (impressão ZPL por IoT).

Na V17 as etiquetas eram cinco relatórios **Odoo Studio**
(`studio_customization.studio_report_docume_<uuid>`), chamados pelo módulo
`PG_Etiquetas_A5` através desses UUID. Estando na base e não no código, não migram
para a v19: este módulo substitui-os.

b) Pré-requisitos
-----------------
- Módulos standard `product` e `stock`.
- Para imprimir ZPL: módulo `iot` instalado e o relatório "Etiqueta ZPL (recepção)"
  ligado ao dispositivo de impressora da loja — ver alínea (g).
- Opcionais, usados se existirem: `compare_list_price` (vem do `website_sale`) e os
  campos Studio da base migrada. Nenhum é obrigatório; a leitura é defensiva.

c) Como funciona
----------------
- `models/product_template.py`
  - Campo novo `pg_label_type` (A5 / 5x8 / ZPL), que substitui o `print_label_type`
    da V17 — ver alínea (g).
  - `_pg_label_prices`: devolve `(preço a cobrar, preço anterior)`. O preço anterior
    vem a 0.0 quando não há desconto a mostrar, e o template só o imprime se for
    **maior** que o preço a cobrar — nunca aparece um "antes" mais barato do que o
    "agora".
  - `_pg_label_compare_price`: procura o preço anterior em `compare_list_price`
    (nativo, o mesmo que a loja online usa) e, em falta, em
    `x_studio_preo_antes_desconto`. A ordem é a decisão do projeto: o nativo é a
    fonte de verdade, o Studio é recurso enquanto os dados não convergirem — na
    produção V17 o nativo está preenchido em 1299 artigos contra 6181 do Studio.
  - `_pg_label_pricelist`: lista de preços da etiqueta, do contexto ou a por
    omissão da empresa.
  - `_pg_label_reference` / `_pg_label_barcode`: referência e código de barras, com
    o campo Studio como espelho.
  - `_pg_label_logo_url`: logótipo, por parâmetro de sistema — ver alínea (g).
- `models/product_product.py`: o mesmo para a variante, que tem referência e código
  de barras próprios. O preço parte do `x_variant_sale_price` quando existe, como
  na etiqueta ZPL da V17.
- `models/stock_picking.py`: botões da recepção. O PDF junta A5 e 5x8 num
  documento (`odoo.tools.pdf.merge_pdf`); o ZPL sai por `report_action`, sem wizard.
- `report/`: os cinco relatórios e o QWeb das três etiquetas. O corpo da A5 está num
  template só, chamado pelos três relatórios que a usam — em Studio eram três cópias
  e qualquer correcção tinha de ser feita três vezes.
- `hooks.py`: copia o `print_label_type` da V17 para o campo novo.

d) Passo a passo de utilização
------------------------------
1. Instalar o módulo. O `post_init_hook` recupera o tipo de etiqueta de cada artigo.
2. Definir os logótipos, se forem diferentes do da empresa:
   `pg_etiquetas.logo_id` e `pg_etiquetas.logo_kave_id` em Configuração >
   Técnico > Parâmetros do sistema, com o id do anexo da imagem.
3. Com o `iot` instalado, ligar o relatório "Etiqueta ZPL (recepção)" à impressora
   de cada loja (campo "IoT Devices" do relatório).
4. Na recepção: "Etiquetas A5/5x8" para papel, "Etiquetas ZPL" para as térmicas.
5. Conferir o filtro "Sem tipo de etiqueta" na lista de artigos — esses ficam de
   fora da impressão.

e) Exemplo prático
------------------
Artigo ABAJUR, preço de venda 20,00 € e `compare_list_price` 40,00 €. A etiqueta
imprime **40,00 € riscado** e **20,00 €** em grande. O mesmo artigo sem preço
anterior registado imprime só os 20,00 €, sem espaço vazio nem zero.

f) FAQ / Resolução de problemas
-------------------------------
- "Imprimi e não saiu nada na impressora térmica":
  Ver alínea (g), ponto do IoT. Confirmar a que dispositivo o relatório está ligado.
- "A etiqueta imprime 1,00 €":
  O artigo não tem regra própria na lista de preços. O comportamento herdado da V17
  é usar o preço de venda quando a lista devolve 0 ou 1 — desliga-se com o parâmetro
  `pg_etiquetas.fallback_lst_price` a `False`, e aí o preço da lista sai como está.
- "O preço da etiqueta ZPL está desactualizado":
  Ver alínea (g), ponto do `x_variant_sale_price`.
- "O preço anterior não aparece":
  Só aparece quando é maior que o preço a cobrar. Confirmar `compare_list_price` no
  artigo, ou o campo Studio equivalente.
- "Os campos `x_studio_*` não existem":
  É o esperado numa base v19 limpa. São ignorados.

g) Pontos de atenção
--------------------
- **Nome do campo (`pg_label_type`)** — o campo da V17 chamava-se
  `print_label_type`, no mesmo modelo e com os mesmos valores. Foi mudado de nome de
  propósito: mantendo o nome, desinstalar o `PG_Etiquetas_A5` apagaria a coluna e
  levaria os dados de 9609 artigos. Com nomes diferentes os dois coexistem, o
  `post_init_hook` copia, e o módulo antigo sai sem perda. Depois de confirmar as
  contagens, o `PG_Etiquetas_A5` deve ser desinstalado — senão ficam dois campos a
  dizer o mesmo.
- **Encaminhamento IoT (tarefa 6571)** — a V17 tinha um wizard
  (`choose.iot.printer.wizard`) que fazia o utilizador escolher uma **caixa** IoT e
  chamava `report.with_context(iot_device_id=<id de iot.box>).report_action(...)`.
  Nem a chave nem o modelo são os do standard: o módulo `iot` encaminha por
  `ir.actions.report.device_ids` (Many2many para `iot.device`) ou por
  `data={'device_id': <id de iot.device>}`, e um grep por `iot_device_id` em todo o
  módulo `iot` não devolve nada. **A escolha do utilizador não tinha efeito.** O
  documento ia para os dispositivos ligados ao relatório — que na produção V17 são
  as duas Zebras ao mesmo tempo, a de Braga (94) e a do Seixal (96). Imprimir numa
  loja e a etiqueta sair na outra é a explicação mais provável dos reinícios da
  caixa IoT. Aqui o wizard desapareceu: quando o relatório tem mais do que uma
  impressora ligada, é o standard que pergunta qual (`select.printers.wizard`, com
  "não voltar a perguntar"). **Falta ainda a configuração na base migrada**: ligar
  cada relatório à impressora da loja certa, e arquivar as quatro caixas
  "PGPCOELHO" (máquinas de desenvolvimento, com 12 impressoras e 7 balanças de
  ruído). Isso é configuração, não código.
- **Versão das caixas IoT** — as das lojas correm imagem `W23.11-17.0-20250917`, do
  ramo 17.0. A base a passar para 19.0 exige actualizar as caixas; sem isso não se
  imprimem etiquetas no dia do go-live. É trabalho de infraestrutura, a agendar.
- **`x_variant_sale_price`** — é a base do preço na etiqueta ZPL, vem do
  `pg_update_variant_prices` e é um **instantâneo**: só muda quando alguém corre a
  acção na lista de preços. A etiqueta pode por isso imprimir um preço velho. Fica
  primeiro na ordem porque é o que a V17 usava e mudá-lo alterava os preços
  impressos hoje; a correcção de fundo é recalcular por rotina ou passar a ler a
  lista directamente, e é uma decisão a tomar com a Sofmovel.
- **Risco no ZPL** — o preço anterior é riscado desenhando uma linha (`^GB`) por
  cima do texto, porque o ZPL não tem texto riscado. A largura da linha é estimada a
  partir do número de caracteres (`len * 16`). `PONTO POR VALIDAR`: confirmar numa
  etiqueta impressa de verdade, numa Zebra, antes de dar por fechado.
- **Logótipos** — a V17 tinha dois ids de anexo fixos no QWeb (`/web/image/4022059`
  e `/web/image/4036491`). Ids fixos não sobrevivem a outra base; aqui vêm de
  parâmetros de sistema e, em falta, usa-se o logótipo da empresa.
- Face à V17 foram deliberadamente removidos: o `request.env[...]` dentro do QWeb
  (não é fiável no render de relatórios, e era como a V17 ia buscar a lista de
  preços e o tecido), o `search([], limit=1)` para escolher a lista de preços, o
  `<p style="page-break-after">` no meio do fluxo ZPL (lixo enviado para a
  impressora), o `PyPDF2` (substituído pelo `merge_pdf` do próprio Odoo) e o
  `print_label_type` fora de qualquer vista.
    """,
    'depends': ['product', 'stock'],
    'data': [
        'report/pg_etiqueta_a5_templates.xml',
        'report/pg_etiqueta_5x8_templates.xml',
        'report/pg_etiqueta_zpl_templates.xml',
        'report/pg_etiquetas_reports.xml',
        'views/product_views.xml',
        'views/stock_picking_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
}
