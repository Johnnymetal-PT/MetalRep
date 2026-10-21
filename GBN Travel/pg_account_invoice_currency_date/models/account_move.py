"""Câmbio de faturas de fornecedor a partir da "Data de Criação".

Objetivo
--------
Em standard, a taxa de câmbio de um documento
(`account.move.invoice_currency_rate`) é obtida com base na *data da fatura*
(`invoice_date`). Este módulo permite que, **apenas em faturas e notas de
crédito de fornecedor**, essa taxa passe a ser obtida com base num campo de
data dedicado — a *Data de Criação* (`pg_data_criacao`) — preenchido pelo
utilizador. Quando a Data de Criação está vazia, nada muda: o documento mantém
o comportamento standard (usa a `invoice_date`).

Como o standard calcula a taxa (cadeia de dependências)
-------------------------------------------------------
No core `account` (Odoo 19.0, addons/account/models/account_move.py):

    invoice_currency_rate                      (campo stored, editável)
      └─ _compute_invoice_currency_rate()      copia expected_currency_rate
    expected_currency_rate                     (campo não-stored)
      └─ _compute_expected_currency_rate()     taxa na data devolvida por...
        └─ _get_invoice_currency_rate_date()   por defeito: invoice_date

O método `_get_invoice_currency_rate_date()` é o **único** ponto que decide
*qual a data* usada para ir buscar a taxa. É um hook desenhado para ser
estendido: o próprio Odoo faz-lhe override no módulo `l10n_cz`
(addons/l10n_cz/models/account_move.py) para usar a `taxable_supply_date`.

O que este módulo altera
------------------------
1. Adiciona o campo `pg_data_criacao` ao `account.move`.
2. Faz override de `_get_invoice_currency_rate_date()` para devolver
   `pg_data_criacao` nas faturas/notas de fornecedor (quando preenchido).
3. Reacrescenta `pg_data_criacao` às dependências (`@api.depends`) dos dois
   computes da taxa, para que a taxa recalcule quando a data muda.

Porque é preciso o passo 3 (armadilha do @api.depends)
------------------------------------------------------
Quando se faz override de um método de compute e se volta a decorá-lo com
`@api.depends(...)`, a nova lista **SUBSTITUI** (não acumula com) a lista
standard. Logo, é obrigatório repetir a lista standard completa e acrescentar
o novo campo — caso contrário perdiam-se as dependências originais e a taxa
deixaria de recalcular corretamente. O `l10n_cz` não precisou deste passo
porque a `taxable_supply_date` já estava na lista standard; o nosso campo não
está, por isso temos de o declarar (ver `PG_RATE_DEPENDS`).
"""

from odoo import api, fields, models

# Tipos de documento de compra a que se aplica a Data de Criação para o câmbio:
# faturas e notas de crédito de fornecedor. (Recibos de compra ficam de fora.)
PG_PURCHASE_DOC_TYPES = ('in_invoice', 'in_refund')

# Lista de dependências standard dos computes da taxa de câmbio em account.move
# (Odoo 19.0), acrescida do nosso campo. Ver a secção "armadilha do @api.depends"
# no docstring do módulo. IMPORTANTE: manter sincronizada com o core em upgrades
# de versão (métodos _compute_expected_currency_rate / _compute_invoice_currency_rate).
PG_RATE_DEPENDS = (
    'currency_id', 'company_currency_id', 'company_id',
    'invoice_date', 'taxable_supply_date',
    'pg_data_criacao',
)


class AccountMove(models.Model):
    """Extensão de `account.move` para redirecionar a base de cálculo do câmbio.

    Ver o docstring do módulo para o panorama completo. Em resumo: adiciona o
    campo `pg_data_criacao` e liga-o ao cálculo da taxa de câmbio das faturas
    de fornecedor através do hook `_get_invoice_currency_rate_date()`.
    """
    _inherit = 'account.move'

    pg_data_criacao = fields.Date(
        string="Data de Criação",
        copy=False,  # cada documento define a sua data; não herdar ao duplicar
        help="Data usada para obter a taxa de câmbio em faturas e notas de "
             "crédito de fornecedor. Se vazia, é usada a data da fatura "
             "(comportamento standard).",
    )

    def _get_invoice_currency_rate_date(self):
        """Devolve a data a usar para ir buscar a taxa de câmbio.

        Hook standard do `account.move`. Aqui é estendido para que, em faturas e
        notas de crédito de fornecedor com `pg_data_criacao` preenchida, a taxa
        seja obtida nessa data. Em qualquer outro caso (vendas, ou campo vazio),
        delega no comportamento standard (que usa `invoice_date`).
        """
        self.ensure_one()
        if self.move_type in PG_PURCHASE_DOC_TYPES and self.pg_data_criacao:
            return self.pg_data_criacao
        return super()._get_invoice_currency_rate_date()

    @api.depends(*PG_RATE_DEPENDS)
    def _compute_expected_currency_rate(self):
        """Taxa esperada (campo não-stored `expected_currency_rate`).

        Mantém a lógica do standard (chamada a super); o único propósito do
        override é estender as dependências com `pg_data_criacao`, para a taxa
        esperada recalcular quando a Data de Criação muda.
        """
        super()._compute_expected_currency_rate()

    @api.depends(*PG_RATE_DEPENDS)
    def _compute_invoice_currency_rate(self):
        """Taxa efetiva (campo stored `invoice_currency_rate`).

        Igual ao método acima: preserva a lógica standard e apenas estende as
        dependências com `pg_data_criacao`.
        """
        super()._compute_invoice_currency_rate()
