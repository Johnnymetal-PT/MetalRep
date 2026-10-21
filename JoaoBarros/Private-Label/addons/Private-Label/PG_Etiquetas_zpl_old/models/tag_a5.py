import logging
import re
import unicodedata

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    last_label_printed_at = fields.Datetime(
        string="Last Labels Printed At",
        readonly=True,
        copy=False,
    )

    def _zpl_clean_text(self, value):
        """Return ZPL-safe UTF-8 text with normalized whitespace."""
        if isinstance(value, bytes):
            text = value.decode('utf-8', errors='ignore')
        else:
            text = '' if value is None else str(value)

        text = unicodedata.normalize('NFC', text)
        text = text.replace('\r', ' ').replace('\n', ' ')
        text = text.replace('^', ' ').replace('~', ' ')
        text = ''.join(ch for ch in text if unicodedata.category(ch)[0] != 'C')
        return ' '.join(text.split()).strip()

    def _zpl_wrap_text(self, values, line_length=58, max_lines=5, break_long_words=True):
        """Wrap one or more text fragments into ZPL-friendly lines."""
        if isinstance(values, (str, bytes)):
            values = [values]
        values = values or []

        line_length = max(int(line_length or 0), 1)
        max_lines = max(int(max_lines or 0), 1)
        break_long_words = bool(break_long_words)
        wrapped_lines = []
        overflow = False

        def push(line):
            nonlocal overflow
            if not line:
                return True
            if len(wrapped_lines) >= max_lines:
                overflow = True
                return False
            wrapped_lines.append(line[:line_length] if break_long_words else line)
            return True

        for value in values:
            cleaned = self._zpl_clean_text(value)
            if not cleaned:
                continue

            current_line = ''
            for word in cleaned.split():
                while break_long_words and len(word) > line_length:
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

    def _zpl_wrap_text_blocks(self, values, line_length=58, max_lines=5, break_long_words=True):
        """Wrap each text fragment as its own block, preserving line breaks between them."""
        if isinstance(values, (str, bytes)):
            values = [values]
        values = values or []

        line_length = max(int(line_length or 0), 1)
        max_lines = max(int(max_lines or 0), 1)
        break_long_words = bool(break_long_words)
        wrapped_lines = []

        for value in values:
            if len(wrapped_lines) >= max_lines:
                break
            if not self._zpl_clean_text(value):
                continue

            block_lines = self._zpl_wrap_text(
                [value],
                line_length=line_length,
                max_lines=max_lines - len(wrapped_lines),
                break_long_words=break_long_words,
            )
            if block_lines == ['---']:
                continue
            wrapped_lines.extend(block_lines)

        return wrapped_lines or ['---']

    def _zpl_stringify_value(self, value):
        if not value:
            return ''
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='ignore')
        if isinstance(value, models.BaseModel):
            if len(value) > 1:
                return ', '.join(
                    part for part in (self._zpl_stringify_value(record) for record in value) if part
                )
            record = value[:1]
            return (
                getattr(record, 'display_name', False)
                or getattr(record, 'name', False)
                or str(record.id)
            )
        if isinstance(value, (list, tuple, set)):
            return ', '.join(
                part for part in (self._zpl_stringify_value(item) for item in value) if part
            )
        return str(value)

    def _zpl_display_value(self, value, default='---'):
        cleaned = self._zpl_clean_text(self._zpl_stringify_value(value))
        return cleaned or default

    def _zpl_format_date(self, value, default='---'):
        if not value:
            return default

        parsed = value
        if isinstance(value, str):
            parsed = fields.Datetime.to_datetime(value) or fields.Date.to_date(value) or value

        if hasattr(parsed, 'strftime'):
            return parsed.strftime('%d/%m/%Y')

        return self._zpl_display_value(value, default=default)

    def _zpl_get_first_move(self):
        self.ensure_one()
        return self.move_ids_without_package[:1] or self.move_ids[:1]

    def _zpl_is_com_fabric_partner(self, partner=False):
        partner_name = self._zpl_clean_text(partner.name if partner else '')
        return partner_name.upper() == 'COM FABRIC SUPPLIED BY THE CLIENT'

    def _zpl_get_purchase_planned_date(self, purchase=False):
        purchase = purchase[:1] if purchase else self.env['purchase.order']
        if not purchase:
            return False
        if 'date_planned' in purchase._fields and purchase.date_planned:
            return purchase.date_planned
        if 'order_line' in purchase._fields:
            planned_dates = [date for date in purchase.order_line.mapped('date_planned') if date]
            if planned_dates:
                return min(planned_dates)
        return getattr(purchase, 'date_order', False)

    def _zpl_get_partner_autofill_values(self):
        self.ensure_one()
        values = {}
        if 'x_studio_com_fabric' in self._fields:
            values['x_studio_com_fabric'] = self._zpl_is_com_fabric_partner(self.partner_id)
        return values

    def _zpl_get_purchase_autofill_values(self):
        self.ensure_one()
        values = {}
        purchase = (
            self.x_studio_ecf_number_1
            if 'x_studio_ecf_number_1' in self._fields
            else self.env['purchase.order']
        )
        if 'x_studio_ecf_date_1' in self._fields:
            values['x_studio_ecf_date_1'] = self._zpl_get_purchase_planned_date(purchase)
        if 'x_studio_supplier' in self._fields:
            values['x_studio_supplier'] = purchase.partner_id.id if purchase else False
        return values

    @api.onchange('partner_id')
    def _onchange_partner_id_zpl_autofill(self):
        for picking in self:
            for field_name, value in picking._zpl_get_partner_autofill_values().items():
                picking[field_name] = value

    @api.onchange('x_studio_ecf_number_1')
    def _onchange_ecf_number_zpl_autofill(self):
        for picking in self:
            for field_name, value in picking._zpl_get_purchase_autofill_values().items():
                picking[field_name] = value

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        if self.env.context.get('skip_zpl_receipt_autofill'):
            return pickings
        for picking, vals in zip(pickings, vals_list):
            updates = {}
            if 'partner_id' in vals:
                updates.update(picking._zpl_get_partner_autofill_values())
            if 'x_studio_ecf_number_1' in vals:
                updates.update(picking._zpl_get_purchase_autofill_values())
            if updates:
                super(StockPicking, picking.with_context(skip_zpl_receipt_autofill=True)).write(updates)
        return pickings

    def write(self, vals):
        result = super().write(vals)
        if self.env.context.get('skip_zpl_receipt_autofill'):
            return result
        tracked_fields = {'partner_id', 'x_studio_ecf_number_1'}
        if tracked_fields.intersection(vals):
            for picking in self:
                updates = {}
                if 'partner_id' in vals:
                    updates.update(picking._zpl_get_partner_autofill_values())
                if 'x_studio_ecf_number_1' in vals:
                    updates.update(picking._zpl_get_purchase_autofill_values())
                if updates:
                    super(StockPicking, picking.with_context(skip_zpl_receipt_autofill=True)).write(updates)
        return result

    def _zpl_get_move_print_count(self, move=False):
        self.ensure_one()
        move = move[:1] if move else self.env['stock.move']
        if not move or 'x_studio_n_de_impresses' not in move._fields:
            return 0
        try:
            return max(int(move.x_studio_n_de_impresses or 0), 0)
        except (TypeError, ValueError):
            return 0

    def _zpl_get_print_moves(self):
        self.ensure_one()
        moves = self.move_ids_without_package or self.move_ids
        return moves.filtered(lambda move: self._zpl_get_move_print_count(move) > 0)

    def _zpl_get_first_production(self, move=False):
        self.ensure_one()
        if 'production_ids' in self._fields and self.production_ids:
            return self.production_ids[:1]
        if (
            'group_id' in self._fields
            and self.group_id
            and 'mrp_production_ids' in self.group_id._fields
            and self.group_id.mrp_production_ids
        ):
            return self.group_id.mrp_production_ids[:1]
        if move and 'move_dest_ids' in move._fields:
            productions = move.move_dest_ids.mapped('raw_material_production_id')
            if productions:
                return productions[:1]
        return self.env['mrp.production']

    def _zpl_is_fabric_line(self, text):
        upper_text = self._zpl_clean_text(text).upper()
        return 'FABRIC' in upper_text or 'TECIDO' in upper_text

    def _zpl_strip_parenthetical_text(self, text):
        cleaned = self._zpl_clean_text(text)
        while True:
            updated = re.sub(r"\s*\([^()]*\)", "", cleaned).strip()
            if updated == cleaned:
                break
            cleaned = updated
        return ' '.join(cleaned.split())

    def _zpl_normalize_fabric_location_pt(self, text):
        cleaned = self._zpl_clean_text(text)
        mappings = [
            ("FABRIC USED IN INTERNAL BACK AND SEAT", "TECIDO USADO NO ENCOSTO E ASSENTO"),
            ("MAIN FABRIC", "TECIDO PRINCIPAL"),
            ("FABRIC USED IN SEAT", "TECIDO USADO NO ASSENTO"),
            ("FABRIC USED IN BOTTOM OF THE SEAT", "TECIDO USADO NA BASE DO ASSENTO"),
            ("PILLOW FABRIC", "TECIDO DA ALMOFADA DECORATIVA"),
            ("FABRIC USED IN SEAT AND ARMREST", "TECIDO USADO NO ASSENTO E BRACOS"),
            ("FABRIC USED IN ARMREST", "TECIDO USADO NOS BRACOS"),
            ("FABRIC USED IN THE STRAP", "TECIDO USADO NAS FIVELAS"),
            ("FABRIC USED IN ROLL", "TECIDO USADO NO ROLO"),
            ("FABRIC USED IN DOUBLE HEADBOARD", "TECIDO USADO NA CABECEIRA DUPLA"),
            ("FABRIC USED IN EXTERNAL BACK", "TECIDO USADO NA COSTA"),
            ("FABRIC USED IN BASE", "TECIDO USADO NA BASE"),
            ("FABRIC USED IN PIPING", "TECIDO USADO NO VIVO"),
            ("FABRIC USED IN SEAT AND CUSHION BACK", "TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA"),
            ("FABRIC USED IN BACK AND ARMREST", "TECIDO USADO NA COSTA E BRACO"),
            ("FABRIC USED IN BACK", "TECIDO USADO NA COSTA"),
            ("FABRIC USED IN BACK AND BOTTOM OF THE SEAT", "TECIDO USADO NA COSTA E BASE DO ASSENTO"),
            ("FABRIC USED IN UNDER SEAT AND OUTER BACK", "TECIDO USADO NO FUNDO DO ASSENTO E COSTA"),
            ("FABRIC USED IN INNER BACK; SEAT AND ARMREST", "TECIDO USADO NO ENCOSTO, ASSENTO E BRACOS"),
            ("FABRIC USED IN SEAT AND BACKREST", "TECIDO USADO NO ASSENTO E ENCOSTO"),
            ("FABRIC USED IN BACKREST", "TECIDO USADO NO ENCOSTO"),
            ("FABRIC USED IN CUSTOM", "TECIDO USADO NO CUSTOM"),
            ("FABRIC USED IN", "TECIDO USADO"),
        ]
        for en_label, pt_label in mappings:
            cleaned = re.sub(
                rf"(?i)^\s*{re.escape(en_label)}\s*:\s*",
                f"{pt_label}: ",
                cleaned,
            )
        cleaned = re.sub(r"(?i)^\s*FABRIC\s*:\s*", "TECIDO: ", cleaned)
        return cleaned

    def _zpl_match_fabric_line(self, fabric_lines, move=False):
        if not fabric_lines:
            return ''

        reference_values = []
        if move and move.product_id:
            reference_values.extend([
                move.product_id.display_name,
                move.product_id.name,
                move.product_id.default_code,
            ])

        cleaned_references = []
        for value in reference_values:
            cleaned_value = self._zpl_strip_parenthetical_text(value)
            cleaned_value = cleaned_value.split(']')[-1].strip()
            if cleaned_value:
                cleaned_references.append(cleaned_value.upper())

        best_line = fabric_lines[0]
        best_score = -1
        for line in fabric_lines:
            line_upper = self._zpl_clean_text(line).upper()
            score = 0
            for reference in cleaned_references:
                if not reference:
                    continue
                if reference in line_upper:
                    score = max(score, 100 + len(reference))
                    continue
                tokens = [token for token in re.split(r"[^A-Z0-9]+", reference) if len(token) > 2]
                score = max(score, sum(1 for token in tokens if token in line_upper))
            if score > best_score:
                best_score = score
                best_line = line

        return self._zpl_normalize_fabric_location_pt(best_line)

    def _zpl_get_tecido_report_values(self, move=False):
        self.ensure_one()

        move = (
            move[:1]
            if move
            else (self._zpl_get_print_moves()[:1] or self._zpl_get_first_move())
        )
        production = self._zpl_get_first_production(move=move)
        sale = (
            ('sale_id' in self._fields and self.sale_id)
            or (
                move
                and 'sale_line_id' in move._fields
                and move.sale_line_id
                and move.sale_line_id.order_id
            )
            or self.env['sale.order']
        )

        product_name_source = (
            (production and (production.product_id.display_name or production.product_id.name))
            or (move and (move.product_id.display_name or move.product_id.name))
            or ''
        )
        product_name_clean = self._zpl_clean_text(product_name_source)
        product_name = product_name_clean.split(']')[-1].strip() if product_name_clean else ''
        product_name = self._zpl_strip_parenthetical_text(product_name)
        qty_text = '%g' % (
            (production and production.product_qty)
            or (move and move.product_uom_qty)
            or 0
        )

        fabric_source = (
            (
                production
                and 'product_description_variants' in production._fields
                and (production.product_description_variants or '')
            )
            or (
                move
                and 'sale_line_id' in move._fields
                and move.sale_line_id
                and move.sale_line_id.name
            )
            or ''
        )
        raw_segments = (
            fabric_source.replace('\r', '\n').replace(', ', '\n').split('\n')
            if fabric_source else []
        )
        fabric_segments = []
        for segment in raw_segments:
            cleaned_segment = self._zpl_clean_text(segment)
            if cleaned_segment:
                fabric_segments.append(cleaned_segment)

        fabric_lines = [
            segment for segment in fabric_segments if self._zpl_is_fabric_line(segment)
        ]
        selected_fabric_line = self._zpl_match_fabric_line(fabric_lines, move=move)

        supplier_value = (
            ('x_studio_supplier' in self._fields and self.x_studio_supplier)
            or self.partner_id
            or False
        )
        ecf_number_value = (
            ('x_studio_ecf_number_1' in self._fields and self.x_studio_ecf_number_1)
            or ('x_studio_ecf_number_2' in self._fields and self.x_studio_ecf_number_2)
            or False
        )
        ecf_date_value = (
            ('x_studio_ecf_date_1' in self._fields and self.x_studio_ecf_date_1)
            or ('x_studio_ecf_date' in self._fields and self.x_studio_ecf_date)
            or False
        )
        client_relations_value = (
            (
                sale
                and 'salesperson_partner_id' in sale._fields
                and sale.salesperson_partner_id
            )
            or ('x_studio_client_relations' in self._fields and self.x_studio_client_relations)
            or (sale and sale.user_id and (sale.user_id.partner_id or sale.user_id))
            or False
        )
        fabric_arrival_date = self._zpl_format_date(
            ('date_done' in self._fields and self.date_done)
            or ('scheduled_date' in self._fields and self.scheduled_date)
            or False
        )
        comments = self._zpl_display_value(
            ('x_studio_nota_1' in self._fields and self.x_studio_nota_1) or ''
        )
        move_note = self._zpl_display_value(
            (move and 'x_studio_notas' in move._fields and move.x_studio_notas) or '',
            default='',
        )
        com_fabric = (
            ('x_studio_com_fabric' in self._fields and bool(self.x_studio_com_fabric))
            or self._zpl_is_com_fabric_partner(self.partner_id)
        )
        description_values = [f"{qty_text} x {product_name or '---'}"]
        if selected_fabric_line:
            description_values.append(selected_fabric_line)
        if move_note:
            description_values.append(move_note)
        description_lines = self._zpl_wrap_text_blocks(
            description_values,
            line_length=90,
            max_lines=8,
            break_long_words=False,
        )
        print_count = self._zpl_get_move_print_count(move)

        return {
            'supplier_name': self._zpl_display_value(supplier_value),
            'ecf_number': self._zpl_display_value(ecf_number_value),
            'ecf_date': self._zpl_format_date(ecf_date_value),
            'fp_number': self._zpl_display_value((sale and sale.name) or self.origin),
            'client_relations': self._zpl_display_value(client_relations_value),
            'description_lines': description_lines,
            'description_text': '\\&'.join(description_lines[:8]) if description_lines else '---',
            'fabric_arrival_date': fabric_arrival_date,
            'comments': comments,
            'com_fabric_mark': 'X' if com_fabric else '',
            'print_count': print_count,
        }

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
