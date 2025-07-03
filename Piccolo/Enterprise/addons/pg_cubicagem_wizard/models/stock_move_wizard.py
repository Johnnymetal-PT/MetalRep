from odoo import models, fields, api

class StockMoveCubicagemWizard(models.TransientModel):
    _name = 'stock.move.cubicagem.wizard'
    _description = 'Cubicagem Calculation Wizard'

    move_id = fields.Many2one('stock.move', required=True)

    volumes = fields.Float(string="Volumes")

    comprimento_1 = fields.Float()
    altura_1 = fields.Float()
    largura_1 = fields.Float()
    comprimento_2 = fields.Float()
    altura_2 = fields.Float()
    largura_2 = fields.Float()
    comprimento_3 = fields.Float()
    altura_3 = fields.Float()
    largura_3 = fields.Float()
    comprimento_4 = fields.Float()
    altura_4 = fields.Float()
    largura_4 = fields.Float()
    comprimento_5 = fields.Float()
    altura_5 = fields.Float()
    largura_5 = fields.Float()
    comprimento_6 = fields.Float()
    altura_6 = fields.Float()
    largura_6 = fields.Float()

    cubicagem = fields.Float(string="Cubicagem", compute="_compute_cubicagem_and_peso", store=False)
    peso_kg = fields.Float(string="Peso (Kg)", compute="_compute_cubicagem_and_peso", store=False)

    @api.depends(
        'comprimento_1', 'altura_1', 'largura_1',
        'comprimento_2', 'altura_2', 'largura_2',
        'comprimento_3', 'altura_3', 'largura_3',
        'comprimento_4', 'altura_4', 'largura_4',
        'comprimento_5', 'altura_5', 'largura_5',
        'comprimento_6', 'altura_6', 'largura_6',
    )
    def _compute_cubicagem_and_peso(self):
        for rec in self:
            cubicagem = (
                (rec.comprimento_1 or 0) * (rec.altura_1 or 0) * (rec.largura_1 or 0) +
                (rec.comprimento_2 or 0) * (rec.altura_2 or 0) * (rec.largura_2 or 0) +
                (rec.comprimento_3 or 0) * (rec.altura_3 or 0) * (rec.largura_3 or 0) +
                (rec.comprimento_4 or 0) * (rec.altura_4 or 0) * (rec.largura_4 or 0) +
                (rec.comprimento_5 or 0) * (rec.altura_5 or 0) * (rec.largura_5 or 0) +
                (rec.comprimento_6 or 0) * (rec.altura_6 or 0) * (rec.largura_6 or 0)
            )
            rec.cubicagem = cubicagem
            rec.peso_kg = cubicagem * 80

    def action_calculate(self):
        self.ensure_one()

        move = self.move_id
        qty = move.product_uom_qty or 0
        volume_per_unit = self.volumes or 0
        peso_per_unit = self.peso_kg or 0
        cubicagem_per_unit = self.cubicagem or 0

        # 🧮 Calculate required number of boxes
        if volume_per_unit > 0:
            required_boxes = qty / (1 / volume_per_unit)
            required_boxes = int(required_boxes) + (1 if required_boxes % 1 > 0 else 0)
        else:
            required_boxes = 0

        # 🧮 Total peso and cubicagem
        total_peso = peso_per_unit * qty
        total_cubicagem = cubicagem_per_unit * qty

        # 🔄 Write values to move
        move.write({
            'x_studio_volumes_3': required_boxes,
            'x_studio_peso_kg_1': total_peso,
            'x_studio_cubicagem_1': total_cubicagem,
        })
