import logging
import unicodedata

from odoo import models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _zpl_clean_text(self, value):
        """Return ZPL-safe ASCII text with normalized whitespace."""
        if isinstance(value, bytes):
            text = value.decode('utf-8', errors='ignore')
        else:
            text = '' if value is None else str(value)

        text = unicodedata.normalize('NFKD', text)
        text = text.encode('ascii', 'ignore').decode('ascii')
        text = text.replace('\r', ' ').replace('\n', ' ')
        text = text.replace('^', ' ').replace('~', ' ')
        return ' '.join(text.split()).strip()

    def _zpl_wrap_text(self, values, line_length=58, max_lines=5):
        """Wrap one or more text fragments into ZPL-friendly lines."""
        if isinstance(values, (str, bytes)):
            values = [values]
        values = values or []

        line_length = max(int(line_length or 0), 1)
        max_lines = max(int(max_lines or 0), 1)
        wrapped_lines = []
        overflow = False

        def push(line):
            nonlocal overflow
            if not line:
                return True
            if len(wrapped_lines) >= max_lines:
                overflow = True
                return False
            wrapped_lines.append(line[:line_length])
            return True

        for value in values:
            cleaned = self._zpl_clean_text(value)
            if not cleaned:
                continue

            current_line = ''
            for word in cleaned.split():
                while len(word) > line_length:
                    if current_line:
                        if not push(current_line):
                            break
                        current_line = ''
                    if not push(word[:line_length]):
                        break
                    word = word[line_length:]
                if overflow:
                    break

                tentative_line = f"{current_line} {word}".strip()
                if len(tentative_line) <= line_length:
                    current_line = tentative_line
                else:
                    if not push(current_line):
                        break
                    current_line = word

            if overflow:
                break
            if current_line and not push(current_line):
                break

        if not wrapped_lines:
            return ['---']

        if overflow:
            wrapped_lines = wrapped_lines[:max_lines]
            base = wrapped_lines[-1][:max(line_length - 3, 0)].rstrip()
            wrapped_lines[-1] = f"{base}..." if base else "..."

        return wrapped_lines

    # Button: Imprimir Entregas
    def action_print_zpl_entrega(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escolher Impressora Etiqueta Entrega',
            'res_model': 'choose.iot.printer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_label_type': 'Entrega',
            }
        }

    # Button: Imprimir Tecidos
    def action_print_zpl_tecido(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Escolher Impressora Etiqueta Tecido',
            'res_model': 'choose.iot.printer.wizard_tecido',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_picking_id': self.id,
                'default_label_type': 'Tecido',
            }
        }
