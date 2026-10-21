import os
import base64
import unicodedata
import cups
import tempfile
import socket
import requests
from io import BytesIO
from PIL import Image
from odoo import tools
from odoo import models, fields
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    # Boolean field to enable/disable ZPL printing
    enable_zpl_printing2 = fields.Boolean(
        string="Print ZPL Label",
        default=True,  # Set to True by default if you want all pickings to have this option
    )

    def action_print_zpl2(self, label_size):
        """Generates ZPL label dynamically based on the selected label size"""

        all_labels = []  # List to store ZPL codes for each product

        for move in self.move_ids_without_package:
            for move_line in move.move_line_ids:
                product = move_line.product_id
                qty = int(move_line.quantity or 1)
                volume = int(move.x_studio_volumes_3 or 1)

                # Fetch the main product name (ignoring variant details)
                main_product_name = move.product_id.product_tmpl_id.name or ""

                # Generate the ZPL label with dynamic data
                zpl_templates = {
                    'produtos': f"""
^XA
^CI28
^PW400
^LH0,10
^FO0,10^GFA,1440,1440,32,,:::L07IFE,L07JFC,L07JFE,L07I01E,L07I01E03801IFE003IFC007IFE0038J03JF,L07I01E03803JF007IFE00KF0038J0KF8,L07I01E038038003807I0E01EI038038J0EI018,L07I01E038038003807I0E01CI038038J0EI01C,:L078007E038038K07,L07JFC038038K07,L07JF8038038K07,L078K038038K07,L07L038038K07,:L07L038038003807I0E01CI038038J0EI01C,::L07L03803JF807IFE01KF803IFC0KF8,L07L03803JF007IFE00KF003IFE07JF8,,::L0TF8S03SFC,::,::::::::::::::^FS

^FO70,50^A0N,5,5^FDSoluções em estofo^FS

^FO0,80^A0N,20,25^FDCliente^FS
^FO0,105^A0N,25,25^FD{self.x_studio_cliente_1 or ''} | {self.x_studio_sale_order_name or ''}^FS
^FO1,106^A0N,25,25^FD{self.x_studio_cliente_1 or ''} | {self.x_studio_sale_order_name or ''}^FS
^FO0,140^A0N,20,25^FDReferência^FS
^FO0,165^A0N,25,25^FD{self.x_studio_referncia_do_cliente_2 or ''}^FS
^FO1,166^A0N,25,25^FD{self.x_studio_referncia_do_cliente_2 or ''}^FS
^XZ
""",
                    'jdias': f"""
^XA
^CI28
^PW400
^LH0,10
^FO0,10^GFA,1440,1440,32,,:::L07IFE,L07JFC,L07JFE,L07I01E,L07I01E03801IFE003IFC007IFE0038J03JF,L07I01E03803JF007IFE00KF0038J0KF8,L07I01E038038003807I0E01EI038038J0EI018,L07I01E038038003807I0E01CI038038J0EI01C,:L078007E038038K07,L07JFC038038K07,L07JF8038038K07,L078K038038K07,L07L038038K07,:L07L038038003807I0E01CI038038J0EI01C,::L07L03803JF807IFE01KF803IFC0KF8,L07L03803JF007IFE00KF003IFE07JF8,,::L0TF8S03SFC,::,::::::::::::::^FS

^FO70,45^A0N,5,5^FDSoluções em estofo^FS

^FO0,80^A0N,20,25^FDCliente^FS
^FO0,105^A0N,25,25^FD{self.partner_id.name or ''}^FS
^FO1,106^A0N,25,25^FD{self.partner_id.name or ''}^FS
^FO0,140^A0N,20,25^FDReferência^FS
^FO0,165^A0N,25,25^FD{self.x_studio_referncia_do_cliente or ''} {self.x_studio_referncia_2 or ''}^FS
^FO1,166^A0N,25,25^FD{self.x_studio_referncia_do_cliente or ''} {self.x_studio_referncia_2 or ''}^FS
^XZ
""",
                    'acabamento': f"""
^XA
^CI28
^PW400
^LH0,10
^FO0,10^GFA,1440,1440,32,,:::L07IFE,L07JFC,L07JFE,L07I01E,L07I01E03801IFE003IFC007IFE0038J03JF,L07I01E03803JF007IFE00KF0038J0KF8,L07I01E038038003807I0E01EI038038J0EI018,L07I01E038038003807I0E01CI038038J0EI01C,:L078007E038038K07,L07JFC038038K07,L07JF8038038K07,L078K038038K07,L07L038038K07,:L07L038038003807I0E01CI038038J0EI01C,::L07L03803JF807IFE01KF803IFC0KF8,L07L03803JF007IFE00KF003IFE07JF8,,::L0TF8S03SFC,::,::::::::::::::^FS

^FO70,50^A0N,5,5^FDSoluções em estofo^FS

^FO0,80^A0N,20,25^FDCliente^FS
^FO75,76^A0N,25,25^FD{self.partner_id.name or ''}^FS
^FO76,77^A0N,25,25^FD{self.partner_id.name or ''}^FS
^FO0,110^A0N,20,25^FDReferência^FS
^FO110,106^A0N,25,25^FD{self.x_studio_referncia_do_cliente or ''}^FS
^FO111,107^A0N,25,25^FD{self.x_studio_referncia_do_cliente or ''}^FS
^FO0,140^A0N,20,25^FDCor^FS
^FO40,136^A0N,25,25^FD{move.x_studio_cor or ''}^FS
^FO41,137^A0N,25,25^FD{move.x_studio_cor or ''}^FS
^FO0,170^A0N,20,25^FDModelo^FS
^FO80,166^A0N,25,25^FD{int(move.product_uom_qty or 0)}UN | {main_product_name}^FS
^FO81,167^A0N,25,25^FD{int(move.product_uom_qty or 0)}UN | {main_product_name}^FS
^XZ
"""
                }

                zpl_code = zpl_templates.get(label_size, zpl_templates['produtos'])

                # Append label multiple times based on volume
                for i in range(volume):
                    all_labels.append(zpl_code)

        full_zpl_code = "\n".join(all_labels)
        return self._send_to_printer2(full_zpl_code)

    def _send_to_printer2(self, zpl_code):
        """Writes ZPL to a file and sends it to the printer"""
        PRINTER_NAME = "ZEBRAP"
        temp_file_path = "/tmp/zpl_print_job2.zpl"

        try:
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(zpl_code)

            conn = cups.Connection()
            printers = conn.getPrinters()

            if PRINTER_NAME not in printers:
                raise UserError(f"Printer '{PRINTER_NAME}' not found on the network.")

            job_id = conn.printFile(PRINTER_NAME, temp_file_path, "ZPL Print Job", {"raw": "true"})
            print(f"Print job {job_id} sent successfully to {PRINTER_NAME}")

        except cups.IPPError as e:
            raise UserError(f"Printing error: {e}")
        except Exception as e:
            raise UserError(f"Unexpected error: {e}")
        finally:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return {'type': 'ir.actions.client', 'tag': 'reload'}
        
    def action_open_zpl_wizard(self):
        """ Opens the pop-up wizard to choose label size """
        return {
            'name': 'Choose Label Size',
            'type': 'ir.actions.act_window',
            'res_model': 'zpl.label.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('pg_zpl_tags_2.view_zpl_label_wizard').id, 'form')],
            'target': 'new',
            'context': {'default_label_size': 'produtos', 'active_id': self.id}
        }
        
