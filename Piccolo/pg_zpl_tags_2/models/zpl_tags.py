"""Impressao direta de etiquetas ZPL para Zebra a partir do picking.

A logica e linear:
1. Wizard recolhe o template escolhido pelo utilizador.
2. ``action_print_zpl2`` itera moves/move_lines e monta uma string
   ZPL por (move_line, volume).
3. ``_send_to_printer2`` escreve para ficheiro temp e envia via CUPS
   com flag raw=true para a fila ``ZEBRAP``.

Tudo HARDCODED (nome da impressora, path /tmp/, layout 55x28mm).
Procurar "PRINTER_NAME" e "temp_file_path" abaixo para mover.

Os campos Studio referenciados nas f-strings podem ter typo
intencional herdado de Studio (``referncia`` sem 'e'). MANTER literal.
"""
import os
import cups
from odoo import models, fields
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    enable_zpl_printing2 = fields.Boolean(
        string="Print ZPL Label",
        default=True,
    )

    def action_print_zpl2(self, label_size):
        """Gera ZPL para todas as move_lines do picking e envia para a Zebra.

        Repete cada etiqueta ``volume`` vezes
        (``move.x_studio_volumes_3`` - preenchido pelo
        ``pg_cubicagem_wizard``). Se vazio, considera 1.
        """
        all_labels = []

        for move in self.move_ids_without_package:
            for move_line in move.move_line_ids:
                product = move_line.product_id
                qty = int(move_line.quantity or 1)
                volume = int(move.x_studio_volumes_3 or 1)

                # Nome do template (sem variantes) - aparece em 'acabamento'.
                main_product_name = move.product_id.product_tmpl_id.name or ""

                # Templates ZPL inline. ^PW400 = 55mm a 8 dpmm.
                # Texto duplicado em duas posicoes com offset 1px da
                # impressao "negrito fake" (Zebra firmware basico
                # nem sempre rende ^B0).
                zpl_templates = {
                    'produtos': f"""
^XA
^CI28
^PW400
^LH0,10
^FO0,10^GFA,1440,1440,32,,:::L07IFE,L07JFC,L07JFE,L07I01E,L07I01E03801IFE003IFC007IFE0038J03JF,L07I01E03803JF007IFE00KF0038J0KF8,L07I01E038038003807I0E01EI038038J0EI018,L07I01E038038003807I0E01CI038038J0EI01C,:L078007E038038K07,L07JFC038038K07,L07JF8038038K07,L078K038038K07,L07L038038K07,:L07L038038003807I0E01CI038038J0EI01C,::L07L03803JF807IFE01KF803IFC0KF8,L07L03803JF007IFE00KF003IFE07JF8,,::L0TF8S03SFC,::,::::::::::::::^FS

^FO70,50^A0N,5,5^FDSoluções em estofo^FS

^FO0,80^A0N,20,25^FDCliente^FS
^FO0,105^A0N,25,25^FD{self.x_studio_cliente_1.name or ''}^FS
^FO1,106^A0N,25,25^FD{self.x_studio_cliente_1.name or ''}^FS
^FO0,140^A0N,20,25^FDReferência^FS
^FO0,165^A0N,25,25^FD{self.x_studio_sale_order_name or ''} | {self.x_studio_referncia_do_cliente_2 or ''}^FS
^FO1,166^A0N,25,25^FD{self.x_studio_sale_order_name or ''} | {self.x_studio_referncia_do_cliente_2 or ''}^FS
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
^FO300,10^A0N,20,25^FDQtd^FS
^FO300,35^A0N,35,35^FD{int(move.product_uom_qty or 0)}^FS
^FO345,10^A0N,20,25^FDVol^FS
^FO345,35^A0N,30,30^FD__VOLNUM__^FS
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

                # Default seguro para template invalido: 'produtos'.
                zpl_code = zpl_templates.get(label_size, zpl_templates['produtos'])

                # Uma etiqueta por volume (volume vem de x_studio_volumes_3).
                # A etiqueta 'jdias' mostra DUAS informacoes no topo direito:
                # 'Qtd' (move.product_uom_qty, estatica) e 'Vol' como
                # contador indice/total por etiqueta ("1/3", "2/3", "3/3").
                # O template e f-string avaliada 1x por move, por isso o
                # contador usa o placeholder __VOLNUM__ substituido aqui em
                # cada copia (nos outros templates o replace e no-op).
                for i in range(volume):
                    all_labels.append(zpl_code.replace("__VOLNUM__", f"{i + 1}/{volume}"))

        full_zpl_code = "\n".join(all_labels)
        return self._send_to_printer2(full_zpl_code)

    def _send_to_printer2(self, zpl_code):
        """Envia ZPL para a Zebra via CUPS em modo raw."""
        # HARDCODED: nome da fila CUPS e path do ficheiro temp.
        PRINTER_NAME = "ZEBRAP"
        temp_file_path = "/tmp/zpl_print_job2.zpl"

        try:
            with open(temp_file_path, "w", encoding="utf-8") as temp_file:
                temp_file.write(zpl_code)

            conn = cups.Connection()
            printers = conn.getPrinters()

            if PRINTER_NAME not in printers:
                raise UserError(f"Printer '{PRINTER_NAME}' not found on the network.")

            # raw=true e essencial: o CUPS NAO deve interpretar/converter
            # o ZPL, so empurra os bytes para a impressora.
            job_id = conn.printFile(PRINTER_NAME, temp_file_path, "ZPL Print Job", {"raw": "true"})

        except cups.IPPError as e:
            raise UserError(f"Printing error: {e}")
        except Exception as e:
            raise UserError(f"Unexpected error: {e}")
        finally:
            # Limpar o temp file mesmo em caso de erro.
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_open_zpl_wizard(self):
        """Abre o wizard de escolha de template ZPL."""
        return {
            'name': 'Choose Label Size',
            'type': 'ir.actions.act_window',
            'res_model': 'zpl.label.wizard',
            'view_mode': 'form',
            'views': [(self.env.ref('pg_zpl_tags_2.view_zpl_label_wizard').id, 'form')],
            'target': 'new',
            # Default 'produtos' (Tecidos) - o template mais usado.
            'context': {'default_label_size': 'produtos', 'active_id': self.id},
        }
