from odoo import models, api

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Auto-preencher lotes vazios antes de validar"""
        # Só para recebimentos
        if self.picking_type_code == 'incoming':
            for line in self.move_line_ids:
                # Se produto tem rastreamento e não tem lote
                if line.product_id.tracking != 'none' and not line.lot_id and not line.lot_name:
                    # Definir nome padrão
                    if line.product_id.tracking == 'lot':
                        line.lot_name = 'SEM-LOTE'
                    elif line.product_id.tracking == 'serial':
                        line.lot_name = 'AUTO-SERIAL'

        # Chamar o método original
        return super().button_validate()