from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockScrapRemediationWizard(models.TransientModel):
    _name = 'stock.scrap.remediation.wizard'
    _description = 'Wizard de Remediação do Scrap'

    scrap_id = fields.Many2one(
        'stock.scrap',
        string='Scrap',
        required=True,
        readonly=True,
    )

    product_form = fields.Selection([
        ('none', 'Nenhum'),
        ('block', 'Bloco'),
        ('slab', 'Placa'),
        ('strip', 'Banda'),
        ('tiles', 'Ladrilhos'),
    ], string='Forma do Produto', readonly=True)

    # Dimensões originais (readonly, para referência)
    original_length = fields.Float(
        string='Comprimento Original',
        digits='Dimensions',
        readonly=True,
    )

    original_width = fields.Float(
        string='Largura Original',
        digits='Dimensions',
        readonly=True,
    )

    original_thickness = fields.Float(
        string='Espessura Original',
        digits='Dimensions',
        readonly=True,
    )

    original_area = fields.Float(
        string='Volume/Área Original',
        digits='Dimensions',
        compute='_compute_original_area',
    )

    # Novas dimensões
    remediation_length = fields.Float(
        string='Novo Comprimento',
        digits='Dimensions',
        required=True,
    )

    remediation_width = fields.Float(
        string='Nova Largura',
        digits='Dimensions',
        required=True,
    )

    remediation_thickness = fields.Float(
        string='Nova Espessura',
        digits='Dimensions',
    )

    remediation_area = fields.Float(
        string='Novo Volume/Área',
        digits='Dimensions',
        compute='_compute_remediation_area',
    )

    @api.depends('original_length', 'original_width', 'original_thickness', 'product_form')
    def _compute_original_area(self):
        for record in self:
            area = record.original_length * record.original_width
            if record.product_form == 'block' and record.original_thickness:
                area *= record.original_thickness
            record.original_area = area

    @api.depends('remediation_length', 'remediation_width', 'remediation_thickness', 'product_form')
    def _compute_remediation_area(self):
        for record in self:
            area = record.remediation_length * record.remediation_width
            if record.product_form == 'block' and record.remediation_thickness:
                area *= record.remediation_thickness
            record.remediation_area = area

    def action_save(self):
        """Guardar dimensões no scrap sem validar"""
        self.ensure_one()
        self._validate_dimensions()
        vals = {
            'remediation_length': self.remediation_length,
            'remediation_width': self.remediation_width,
        }
        if self.product_form == 'block':
            vals['remediation_thickness'] = self.remediation_thickness
        self.scrap_id.write(vals)
        return {'type': 'ir.actions.act_window_close'}

    def action_validate(self):
        """Guardar dimensões e validar o scrap"""
        self.ensure_one()
        self._validate_dimensions()
        vals = {
            'remediation_length': self.remediation_length,
            'remediation_width': self.remediation_width,
        }
        if self.product_form == 'block':
            vals['remediation_thickness'] = self.remediation_thickness
        self.scrap_id.write(vals)
        return self.scrap_id.action_validate()

    def _validate_dimensions(self):
        """Validar que as novas dimensões são válidas"""
        if not self.remediation_length or self.remediation_length <= 0:
            raise UserError(_('O novo comprimento deve ser maior que zero.'))
        if not self.remediation_width or self.remediation_width <= 0:
            raise UserError(_('A nova largura deve ser maior que zero.'))
        if self.remediation_length > self.original_length:
            raise UserError(_(
                'O novo comprimento (%.4f) não pode ser maior que o original (%.4f).',
                self.remediation_length, self.original_length,
            ))
        if self.remediation_width > self.original_width:
            raise UserError(_(
                'A nova largura (%.4f) não pode ser maior que a original (%.4f).',
                self.remediation_width, self.original_width,
            ))
        # Blocos: validar espessura
        if self.product_form == 'block':
            if not self.remediation_thickness or self.remediation_thickness <= 0:
                raise UserError(_('Para blocos, a nova espessura deve ser maior que zero.'))
            if self.remediation_thickness > self.original_thickness:
                raise UserError(_(
                    'A nova espessura (%.4f) não pode ser maior que a original (%.4f).',
                    self.remediation_thickness, self.original_thickness,
                ))
