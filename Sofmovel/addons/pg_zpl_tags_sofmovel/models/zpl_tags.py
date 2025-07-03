from odoo import models
import subprocess
import os

class ProductProduct(models.Model):
    _inherit = 'product.product'

    def action_print_zpl_label(self):
        """Renderiza, guarda e imprime a etiqueta ZPL no servidor"""
        for product in self:
            zpl = self.env['ir.qweb']._render(
                'stock.label_product_product_view',
                {'product': product}
            )
            if isinstance(zpl, bytes):
                zpl = zpl.decode('utf-8')

            filepath = f"/tmp/etiqueta_{product.id}.zpl"
            with open(filepath, "w") as f:
                f.write(zpl)

            os.chmod(filepath, 0o777)

            # Envia para impressora 'Etiquetas'
            subprocess.run(["lp", "-d", "Etiquetas", filepath], check=True)

