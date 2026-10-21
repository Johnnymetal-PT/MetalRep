{
    'name': 'PG - Câmbio por Data de Criação (Faturas de Fornecedor)',
    'version': '19.0.2.0.0',
    'summary': "Nas faturas/notas de fornecedor, calcula a taxa de câmbio a partir de uma "
               "'Data de Criação' dedicada, em vez da data da fatura.",
    'description': """
Câmbio de Faturas de Fornecedor por Data de Criação
===================================================

Para quem lê isto pela primeira vez
------------------------------------
Este módulo resolve um caso específico de contabilidade multi-moeda: permitir
que a **taxa de câmbio** de uma fatura de fornecedor seja determinada por uma
data de controlo interno (a "Data de Criação") e não pela data da fatura do
fornecedor.

Comportamento standard do Odoo
------------------------------
No Odoo, a taxa de câmbio de um documento (campo *Currency Rate*,
`account.move.invoice_currency_rate`) é obtida com base na **data da fatura**
(`invoice_date`). Não existe, por configuração, forma de a basear noutra data.

O que este módulo faz
---------------------
* Adiciona o campo **Data de Criação** (`pg_data_criacao`) às faturas e notas
  de crédito de fornecedor.
* Quando esse campo está preenchido, a taxa de câmbio passa a ser obtida nessa
  data.
* Quando está vazio, **nada muda**: mantém-se o comportamento standard
  (`invoice_date`).
* Aplica-se **apenas** a documentos de fornecedor (`in_invoice`, `in_refund`).
  Vendas e outros documentos ficam intactos.

Como funciona (técnico)
-----------------------
Faz override do hook standard
`account.move._get_invoice_currency_rate_date()`, que é o ponto único onde o
Odoo decide qual a data usada para a taxa. É exatamente o mesmo padrão que o
próprio Odoo usa no módulo `l10n_cz`. Os detalhes (incluindo a "armadilha do
`@api.depends`" ao estender os computes) estão documentados no topo de
`models/account_move.py`.

Instalação
----------
Instalar o módulo a partir de Apps. Não requer qualquer configuração própria.

Guia de utilização
-------------------
Pré-requisitos:
* Modo multi-moeda ativo (Contabilidade > Configuração > Definições).
* Taxas de câmbio (`res.currency.rate`) carregadas para as datas relevantes,
  manualmente ou via atualização automática. Se não existir taxa exatamente na
  data escolhida, o Odoo usa a taxa mais próxima anterior disponível
  (comportamento standard).

Passo a passo:
1. Abrir ou criar uma fatura / nota de crédito de fornecedor **em rascunho**,
   numa moeda diferente da moeda da empresa.
2. No cabeçalho, no grupo de datas (junto à *Bill Date*), preencher o campo
   **Data de Criação** com a data cujo câmbio se pretende aplicar.
3. O campo *Currency Rate* recalcula automaticamente para a taxa em vigor nessa
   data.
4. Para reverter ao comportamento standard, apagar a **Data de Criação**: a
   taxa volta a basear-se na *Bill Date*.
5. Validar / lançar a fatura normalmente. A Data de Criação não altera a data
   contabilística nem os prazos de pagamento — só o câmbio.

Exemplo prático:
* Empresa em EUR; fatura de fornecedor em USD.
* *Bill Date* = 20/01 (câmbio do dia: 1 EUR = 1,10 USD).
* *Data de Criação* = 10/01 (câmbio do dia: 1 EUR = 1,05 USD).
* Sem o módulo (ou com a Data de Criação vazia): a fatura usaria a taxa de
  20/01 (1,10).
* Com a Data de Criação preenchida: a fatura usa a taxa de 10/01 (1,05).

Perguntas frequentes / resolução de problemas:
* "Não vejo o campo Data de Criação." -> Só aparece em faturas e notas de
  crédito de fornecedor. Confirme o tipo de documento.
* "O campo está a cinzento e não o consigo editar." -> Só é editável com o
  documento em rascunho.
* "Preenchi a Data de Criação mas a taxa não mudou." -> Causas possíveis:
  (a) não existe taxa configurada para a moeda em datas até à data escolhida;
  (b) a taxa dessa data é igual à que já estava aplicada;
  (c) a taxa foi fixada manualmente — ver ponto seguinte.
* "Quero fixar uma taxa manual." -> Pode editar diretamente o *Currency Rate*
  (em rascunho). Atenção: alterar a seguir a *Data de Criação* (ou a *Bill
  Date*) volta a recalcular a taxa automaticamente, sobrepondo-se ao valor
  manual. Defina a taxa manual **depois** de fixar as datas. Junto ao campo
  existe ainda um botão para repor a taxa calculada.
* "A Data de Criação afeta a contabilidade?" -> Não. Afeta apenas a taxa de
  câmbio; a data contabilística (*Accounting Date*) e os prazos seguem a
  *Bill Date*.

Manutenção / upgrade
--------------------
Em upgrades de versão do Odoo, validar a lista `PG_RATE_DEPENDS` em
`models/account_move.py` contra as dependências standard dos métodos
`_compute_expected_currency_rate` / `_compute_invoice_currency_rate` do core.

Estado: ATIVO.

Referências (Odoo 19.0)
-----------------------
* addons/account/models/account_move.py — campo invoice_currency_rate,
  _get_invoice_currency_rate_date e computes da taxa.
* addons/l10n_cz/models/account_move.py — precedente standard do mesmo padrão.
""",
    'category': 'Accounting/Accounting',
    'author': 'Parametro Global',
    'website': 'https://parametro.global',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
}
