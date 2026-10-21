"""Higienizacao e ordenacao do texto tecnico nas linhas de venda.

Normaliza etiquetas de tecido, remove ruido (MESMO TECIDO/custom tokens) e
mantem a descricao alinhada com os atributos reais do produto.
"""

import re

from odoo import api, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @staticmethod
    def _normalize_for_compare(value):
        # Normalizacao "semantica": usada para comparar texto funcionalmente
        # equivalente apesar de diferencas de espaco/aspas/acentos.
        if not value:
            return ''
        text = value.lower()
        text = text.replace('\u2019', "'").replace('\u2018', "'")
        text = text.replace('\u201c', '"').replace('\u201d', '"')
        # Keep decimal comma comparisons stable (e.g. "21, 65" == "21,65").
        text = re.sub(r"(?<=\d)\s*,\s*(?=\d)", ",", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _split_parenthesis_items(content):
        if not content:
            return []
        # Split only when a new item starts with a letter; avoid decimal commas.
        parts = re.split(r",\s+(?=[^\W\d_])", content)
        return [p.strip() for p in parts if p and p.strip()]

    @staticmethod
    def _has_dimensions_in_line(text):
        if not text:
            return False
        norm = SaleOrderLine._normalize_for_compare(text)
        if "dimensions" in norm or "custom dimensions" in norm or "dimensoes" in norm or "dimensões" in norm:
            return True
        return bool(re.search(r"\bw\s*\d+.*\bd\s*\d+.*\bh\s*\d+", norm))

    @staticmethod
    def _looks_like_dimensions(value):
        if not value:
            return False
        norm = SaleOrderLine._normalize_for_compare(value)
        if "dimensions" in norm or "custom dimensions" in norm or "dimensoes" in norm or "dimensões" in norm:
            return True
        return bool(re.search(r"\bw\s*\d+.*\bd\s*\d+.*\bh\s*\d+", norm))

    @staticmethod
    def _strip_mesmo_tecido(text):
        if not text:
            return text

        # Escolha intencional:
        # limpar apenas a 1a linha (nome comercial) para nao perder detalhe
        # tecnico nas linhas seguintes.
        lines = text.splitlines()
        if not lines:
            return text

        # Only clean the product name line (first line) and only inside parentheses.
        first_line = lines[0]

        def _clean_paren(match):
            content = match.group(1)
            cleaned = re.sub(
                r"(?i)\s*(?:,|;)?\s*MESMO\s+TECIDO\b(?:\s*[:\-]\s*)?",
                "",
                content,
            )
            cleaned = re.sub(
                r"\s*(?:,|;)?\s*MESMO\b(?:\s*[:\-]\s*)?",
                "",
                cleaned,
            )
            cleaned = re.sub(r"\s*,\s*,", ", ", cleaned)
            cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" ,;:-")
            if not cleaned:
                return ""
            return f"({cleaned})"

        first_line = re.sub(r"\(([^)]*)\)", _clean_paren, first_line)
        first_line = re.sub(r"\s{2,}", " ", first_line).strip()
        first_line = re.sub(r"\s+\)", ")", first_line)
        first_line = re.sub(r"\(\s+\)", "", first_line)

        return "\n".join([first_line] + lines[1:])

    @staticmethod
    def _strip_custom_tokens(text, prefer_pt=False):
        if not text:
            return text

        lines = text.splitlines()
        if not lines:
            return text

        first_line = lines[0]

        def _clean_paren(match):
            content = match.group(1)
            parts = SaleOrderLine._split_parenthesis_items(content)
            parts = [p for p in parts if p.lower() != "custom"]
            cleaned = ", ".join(parts)
            if not cleaned:
                return ""
            return f"({cleaned})"

        first_line = re.sub(r"\(([^)]*)\)", _clean_paren, first_line)
        first_line = re.sub(r"\s{2,}", " ", first_line).strip()
        first_line = re.sub(r"\s+\)", ")", first_line)
        first_line = re.sub(r"\(\s+\)", "", first_line)

        cleaned_lines = [first_line]
        for line in lines[1:]:
            updated = re.sub(r"(?i)\bCUSTOM\s*:\s*", "", line)
            updated = re.sub(r"\s{2,}", " ", updated).strip()
            cleaned_lines.append(updated)

        cleaned_lines = SaleOrderLine._normalize_fabric_lines(cleaned_lines, prefer_pt=prefer_pt)
        return "\n".join(cleaned_lines)

    @staticmethod
    def _has_mesmo_token(text):
        if not text:
            return False
        if re.search(r"(?i)\bMESMO\s+TECIDO\b", text):
            return True
        return bool(re.search(r"\bMESMO\b", text))

    @staticmethod
    def _normalize_fabric_lines(lines, prefer_pt=False):
        if not lines:
            return lines

        label = "TECIDO" if prefer_pt else "FABRIC"
        fabric_prefixes = [
            r"TECIDO USADO NO ENCOSTO E ASSENTO",
            r"TECIDO PRINCIPAL",
            r"TECIDO USADO NO ASSENTO",
            r"TECIDO USADO NA BASE DO ASSENTO",
            r"TECIDO DA ALMOFADA DECORATIVA",
            "TECIDO USADO NO ASSENTO E BRACOS?|TECIDO USADO NO ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?",
            r"TECIDO USADO NAS FIVELAS",
            r"TECIDO USADO NO ROLO",
            r"TECIDO USADO NA CABECEIRA DUPLA",
            r"TECIDO USADO NA BASE",
            "TECIDO USADO NOS BRACOS?|TECIDO USADO NOS BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?",
            r"TECIDO USADO NO VIVO",
            r"TECIDO USADO NA COSTA",
            r"TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA",
            "TECIDO USADO NA COSTA E BRACO|TECIDO USADO NA COSTA E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O",
            r"TECIDO USADO NA COSTA E BASE DO ASSENTO",
            "TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRACOS?|TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?",
            r"TECIDO USADO NO ASSENTO E ENCOSTO",
            r"TECIDO USADO NO ENCOSTO",
            r"TECIDO USADO NO FUNDO DO ASSENTO E COSTA",
            r"TECIDO USADO",
            r"TECIDO",
            r"FABRIC USED IN INTERNAL BACK AND SEAT",
            r"MAIN FABRIC",
            r"FABRIC USED IN SEAT",
            r"FABRIC USED IN BOTTOM OF THE SEAT",
            r"PILLOW FABRIC",
            r"FABRIC USED IN SEAT AND ARMREST",
            r"FABRIC USED IN ARMREST",
            r"FABRIC USED IN THE STRAP",
            r"FABRIC USED IN ROLL",
            r"FABRIC USED IN DOUBLE HEADBOARD",
            r"FABRIC USED IN EXTERNAL BACK",
            r"FABRIC USED IN BASE",
            r"FABRIC USED IN PIPING",
            r"FABRIC USED IN SEAT AND CUSHION BACK",
            r"FABRIC USED IN BACK AND ARMREST",
            r"FABRIC USED IN BACK",
            r"FABRIC USED IN BACK AND BOTTOM OF THE SEAT",
            r"FABRIC USED IN UNDER SEAT AND OUTER BACK",
            r"FABRIC USED IN INNER BACK; SEAT AND ARMREST",
            r"FABRIC USED IN SEAT AND BACKREST",
            r"FABRIC USED IN BACKREST",
            r"FABRIC USED IN CUSTOM",
            r"FABRIC USED IN",
        ]
        fabric_prefix_re = re.compile(rf"^\s*({'|'.join(fabric_prefixes)})\s*:\s*(.+)$", re.IGNORECASE)

        fabric_lines = []
        non_fabric_lines = []
        for line in lines[1:]:
            if fabric_prefix_re.search(line) or re.search(r"(?i)\b(fabric|tecido)\b", line):
                fabric_lines.append(line)
            else:
                non_fabric_lines.append(line)

        if not fabric_lines:
            return lines

        has_mesmo = any(SaleOrderLine._has_mesmo_token(line) for line in fabric_lines)
        # So normalizamos quando "MESMO" aparece; caso contrario preservamos
        # estrutura original para minimizar alteracoes de texto.
        if not has_mesmo:
            return lines

        donor_value = ""
        for line in fabric_lines:
            if SaleOrderLine._has_mesmo_token(line):
                continue
            match = fabric_prefix_re.match(line.strip())
            if match:
                value = match.group(2).strip()
            elif ":" in line:
                value = line.split(":", 1)[1].strip()
            else:
                value = ""
            if value:
                donor_value = value
                break

        if not donor_value:
            return lines

        normalized = [lines[0]]
        normalized.append(f"{label}: {donor_value}")
        normalized.extend(non_fabric_lines)
        return normalized

    @staticmethod
    def _normalize_fabric_labels(text, prefer_pt=False):
        if not text:
            return text

        label = "TECIDO" if prefer_pt else "FABRIC"
        en_to_pt = [
            ("FABRIC USED IN INTERNAL BACK AND SEAT", "TECIDO USADO NO ENCOSTO E ASSENTO", "TECIDO USADO NO ENCOSTO E ASSENTO"),
            ("MAIN FABRIC", "TECIDO PRINCIPAL", "TECIDO PRINCIPAL"),
            ("FABRIC USED IN SEAT", "TECIDO USADO NO ASSENTO", "TECIDO USADO NO ASSENTO"),
            ("FABRIC USED IN BOTTOM OF THE SEAT", "TECIDO USADO NA BASE DO ASSENTO", r"TECIDO USADO NA BASE DO ASSENTO|TECIDO USADO NO FUNDO DO ASSENTO"),
            ("PILLOW FABRIC", "TECIDO DA ALMOFADA DECORATIVA", r"TECIDO DA ALMOFADA DECORATIVA|TECIDO(?:\s+DA)?\s+ALMOFADA"),
            ("FABRIC USED IN SEAT AND ARMREST", "TECIDO USADO NO ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS", "TECIDO USADO NO ASSENTO E BRACOS?|TECIDO USADO NO ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?"),
            ("FABRIC USED IN ARMREST", "TECIDO USADO NOS BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS", "TECIDO USADO NOS BRACOS?|TECIDO USADO NOS BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?|TECIDO USADO NO BRACO|TECIDO USADO NO BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O"),
            ("FABRIC USED IN THE STRAP", "TECIDO USADO NAS FIVELAS", r"TECIDO USADO NAS FIVELAS|TECIDO USADO NA TIRA"),
            ("FABRIC USED IN ROLL", "TECIDO USADO NO ROLO", "TECIDO USADO NO ROLO"),
            ("FABRIC USED IN DOUBLE HEADBOARD", "TECIDO USADO NA CABECEIRA DUPLA", "TECIDO USADO NA CABECEIRA DUPLA"),
            ("FABRIC USED IN EXTERNAL BACK", "TECIDO USADO NA COSTA", "TECIDO USADO NA COSTA"),
            ("FABRIC USED IN BASE", "TECIDO USADO NA BASE", "TECIDO USADO NA BASE"),
            ("FABRIC USED IN PIPING", "TECIDO USADO NO VIVO", "TECIDO USADO NO VIVO"),
            ("FABRIC USED IN SEAT AND CUSHION BACK", "TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA", r"TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA|TECIDO USADO NO ASSENTO E ALMOFADA DO ENCOSTO"),
            ("FABRIC USED IN BACK AND ARMREST", "TECIDO USADO NA COSTA E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O", "TECIDO USADO NA COSTA E BRACO|TECIDO USADO NA COSTA E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O|TECIDO USADO NO ENCOSTO E BRACO|TECIDO USADO NO ENCOSTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O"),
            ("FABRIC USED IN BACK", "TECIDO USADO NA COSTA", r"TECIDO USADO NA COSTA|TECIDO USADO NO ENCOSTO"),
            ("FABRIC USED IN BACK AND BOTTOM OF THE SEAT", "TECIDO USADO NA COSTA E BASE DO ASSENTO", r"TECIDO USADO NA COSTA E BASE DO ASSENTO|TECIDO USADO NO ENCOSTO E FUNDO DO ASSENTO"),
            ("FABRIC USED IN UNDER SEAT AND OUTER BACK", "TECIDO USADO NO FUNDO DO ASSENTO E COSTA", "TECIDO USADO NO FUNDO DO ASSENTO E COSTA"),
            ("FABRIC USED IN INNER BACK; SEAT AND ARMREST", "TECIDO USADO NO ENCOSTO, ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS", "TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRACOS?|TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?|TECIDO USADO NO ENCOSTO INTERIOR;\\s*ASSENTO E BRACO|TECIDO USADO NO ENCOSTO INTERIOR;\\s*ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O"),
            ("FABRIC USED IN SEAT AND BACKREST", "TECIDO USADO NO ASSENTO E ENCOSTO", "TECIDO USADO NO ASSENTO E ENCOSTO"),
            ("FABRIC USED IN BACKREST", "TECIDO USADO NO ENCOSTO", "TECIDO USADO NO ENCOSTO"),
            ("FABRIC USED IN CUSTOM", "TECIDO USADO NO CUSTOM", "TECIDO USADO NO CUSTOM"),
            ("FABRIC USED IN", "TECIDO USADO", "TECIDO USADO"),
        ]

        if prefer_pt:
            for en_label, pt_label, _pt_pattern in en_to_pt:
                text = re.sub(rf"(?mi)^(\s*){en_label}\s*:\s*", rf"\1{pt_label}: ", text)
        else:
            for en_label, _pt_label, pt_pattern in en_to_pt:
                text = re.sub(rf"(?mi)^(\s*){pt_pattern}\s*:\s*", rf"\1{en_label}: ", text)

        return re.sub(r"(?mi)^(\s*)(?:FABRIC|TECIDO)\s*:\s*", rf"\1{label}: ", text)

    @staticmethod
    def _prefer_pt_labels_for_partner(partner, context_lang=None):
        lang = (partner and partner.lang) or (context_lang or "")
        lang = (lang or "").lower()
        if lang.startswith("pt"):
            return True
        country_code = (partner and partner.country_id and partner.country_id.code) or ""
        return country_code.upper() == "PT"

    def _prefer_pt_labels(self):
        partner = self.order_id and self.order_id.partner_id
        return self._prefer_pt_labels_for_partner(partner, self.env.context.get("lang"))

    @classmethod
    def _normalized_label_variants(cls, label):
        raw = (label or '').strip()
        if not raw:
            return set()

        variants = {cls._normalize_for_compare(raw).strip(':')}
        for prefer_pt in (False, True):
            normalized_line = cls._normalize_fabric_labels(f"{raw}: __pg__", prefer_pt=prefer_pt)
            normalized_label = normalized_line.split(':', 1)[0]
            variants.add(cls._normalize_for_compare(normalized_label).strip(':'))

        return {item for item in variants if item}

    def _get_custom_line_attribute_index(self, line_text, attr_order):
        if not line_text or ':' not in line_text:
            return None

        raw_label = line_text.split(':', 1)[0].strip()
        candidates = set(self._normalized_label_variants(raw_label))
        norm_label = self._normalize_for_compare(raw_label)
        if 'dimensions' in norm_label or 'dimensoes' in norm_label or 'dimensÃµes' in norm_label:
            candidates.update({'dimensions', 'custom dimensions', 'dimensoes', 'dimensÃµes'})

        for candidate in candidates:
            if candidate in attr_order:
                return attr_order[candidate]

        for candidate in candidates:
            for attr_label, idx in attr_order.items():
                if not attr_label:
                    continue
                if candidate == attr_label or candidate.endswith(attr_label) or attr_label in candidate:
                    return idx

        return None

    def _order_custom_lines_by_attribute(self, name):
        if not name:
            return name

        lines = name.splitlines()
        if len(lines) <= 1:
            return name

        tmpl = self.product_template_id or (self.product_id and self.product_id.product_tmpl_id)
        if not tmpl:
            return name

        attr_order = {}
        for idx, attr_line in enumerate(tmpl.attribute_line_ids):
            attr_name = (attr_line.attribute_id.name or '').strip()
            for candidate in self._normalized_label_variants(attr_name):
                attr_order.setdefault(candidate, idx)

        if not attr_order:
            return name

        rest_lines = lines[1:]
        indexed = []
        for pos, line in enumerate(rest_lines):
            idx = self._get_custom_line_attribute_index(line, attr_order)
            indexed.append((line, idx, pos))

        mapped = [item for item in indexed if item[1] is not None]
        if not mapped:
            return name

        # Mantemos ordem por atributo no template; em empate, preserva ordem original.
        mapped_sorted = sorted(mapped, key=lambda item: (item[1], item[2]))
        unmapped = [item for item in indexed if item[1] is None]
        ordered_rest = [item[0] for item in mapped_sorted + unmapped]

        if ordered_rest == rest_lines:
            return name

        return "\n".join([lines[0]] + ordered_rest)

    def _append_single_value_attributes_to_name(self, name):
        if not name:
            return name

        lines = name.splitlines()
        if not lines:
            return name

        first_line = lines[0]
        rest_lines = lines[1:]

        match = re.search(r"\(([^)]*)\)", first_line)
        existing_items = []
        existing_vals = set()
        if match:
            existing_items = self._split_parenthesis_items(match.group(1))
            existing_vals = {self._normalize_for_compare(v) for v in existing_items}

        tmpl = self.product_template_id or (self.product_id and self.product_id.product_tmpl_id)
        if not tmpl:
            return name

        actual_by_attr = {}
        no_variant_model = self.env.get('product.template.attribute.value')
        for ptav in getattr(self, 'product_no_variant_attribute_value_ids', no_variant_model or []):
            if ptav.attribute_id and ptav.name:
                actual_by_attr[ptav.attribute_id.id] = ptav.name

        custom_model = self.env.get('product.custom.attribute.value')
        for cav in getattr(self, 'product_custom_attribute_value_ids', custom_model or []):
            ptav = cav.custom_product_template_attribute_value_id
            if ptav and ptav.attribute_id:
                value = cav.custom_value or ptav.name or ''
                if value:
                    actual_by_attr[ptav.attribute_id.id] = value

        for ptav in getattr(self, 'product_template_attribute_value_ids', no_variant_model or []):
            if ptav.attribute_id and ptav.name:
                actual_by_attr.setdefault(ptav.attribute_id.id, ptav.name)

        value_to_attr_idx = {}
        for idx, attr_line in enumerate(tmpl.attribute_line_ids):
            attr_id = attr_line.attribute_id.id
            value = actual_by_attr.get(attr_id)
            if not value:
                continue
            norm_value = self._normalize_for_compare(value)
            if norm_value and norm_value not in value_to_attr_idx:
                value_to_attr_idx[norm_value] = idx

        # "missing" = atributos de valor unico no template que ainda nao estao
        # no nome da linha e devem ser anexados para rastreabilidade.
        missing = []
        for idx, attr_line in enumerate(tmpl.attribute_line_ids):
            if len(attr_line.value_ids) != 1:
                continue
            attr_id = attr_line.attribute_id.id
            value = actual_by_attr.get(attr_id) or (attr_line.value_ids[0].name if attr_line.value_ids else '')
            value = (value or '').strip()
            if not value:
                continue
            attr_name = (attr_line.attribute_id.name or '').lower()
            if self._looks_like_dimensions(value) and self._has_dimensions_in_line(first_line):
                continue
            if 'dimensions' in attr_name and self._has_dimensions_in_line(first_line):
                continue
            norm_value = self._normalize_for_compare(value)
            if norm_value in existing_vals:
                continue
            if norm_value and norm_value in self._normalize_for_compare(first_line):
                continue
            missing.append((idx, value, norm_value))

        if match:
            items_with_idx = []
            for pos, item in enumerate(existing_items):
                norm_item = self._normalize_for_compare(item)
                items_with_idx.append((item, value_to_attr_idx.get(norm_item), pos))

            has_known_positions = any(item_idx is not None for _item, item_idx, _pos in items_with_idx)
            if not has_known_positions and not missing:
                return name

            if not has_known_positions:
                ordered_missing = [
                    (value, idx, -1 - pos)
                    for pos, (idx, value, _norm) in enumerate(sorted(missing, key=lambda x: x[0]))
                ]
                items_with_idx = ordered_missing + items_with_idx
            else:
                for idx, value, _norm in sorted(missing, key=lambda x: x[0]):
                    insert_at = len(items_with_idx)
                    for pos, (_item, item_idx, _orig_pos) in enumerate(items_with_idx):
                        if item_idx is not None and item_idx > idx:
                            insert_at = pos
                            break
                    items_with_idx.insert(insert_at, (value, idx, -1))

                mapped_items = [item for item in items_with_idx if item[1] is not None]
                unmapped_items = [item for item in items_with_idx if item[1] is None]
                items_with_idx = sorted(mapped_items, key=lambda item: (item[1], item[2])) + unmapped_items

            combined = ", ".join([item for item, _idx, _pos in items_with_idx if item])
            current_combined = ", ".join(existing_items)
            if not missing and combined == current_combined:
                return name
            first_line = re.sub(r"\(([^)]*)\)", f"({combined})", first_line, count=1)
        else:
            if not missing:
                return name
            first_line = f"{first_line} ({', '.join([value for _idx, value, _norm in missing])})"

        return "\n".join([first_line] + rest_lines)

    def _apply_mesmo_tecido_cleanup(self):
        # Punto unico de higienizacao de nome para reduzir divergencia entre
        # onchange/create/write.
        if self.env.context.get('skip_mesmo_tecido_cleanup'):
            return
        for line in self:
            if not line.name:
                continue
            prefer_pt = line._prefer_pt_labels()
            cleaned = self._strip_mesmo_tecido(line.name)
            cleaned = self._strip_custom_tokens(cleaned, prefer_pt=prefer_pt)
            cleaned = self._normalize_fabric_labels(cleaned, prefer_pt=prefer_pt)
            cleaned = line._append_single_value_attributes_to_name(cleaned)
            cleaned = line._order_custom_lines_by_attribute(cleaned)
            if cleaned != line.name:
                line.with_context(skip_mesmo_tecido_cleanup=True).write({'name': cleaned})

    @api.onchange('product_id', 'product_custom_attribute_value_ids', 'product_template_attribute_value_ids')
    def _onchange_strip_mesmo_tecido(self):
        self._apply_mesmo_tecido_cleanup()

    @api.model_create_multi
    def create(self, vals_list):
        # Pre-limpeza antes do create evita persistir texto sujo em DB.
        for vals in vals_list:
            if vals.get('name'):
                vals['name'] = self._strip_mesmo_tecido(vals['name'])
                vals['name'] = self._strip_custom_tokens(vals['name'])
                vals['name'] = self._normalize_fabric_labels(vals['name'])
        lines = super().create(vals_list)
        lines._apply_mesmo_tecido_cleanup()
        return lines

    def write(self, vals):
        if self.env.context.get('skip_mesmo_tecido_cleanup'):
            return super().write(vals)
        if vals.get('name'):
            vals['name'] = self._strip_mesmo_tecido(vals['name'])
            vals['name'] = self._strip_custom_tokens(vals['name'])
            vals['name'] = self._normalize_fabric_labels(vals['name'])
        res = super().write(vals)
        if 'name' in vals:
            self._apply_mesmo_tecido_cleanup()
        return res
