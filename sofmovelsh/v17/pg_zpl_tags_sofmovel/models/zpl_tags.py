"""Impressao ZPL via CUPS (abordagem anterior ao PG_Etiquetas_A5).

[POSSIVELMENTE OBSOLETO] Pertence ao modulo `pg_zpl_tags_sofmovel`. Substituto
recomendado: `PG_Etiquetas_A5` (envia ZPL via IoT Box). Manter so se houver
ainda dependencia da impressora CUPS chamada "Etiquetas" no servidor.
"""
from odoo import models
import subprocess
import os

class ProductProduct(models.Model):
    """Adiciona impressao ZPL via CUPS a `product.product`."""

    _inherit = 'product.product'

    def action_print_zpl_label(self):
        """Renderiza, guarda em /tmp e imprime ZPL pela impressora 'Etiquetas'.

        Depende de CUPS no host e da impressora chamada exatamente "Etiquetas".
        O ficheiro fica em `/tmp/etiqueta_<id>.zpl` com chmod 0o777 para
        permitir leitura pelo daemon CUPS independentemente do user do Odoo.
        """
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

