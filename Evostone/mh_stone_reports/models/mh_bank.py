from odoo import fields, models


class MhBank(models.Model):
    _name = 'mh.bank'
    _description = 'Bancos da Empresa'
    _order = 'sequence, id'

    name = fields.Char(string='Banco', required=True, help='Nome do banco (ex: BCI, BIM, MOZA)')
    nib = fields.Char(string='NIB', help='Número de Identificação Bancária')
    account_number = fields.Char(string='Nº Conta', help='Número da conta bancária')
    iban = fields.Char(string='IBAN', help='International Bank Account Number')
    swift = fields.Char(string='SWIFT/BIC', help='Código SWIFT ou BIC')
    sequence = fields.Integer(string='Sequência', default=10)
    active = fields.Boolean(string='Activo', default=True)
    company_id = fields.Many2one(
        'res.company', string='Empresa', required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
