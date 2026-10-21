"""Campos x_studio_* na BD destino para alinhar com a BD origem.

O ``pg_bd_connection`` (instalado na BD origem PICCOLO) escreve em
campos Studio na BD destino (PICCOLO_COMMUNITY) ao replicar guias,
faturas e pagamentos. Esses campos so existem na BD origem; este
modulo cria-os via codigo na BD destino para que o sync nao falhe.

NOMES com typos sao **intencionais** - sao espelhos literais dos
nomes Studio na BD origem. NAO renomear sem migration coordenada nos
dois lados.
"""
from odoo import models, fields


class StockMove(models.Model):
    _inherit = "stock.move"

    # Espelhos dos campos Studio em PICCOLO.stock.move usados pelo
    # ``pg_cubicagem_wizard`` e replicados pelo ``pg_bd_connection``.
    x_studio_volumes_3 = fields.Integer(string="Volumes")
    x_studio_peso_kg_1 = fields.Float(string="Peso (Kg)")
    x_studio_cubicagem_1 = fields.Float(string="Cubicagem")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # "Zona" usada para repartir guias por zona logistica em PICCOLO;
    # replicada para PICCOLO_COMMUNITY para nao perder a informacao.
    x_studio_zona = fields.Many2one("res.country.state", string="Zona")


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Typo 'observaes' (deveria ser 'observacoes') herdado do nome do
    # campo Studio em PICCOLO. MANTER literal - o matching no sync e
    # feito por nome de campo exato.
    x_studio_observaes_no_recibo = fields.Char(
        string="Observacoes No Recibo",
    )
