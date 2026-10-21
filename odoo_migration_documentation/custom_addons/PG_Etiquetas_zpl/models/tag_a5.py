"""Integracao de impressao ZPL para transferencias de stock via IoT.

Nota: apesar do nome do ficheiro (`tag_a5.py`), o modelo estendido e
`stock.picking`, com botoes para disparar reports Studio para etiqueta.
"""

import html

from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_print_zpl_label(self):
        # Alias mantido por compatibilidade com botoes antigos.
        return self.action_print_zpl_tecido()

    def action_print_zpl_entrega(self):
        # XML ID fixo do report Studio de etiqueta de entrega.
        return self._print_studio_report('studio_customization.studio_report_docume_03a04fe9-992d-4af4-b03b-1347317aaae0')

    def action_print_zpl_tecido(self):
        # XML ID fixo do report Studio de etiqueta de tecido.
        return self._print_studio_report('studio_customization.studio_report_docume_9d62d515-ae63-44f2-b236-55c8f03b7ac5')

    def _print_studio_report(self, report_name):
        # Encapsula o disparo do report Studio para centralizar validacao
        # de existencia do report + resolucao de impressora IoT.
        report = self.env['ir.actions.report']._get_report_from_name(report_name)
        if not report:
            raise UserError(_("Studio report '%s' was not found.") % report_name)
        printer = self._get_zpl_printer()
        return report.with_context(
            force_print=True,
            lang=self.env.context.get('lang') or self.env.user.lang,
        ).report_action(self, data={'device_id': printer.id})

    def _get_zpl_printer(self):
        # Convencao local: procurar primeiro por nome exato ZEBRA.
        printer = self.env['iot.device'].sudo().search([
            ('name', '=', 'ZEBRA')
        ], limit=1)
        if not printer:
            printer = self.env['iot.device'].sudo().search([
                ('name', 'ilike', 'ZEBRA'),
                ('name', 'ilike', 'ZPL'),
        ], limit=1)
        if not printer:
            raise UserError(_("IoT printer 'ZEBRA' was not found."))
        return printer

    def _zpl_clean_text(self, value, multiline=False):
        # Higienizacao defensiva para dados vindos de campos HTML/char/text.
        text = html.unescape(str(value or ''))
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        if multiline:
            lines = [' '.join(line.split()) for line in text.split('\n')]
            return '\n'.join(line for line in lines if line).strip()
        return ' '.join(text.replace('\n', ' ').split()).strip()

    def _zpl_wrap_text(self, values, width=70, max_lines=4):
        # Wrapper simples para caber texto no layout ZPL sem quebrar o comando.
        if isinstance(values, (list, tuple)):
            source_lines = [self._zpl_clean_text(value) for value in values if self._zpl_clean_text(value)]
        else:
            cleaned = self._zpl_clean_text(values)
            source_lines = [cleaned] if cleaned else []

        wrapped = []
        for source in source_lines:
            current = ''
            for word in source.split():
                candidate = f"{current} {word}".strip()
                if len(candidate) <= width:
                    current = candidate
                    continue
                if current:
                    wrapped.append(current)
                    current = ''
                while len(word) > width:
                    wrapped.append(word[:width])
                    word = word[width:]
                current = word
            if current:
                wrapped.append(current)

        if max_lines and len(wrapped) > max_lines:
            wrapped = wrapped[:max_lines]
        return wrapped
