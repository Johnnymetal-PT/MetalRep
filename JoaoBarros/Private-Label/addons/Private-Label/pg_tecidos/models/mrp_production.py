import logging
import re
import unicodedata
from collections import defaultdict

from odoo import _, fields, api, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    TERM_NAMES = [
        'WOOD',
        'FRONT WOOD',
        'INTERIOR',
        'BASE',
        'GAVETA',
        'METAL',
        'SUPORTES',
        'ESTRUTURA',
        'MARMORE',
        'BOTTOM WOOD',
        'TOP WOOD',
        'TAMPO',
        'TOP',
        'VIDRO',
        'FABRIC',
        'FABRIC USED IN INTERNAL BACK AND SEAT',
        'FABRIC USED IN SEAT',
        'FABRIC USED IN BOTTOM OF THE SEAT',
        'FABRIC USED IN SEAT AND ARMREST',
        'FABRIC USED IN ARMREST',
        'FABRIC USED IN THE STRAP',
        'FABRIC USED IN ROLL',
        'FABRIC USED IN DOUBLE HEADBOARD',
        'FABRIC USED IN EXTERNAL BACK',
        'FABRIC USED IN BASE',
        'FABRIC USED IN PIPING',
        'FABRIC USED IN SEAT AND CUSHION BACK',
        'FABRIC USED IN BACK AND ARMREST',
        'FABRIC USED IN BACK',
        'FABRIC USED IN BACK AND BOTTOM OF THE SEAT',
        'FABRIC USED IN UNDER SEAT AND OUTER BACK',
        'FABRIC USED IN INNER BACK; SEAT AND ARMREST',
        'FABRIC USED IN SEAT AND BACKREST',
        'FABRIC USED IN BACKREST',
        'FABRIC:',
        'MAIN FABRIC',
        'PILLOW FABRIC',
        'FABRIC USED IN CUSTOM',
        'DIMENSIONS',
    ]

    BOM_TERMS = [term for term in TERM_NAMES if term != 'DIMENSIONS']

    TERM_BASE_MAP = {
        'WOOD': 'WOOD',
        'FRONT WOOD': 'WOOD',
        'BOTTOM WOOD': 'WOOD',
        'TOP WOOD': 'WOOD',
        'SUPORTES': 'METAL',
        'FABRIC:': 'FABRIC',
    }

    @classmethod
    def _get_base_term(cls, term):
        """Return the normalized base term used for precedence checks."""
        normalized = (term or '').strip().upper()
        if not normalized:
            return ''

        if normalized in cls.TERM_BASE_MAP:
            return cls.TERM_BASE_MAP[normalized]

        if normalized in cls.TERM_NAMES:
            return normalized

        for candidate in cls.TERM_NAMES:
            candidate_upper = (candidate or '').strip().upper()
            if candidate_upper and normalized.startswith(f"{candidate_upper} "):
                return cls.TERM_BASE_MAP.get(candidate_upper, candidate_upper)

        return normalized

    TERM_DEFINITIONS = [
        ('FRONT WOOD', ['front wood', 'madeira frontal', 'madeira frente', 'frente madeira']),
        ('BOTTOM WOOD', ['bottom wood', 'madeira inferior', 'madeira fundo', 'fundo madeira']),
        ('TOP WOOD', ['top wood', 'madeira superior', 'madeira topo', 'topo madeira']),
        ('TAMPO', ['tampo', 'tampo superior', 'tampo inferior']),
        ('WOOD', ['wood', 'madeira']),
        ('INTERIOR', ['interior', 'interior madeira', 'interior metal']),
        ('BASE', ['base', 'base metal', 'base madeira']),
        ('GAVETA', ['gaveta', 'gavetas']),
        ('METAL', ['metal']),
        ('SUPORTES', ['suportes', 'suporte']),
        ('ESTRUTURA', ['estrutura']),
        ('MARMORE', ['marmore', 'marmore']),
        ('TOP', ['top', 'topo']),
        ('VIDRO', ['vidro', 'vidraca']),
        ('FABRIC', ['fabric', 'tecido']),
        ('FABRIC USED IN INTERNAL BACK AND SEAT', ['fabric used in internal back and seat', 'tecido usado no encosto e assento']),
        ('FABRIC USED IN SEAT', ['fabric used in seat', 'tecido usado no assento']),
        ('FABRIC USED IN BOTTOM OF THE SEAT', ['fabric used in bottom of the seat', 'tecido usado na base do assento', 'tecido usado no fundo do assento']),
        ('FABRIC USED IN SEAT AND ARMREST', ['fabric used in seat and armrest', 'tecido usado no assento e bracos', 'tecido usado no assento e bracos', 'tecido usado no assento e braco', 'tecido usado no assento e braco']),
        ('FABRIC USED IN ARMREST', ['fabric used in armrest', 'tecido usado nos bracos', 'tecido usado nos bracos', 'tecido usado no braco', 'tecido usado no braco']),
        ('FABRIC USED IN THE STRAP', ['fabric used in the strap', 'tecido usado nas fivelas', 'tecido usado na tira']),
        ('FABRIC USED IN ROLL', ['fabric used in roll', 'tecido usado no rolo']),
        ('FABRIC USED IN DOUBLE HEADBOARD', ['fabric used in double headboard', 'tecido usado na cabeceira dupla']),
        ('FABRIC USED IN EXTERNAL BACK', ['fabric used in external back', 'tecido usado na costa']),
        ('FABRIC USED IN BASE', ['fabric used in base', 'tecido usado na base']),
        ('FABRIC USED IN PIPING', ['fabric used in piping', 'tecido usado no vivo']),
        ('FABRIC USED IN SEAT AND CUSHION BACK', ['fabric used in seat and cushion back', 'tecido usado no assento e almofada da costa', 'tecido usado no assento e almofada do encosto']),
        ('FABRIC USED IN BACK AND ARMREST', ['fabric used in back and armrest', 'tecido usado na costa e braco', 'tecido usado na costa e braco', 'tecido usado no encosto e braco', 'tecido usado no encosto e braco']),
        ('FABRIC USED IN BACK', ['fabric used in back', 'tecido usado na costa', 'tecido usado no encosto']),
        ('FABRIC USED IN BACK AND BOTTOM OF THE SEAT', ['fabric used in back and bottom of the seat', 'tecido usado na costa e base do assento', 'tecido usado no encosto e fundo do assento']),
        ('FABRIC USED IN UNDER SEAT AND OUTER BACK', ['fabric used in under seat and outer back', 'tecido usado no fundo do assento e costa']),
        ('FABRIC USED IN INNER BACK; SEAT AND ARMREST', ['fabric used in inner back; seat and armrest', 'tecido usado no encosto, assento e bracos', 'tecido usado no encosto, assento e bracos', 'tecido usado no encosto interior; assento e braco', 'tecido usado no encosto interior; assento e braco']),
        ('FABRIC USED IN SEAT AND BACKREST', ['fabric used in seat and backrest', 'tecido usado no assento e encosto']),
        ('FABRIC USED IN BACKREST', ['fabric used in backrest', 'tecido usado no encosto']),
        ('FABRIC:', ['fabric:', 'tecido:']),
        ('MAIN FABRIC', ['main fabric', 'tecido principal']),
        ('PILLOW FABRIC', ['pillow fabric', 'tecido da almofada decorativa', 'tecido da almofada', 'tecido almofada']),
        ('FABRIC USED IN CUSTOM', ['fabric used in custom', 'tecido usado no custom']),
        # PT-PT generic labels
        ('DIMENSIONS', ['dimensoes', 'dimensoes']),
        ('WOOD', ['madeira']),
        ('METAL', ['metal']),
        ('FABRIC', ['tecido']),
        ('MAIN FABRIC', ['tecido principal']),
    ]

    SPECIAL_LABELS = {
        'WOOD': [
            'Estrutura e Polimento',
            'Casco',
            'Polimento',
            'Rodape',
            'Madeira',
            'Pormenores Bracos',
            'Base e Polimento',
            'Madeira e Polimento',
            'Friso e Polimento',
        ],
        'FRONT WOOD': ['Estrutura e Polimento'],
        'INTERIOR': ['Estrutura e Polimento'],
        'BASE': ['Estrutura e Polimento'],
        'GAVETA': ['Estrutura e Polimento'],
        'BOTTOM WOOD': ['Estrutura e Polimento'],
        'TOP WOOD': ['Estrutura e Polimento'],
        'METAL': ['Apoio Costa'],
        'SUPORTES': ['Metal'],
        'ESTRUTURA': ['Metal'],
        'MARMORE': ['Marble'],
        'TAMPO': ['Tampo'],
        'TOP': ['Tampo'],
        'VIDRO': ['Tampo'],
        'MAIN FABRIC': [
            'Casco e Estofo',
            'Casco, Polimento e Estofo',
            'Estrutura, Polimento e Estofo',
            'Madeira, Polimento e Estofo',
        ],
    }

    SPECIAL_LABELS['WOOD'] = [
        'Estrutura e Polimento',
        'Casco',
        'Polimento',
        'Rodape',
        'Madeira',
        'Pormenores Bracos',
        'Base e Polimento',
        'Madeira e Polimento',
        'Friso e Polimento',
    ]

    FABRIC_DOMINANT_SPECIAL_LABELS = set(SPECIAL_LABELS.get('MAIN FABRIC', []))

    TERM_PRIORITY = {term: index for index, term in enumerate(TERM_NAMES)}

    product_description_variants = fields.Char()
    partner_id = fields.Many2one(
        'res.partner',
        string='Fornecedor',
        domain="['|', ('company_id', '=', company_id), ('company_id', 'parent_of', company_id)]",
    )

    # ----------------------------
    # Helpers for FABRIC cleanup / MESMO TECIDO
    # ----------------------------
    @staticmethod
    def _parse_mesmo_tecido(value):
        """
        Detect MESMO TECIDO in values like:
          "MESMO TECIDO"
          "MESMO TECIDO: COISO"
          "MESMO TECIDO - COISO"
          "MESMO TECIDO COISO"
        Returns: (is_mesmo: bool, custom: str)
        """
        txt = re.sub(r"\s+", " ", (value or "")).strip(" ,;:")
        if not txt:
            return False, ""

        # Accept "MESMO TECIDO" in any case, but "MESMO" alone only if uppercase.
        m = re.match(r"^MESMO\s+(?:TECIDO|FABRIC)\b(?:\s*[:\-]\s*(.*))?$", txt, flags=re.IGNORECASE)
        if m:
            custom = (m.group(1) or "").strip(" ,;:")
            return True, custom

        m = re.match(r"^MESMO\b(?:\s*[:\-]\s*(.*))?$", txt)
        if not m:
            return False, ""

        custom = (m.group(1) or "").strip(" ,;:")
        return True, custom

    @classmethod
    def _is_mesmo_tecido(cls, value):
        return cls._parse_mesmo_tecido(value)[0]

    def _strip_trailing_term_labels(self, value, term=None):
        """Remove dangling term labels and trailing MESMO TECIDO from an extracted value."""
        text = re.sub(r"\s+", " ", (value or '')).strip(" ,;:")
        if not text:
            return ''

        # Remove trailing "MESMO TECIDO" (any case) and "MESMO" (uppercase only).
        text = re.sub(
            r"(?:\s*[,;:]?\s*)MESMO\s+TECIDO\b\s*[:\-]?\s*$",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip(" ,;:")
        text = re.sub(
            r"(?:\s*[,;:]?\s*)MESMO\b\s*[:\-]?\s*$",
            "",
            text,
        ).strip(" ,;:")

        # Remove trailing known labels (longest first to avoid partial matches)
        excluded_terms = set()
        if term:
            excluded_terms.add((term or '').strip().upper())
            excluded_terms.add(self._get_base_term(term))

        term_candidates = sorted(
            [(t or '').strip().rstrip(':') for t in self.TERM_NAMES if t],
            key=lambda x: len(x),
            reverse=True
        )

        changed = True
        while changed and text:
            changed = False
            for t in term_candidates:
                if not t:
                    continue
                if t.strip().upper() in excluded_terms:
                    continue
                pattern = re.compile(rf"(?:\s*[,;:]?\s*){re.escape(t)}\s*$", re.IGNORECASE)
                new_text = pattern.sub("", text).strip(" ,;:")
                if new_text != text:
                    text = new_text
                    changed = True

        return text.strip(" ,;:")

    def _strip_leading_fabric_labels(self, value):
        text = re.sub(r"\s+", " ", (value or '')).strip(" ,;:")
        if not text:
            return ''

        label_candidates = list(self._get_fabric_label_candidates())
        label_candidates.extend([
            'FABRIC',
            'TECIDO',
            'MAIN FABRIC',
            'TECIDO PRINCIPAL',
            'PILLOW FABRIC',
            'TECIDO DA ALMOFADA DECORATIVA',
        ])

        changed = True
        while changed and text:
            changed = False
            for label in label_candidates:
                if not label:
                    continue
                new_text = re.sub(
                    rf"(?i)^\s*{re.escape(label)}\s*:\s*",
                    "",
                    text,
                    count=1,
                ).strip(" ,;:")
                if new_text != text:
                    text = new_text
                    changed = True

            # Remove accidental non-fabric term prefixes inside fabric values (e.g. "WOOD: ...").
            match = re.match(r"^\s*([^:]{1,80})\s*:\s*(.+)$", text)
            if match:
                label = match.group(1).strip()
                normalized = self._normalize_pt_labels_to_en(f"{label}: __pg__")
                normalized_label = normalized.split(':', 1)[0].strip()
                base_label = self._get_base_term(normalized_label)
                if base_label in self.TERM_NAMES and not self._is_fabric_term(base_label):
                    text = match.group(2).strip(" ,;:")
                    changed = True

        return text.strip(" ,;:")

    @classmethod
    def _normalize_so_description_for_mo(cls, description):
        """Collapse MESMO TECIDO lines into a single TECIDO/FABRIC line when possible."""
        if not description:
            return description

        lines = description.splitlines()
        if not lines:
            return description

        header = lines[0]
        rest = lines[1:]
        if not rest:
            return description

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
        has_mesmo = False
        donor_value = ""

        for line in rest:
            line_stripped = line.strip()
            match = fabric_prefix_re.match(line_stripped)
            if match:
                value = match.group(2).strip()
            elif re.search(r"(?i)\b(fabric|tecido)\b", line_stripped) and ":" in line_stripped:
                value = line_stripped.split(":", 1)[1].strip()
            else:
                non_fabric_lines.append(line)
                continue
            fabric_lines.append(line)
            if cls._is_mesmo_tecido(value):
                has_mesmo = True
                continue
            if value and not donor_value:
                donor_value = value

        if not fabric_lines or not has_mesmo or not donor_value:
            return description

        normalized = [header, f"FABRIC: {donor_value}"]
        normalized.extend(non_fabric_lines)
        return "\n".join(normalized)

    @staticmethod
    def _prefer_pt_labels_for_partner(partner, context_lang=None):
        lang = (partner and partner.lang) or (context_lang or "")
        lang = (lang or "").lower()
        if lang.startswith("pt"):
            return True
        country_code = (partner and partner.country_id and partner.country_id.code) or ""
        return country_code.upper() == "PT"

    @classmethod
    def _normalize_pt_labels_to_en(cls, description):
        if not description:
            return description

        pt_to_en = [
            (r"TECIDO USADO NO ENCOSTO E ASSENTO", "FABRIC USED IN INTERNAL BACK AND SEAT"),
            (r"TECIDO PRINCIPAL", "MAIN FABRIC"),
            (r"TECIDO USADO NO ASSENTO", "FABRIC USED IN SEAT"),
            (r"TECIDO USADO NA BASE DO ASSENTO|TECIDO USADO NO FUNDO DO ASSENTO", "FABRIC USED IN BOTTOM OF THE SEAT"),
            (r"TECIDO DA ALMOFADA DECORATIVA|TECIDO(?:\s+DA)?\s+ALMOFADA", "PILLOW FABRIC"),
            ("TECIDO USADO NO ASSENTO E BRACOS?|TECIDO USADO NO ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?", "FABRIC USED IN SEAT AND ARMREST"),
            ("TECIDO USADO NOS BRACOS?|TECIDO USADO NOS BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?|TECIDO USADO NO BRACO|TECIDO USADO NO BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O", "FABRIC USED IN ARMREST"),
            (r"TECIDO USADO NAS FIVELAS|TECIDO USADO NA TIRA", "FABRIC USED IN THE STRAP"),
            (r"TECIDO USADO NO ROLO", "FABRIC USED IN ROLL"),
            (r"TECIDO USADO NA CABECEIRA DUPLA", "FABRIC USED IN DOUBLE HEADBOARD"),
            (r"TECIDO USADO NA BASE", "FABRIC USED IN BASE"),
            (r"TECIDO USADO NO VIVO", "FABRIC USED IN PIPING"),
            (r"TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA|TECIDO USADO NO ASSENTO E ALMOFADA DO ENCOSTO", "FABRIC USED IN SEAT AND CUSHION BACK"),
            ("TECIDO USADO NA COSTA E BRACO|TECIDO USADO NA COSTA E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O|TECIDO USADO NO ENCOSTO E BRACO|TECIDO USADO NO ENCOSTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O", "FABRIC USED IN BACK AND ARMREST"),
            (r"TECIDO USADO NA COSTA E BASE DO ASSENTO|TECIDO USADO NO ENCOSTO E FUNDO DO ASSENTO", "FABRIC USED IN BACK AND BOTTOM OF THE SEAT"),
            (r"TECIDO USADO NO FUNDO DO ASSENTO E COSTA", "FABRIC USED IN UNDER SEAT AND OUTER BACK"),
            ("TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRACOS?|TECIDO USADO NO ENCOSTO,\\s*ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS?|TECIDO USADO NO ENCOSTO INTERIOR;\\s*ASSENTO E BRACO|TECIDO USADO NO ENCOSTO INTERIOR;\\s*ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O", "FABRIC USED IN INNER BACK; SEAT AND ARMREST"),
            (r"TECIDO USADO NO ASSENTO E ENCOSTO", "FABRIC USED IN SEAT AND BACKREST"),
            (r"TECIDO USADO NA COSTA", "FABRIC USED IN EXTERNAL BACK"),
            (r"TECIDO USADO NO ENCOSTO", "FABRIC USED IN BACKREST"),
            (r"TECIDO USADO", "FABRIC USED IN"),
            (r"DIMENS(?:OES|ÕES)", "DIMENSIONS"),
            (r"MADEIRA", "WOOD"),
            (r"METAL", "METAL"),
        ]

        for pt_label, en_label in pt_to_en:
            # Replace only label prefixes at line start to avoid touching values like "MESMO TECIDO".
            description = re.sub(
                rf"(?im)^\s*(?:{pt_label})[ \t]*:",
                f"{en_label}: ",
                description,
            )

        # Same rule for generic "TECIDO:" label: line start only.
        description = re.sub(r"(?im)^\s*TECIDO[ \t]*:[ \t]*", "FABRIC: ", description)
        return description

    @classmethod
    def _translate_terms_for_output(cls, terms, prefer_pt=False):
        if not prefer_pt:
            return terms

        en_to_pt = {
            'FABRIC': 'TECIDO',
            'FABRIC USED IN INTERNAL BACK AND SEAT': 'TECIDO USADO NO ENCOSTO E ASSENTO',
            'MAIN FABRIC': 'TECIDO PRINCIPAL',
            'FABRIC USED IN SEAT': 'TECIDO USADO NO ASSENTO',
            'FABRIC USED IN BOTTOM OF THE SEAT': 'TECIDO USADO NA BASE DO ASSENTO',
            'PILLOW FABRIC': 'TECIDO DA ALMOFADA DECORATIVA',
            'FABRIC USED IN SEAT AND ARMREST': 'TECIDO USADO NO ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS',
            'FABRIC USED IN ARMREST': 'TECIDO USADO NOS BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS',
            'FABRIC USED IN THE STRAP': 'TECIDO USADO NAS FIVELAS',
            'FABRIC USED IN ROLL': 'TECIDO USADO NO ROLO',
            'FABRIC USED IN DOUBLE HEADBOARD': 'TECIDO USADO NA CABECEIRA DUPLA',
            'FABRIC USED IN EXTERNAL BACK': 'TECIDO USADO NA COSTA',
            'FABRIC USED IN BASE': 'TECIDO USADO NA BASE',
            'FABRIC USED IN PIPING': 'TECIDO USADO NO VIVO',
            'FABRIC USED IN SEAT AND CUSHION BACK': 'TECIDO USADO NO ASSENTO E ALMOFADA DA COSTA',
            'FABRIC USED IN BACK AND ARMREST': 'TECIDO USADO NA COSTA E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}O',
            'FABRIC USED IN BACK': 'TECIDO USADO NA COSTA',
            'FABRIC USED IN BACK AND BOTTOM OF THE SEAT': 'TECIDO USADO NA COSTA E BASE DO ASSENTO',
            'FABRIC USED IN UNDER SEAT AND OUTER BACK': 'TECIDO USADO NO FUNDO DO ASSENTO E COSTA',
            'FABRIC USED IN INNER BACK; SEAT AND ARMREST': 'TECIDO USADO NO ENCOSTO, ASSENTO E BRA\N{LATIN CAPITAL LETTER C WITH CEDILLA}OS',
            'FABRIC USED IN SEAT AND BACKREST': 'TECIDO USADO NO ASSENTO E ENCOSTO',
            'FABRIC USED IN BACKREST': 'TECIDO USADO NO ENCOSTO',
            'FABRIC USED IN': 'TECIDO USADO',
            'FABRIC USED IN CUSTOM': 'TECIDO USADO NO CUSTOM',
            'DIMENSIONS': 'DIMENSOES',
            'WOOD': 'MADEIRA',
            'FRONT WOOD': 'MADEIRA FRONTAL',
            'BOTTOM WOOD': 'MADEIRA INFERIOR',
            'TOP WOOD': 'MADEIRA SUPERIOR',
            'TAMPO': 'TAMPO',
            'BASE': 'BASE',
            'INTERIOR': 'INTERIOR',
            'GAVETA': 'GAVETA',
            'METAL': 'METAL',
            'ESTRUTURA': 'ESTRUTURA',
            'SUPORTES': 'SUPORTES',
            'MARMORE': 'MARMORE',
            'VIDRO': 'VIDRO',
            'TOP': 'TOPO',
        }

        translated = {}
        for key, value in terms.items():
            label = en_to_pt.get(key, key)
            translated[label] = value
        return translated

    @classmethod
    def _get_pt_term_label(cls, term):
        translated = cls._translate_terms_for_output({term: ''}, prefer_pt=True)
        return next(iter(translated.keys()), term)

    @classmethod
    def _get_fabric_label_candidates(cls):
        """Collect EN/PT labels used for fabric terms, longest-first."""
        labels = set()

        for term in cls.TERM_NAMES:
            if cls._is_fabric_term(term):
                label = (term or '').strip().rstrip(':')
                if label:
                    labels.add(label)

        generic_labels = {'fabric', 'tecido', 'fabric used in', 'tecido usado'}
        for canonical_term, keywords in cls.TERM_DEFINITIONS:
            if not cls._is_fabric_term(canonical_term):
                continue
            for keyword in (keywords or []):
                label = (keyword or '').strip().rstrip(':')
                if not label:
                    continue
                if label.lower() in generic_labels:
                    continue
                labels.add(label)

        return sorted(labels, key=len, reverse=True)

    def _remove_all_fabric_labels(self, name):
        """Remove all EN/PT fabric-location labels from a component name."""
        if not name:
            return name

        cleaned = re.sub(r"\s+", " ", name).strip()
        for label in self._get_fabric_label_candidates():
            pattern = re.compile(rf"(?i)(?<!\w){re.escape(label)}(?!\w)\s*:?")
            cleaned = pattern.sub(" ", cleaned)

        cleaned = re.sub(r"\s*,\s*,", ", ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")
        return cleaned

    def _remove_all_term_labels(self, name):
        """Remove all known term labels from a component name (used to drop placeholders)."""
        if not name:
            return name
        cleaned = re.sub(r"\s+", " ", name).strip()
        term_candidates = sorted(
            [(t or '').strip().rstrip(':') for t in self.TERM_NAMES if t and t != 'DIMENSIONS'],
            key=lambda x: len(x),
            reverse=True,
        )
        for term in term_candidates:
            if not term:
                continue
            pattern = re.compile(rf"(?i)(?:^|\s){re.escape(term)}(?:\s|$)")
            cleaned = pattern.sub(" ", cleaned)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:-")
        return cleaned

    def _clean_fabric_parts(self, combined_value):
        """Split combined value, strip labels, drop MESMO TECIDO, dedupe preserving order."""
        raw = re.sub(r"\s+", " ", (combined_value or '')).strip(" ,;:")
        if not raw:
            return []
        parts = [p.strip(" ,;:") for p in raw.split(",") if p.strip(" ,;:")]
        cleaned = []
        seen = set()
        for p in parts:
            p2 = self._strip_trailing_term_labels(p)
            if not p2:
                continue
            # Detect MESMO TECIDO (including "MESMO TECIDO: X") and drop it from normal fabric list parts
            if self._is_mesmo_tecido(p2):
                continue
            key = p2.strip().lower()
            if key in seen:
                continue
            seen.add(key)
            cleaned.append(p2)
        return cleaned

    def _get_sale_order_line_for_mo_vals(self, vals):
        product_id = vals.get('product_id')
        if not product_id:
            return self.env['sale.order.line']

        sale_order = self.env['sale.order']
        procurement_group_id = vals.get('procurement_group_id')
        if procurement_group_id:
            group = self.env['procurement.group'].browse(procurement_group_id)
            sale_order = getattr(group, 'sale_id', self.env['sale.order'])

        if sale_order:
            candidates = sale_order.order_line.filtered(lambda l: l.product_id.id == product_id)
            if candidates:
                return candidates.sorted(key=lambda l: (l.sequence, l.id), reverse=True)[:1]

        origin = vals.get('origin')
        if origin:
            line = self.env['sale.order.line'].search([
                ('order_id.name', '=', origin),
                ('product_id', '=', product_id),
            ], order='sequence desc, id desc', limit=1)
            if line:
                return line

        return self.env['sale.order.line'].search([
            ('product_id', '=', product_id),
        ], order='id desc', limit=1)

    def _has_non_mesmo_fabric_terms(self, terms):
        for term, value in (terms or {}).items():
            if not self._is_fabric_term(term):
                continue
            cleaned = self._strip_trailing_term_labels(value or '', term=term)
            cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,;:")
            if cleaned and not self._is_mesmo_tecido(cleaned):
                return True
        return False

    def _extract_fabric_terms_from_sale_line(self, sale_order_line):
        extracted = {}
        if not sale_order_line:
            return extracted

        def _store(attr_name, raw_value):
            value = re.sub(r"\s+", " ", (raw_value or '')).strip(" ,;:")
            value = self._strip_leading_fabric_labels(value)
            if not value or self._is_mesmo_tecido(value):
                return
            if value.upper() in {'FAB', 'COM'}:
                return

            normalized = self._normalize_pt_labels_to_en(f"{attr_name}: {value}")
            term_label = normalized.split(':', 1)[0].strip()
            base_term = self._get_base_term(term_label)
            if not self._is_fabric_term(base_term):
                return
            extracted.setdefault(base_term, value)

        for ptav in sale_order_line.product_template_attribute_value_ids:
            _store(ptav.attribute_id.name or '', ptav.name or '')

        if hasattr(sale_order_line, 'product_no_variant_attribute_value_ids'):
            for ptav in sale_order_line.product_no_variant_attribute_value_ids:
                _store(ptav.attribute_id.name or '', ptav.name or '')

        for cav in sale_order_line.product_custom_attribute_value_ids:
            ptav = cav.custom_product_template_attribute_value_id
            attr_name = (ptav and ptav.attribute_id and ptav.attribute_id.name) or ''
            _store(attr_name, cav.custom_value or (ptav and ptav.name) or '')

        if not extracted:
            normalized_so_name = self._normalize_pt_labels_to_en(sale_order_line.name or '')
            for line in normalized_so_name.splitlines():
                match = re.match(r"^\s*FABRIC\s*:\s*(.+)$", line.strip(), flags=re.IGNORECASE)
                if match:
                    fallback = re.sub(r"\s+", " ", match.group(1)).strip(" ,;:")
                    if fallback and not self._is_mesmo_tecido(fallback):
                        extracted['FABRIC'] = fallback
                    break

        return extracted


    def _get_zero_quantity_components(self):
        default_rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure') or 0.0001
        zero_moves = self.move_raw_ids.filtered(
            lambda move: float_is_zero(
                move.product_uom_qty,
                precision_rounding=(move.product_uom and move.product_uom.rounding) or default_rounding,
            )
        )
        return zero_moves.filtered(lambda move: move.product_id)

    def _format_zero_qty_message(self, zero_moves):
        message_lines = []
        for production in self:
            moves = zero_moves.filtered(lambda move: move.raw_material_production_id == production)
            if not moves:
                continue
            products = ', '.join(moves.mapped('product_id.display_name'))
            message_lines.append(_("%s: %s") % (production.name, products))
        return '\n'.join(message_lines)

    def action_confirm(self):
        if not self.env.context.get('skip_zero_qty_warning'):
            zero_moves = self._get_zero_quantity_components()
            if zero_moves:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Components with zero quantity'),
                    'res_model': 'mrp.production.zero.qty.warning',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_production_ids': self.ids,
                        'default_zero_component_message': self._format_zero_qty_message(zero_moves),
                    },
                }

        return super().action_confirm()

    @api.model
    def create(self, vals):
        # ----------------------------
        # ? Analytic propagation: SO.analytic_account_id -> MO.analytic_distribution
        # ----------------------------
        if not vals.get('analytic_distribution') and vals.get('procurement_group_id'):
            group = self.env['procurement.group'].browse(vals['procurement_group_id'])
            sale = getattr(group, 'sale_id', False)
            aa = sale and getattr(sale, 'analytic_account_id', False) or False
            if aa:
                vals['analytic_distribution'] = {str(aa.id): 100.0}
        # ------------------------------------------------------------------------------

        # Check if product_description_variants is empty
        sale_order_line = self._get_sale_order_line_for_mo_vals(vals)

        description = str(vals.get('product_description_variants') or '').strip()
        description_from_so = False
        if not description:
            if sale_order_line:
                description = sale_order_line.name
                vals['product_description_variants'] = description
                description_from_so = True
                _logger.info(f"[CREATE] Set product_description_variants to product name: {description}")
            else:
                _logger.warning(f"[CREATE] No sale.order.line found for product_id: {vals.get('product_id')}")

        has_mesmo_tecido = self._is_mesmo_tecido(description)

        terms = {term: '' for term in self.TERM_NAMES}

        description = self._normalize_so_description_for_mo(description)
        description = self._normalize_pt_labels_to_en(description)
        _logger.info(f"[CREATE] Product description variants: {description}")

        normalized_description = description.replace('\r\n', '\n')

        # Extract the text for each term
        for term in terms:
            if term.endswith(':') and term.rstrip(':') in terms:
                continue
            normalized_term = term.lower().rstrip(':')
            pattern = re.compile(rf"{re.escape(normalized_term)}:\s*([^\n\r,]+)", re.IGNORECASE)
            match = pattern.search(normalized_description)
            if match:
                cleaned_value = re.sub(r"\s+", " ", match.group(1)).strip(" ,")
                cleaned_value = self._strip_trailing_term_labels(cleaned_value, term=term)
                if self._is_fabric_term(term):
                    cleaned_value = self._strip_leading_fabric_labels(cleaned_value)
                if term != 'DIMENSIONS':
                    cleaned_value = re.sub(r"(?i)^CUSTOM\s*:\s*", "", cleaned_value).strip(" ,")
                terms[term] = cleaned_value
                _logger.info(f"[CREATE] Extracted term '{term}': {terms[term]}")

        # Normalize FABRIC: alias
        if terms.get('FABRIC:') and not terms.get('FABRIC'):
            terms['FABRIC'] = terms['FABRIC:']
        terms.pop('FABRIC:', None)

        # Fetch "DIMENSIONS" from product variant attribute values
        sale_order_line = sale_order_line or self._get_sale_order_line_for_mo_vals(vals)
        if sale_order_line:
            # If SO description was collapsed, still detect MESMO TECIDO from attributes
            if not has_mesmo_tecido:
                def _has_mesmo(value):
                    return self._is_mesmo_tecido(value or "")

                for cav in sale_order_line.product_custom_attribute_value_ids:
                    ptav = cav.custom_product_template_attribute_value_id
                    if _has_mesmo(cav.custom_value) or _has_mesmo(ptav and ptav.name):
                        has_mesmo_tecido = True
                        break

                if not has_mesmo_tecido:
                    for ptav in sale_order_line.product_template_attribute_value_ids:
                        if _has_mesmo(ptav.name):
                            has_mesmo_tecido = True
                            break

                if not has_mesmo_tecido and hasattr(sale_order_line, 'product_no_variant_attribute_value_ids'):
                    for ptav in sale_order_line.product_no_variant_attribute_value_ids:
                        if _has_mesmo(ptav.name):
                            has_mesmo_tecido = True
                            break

            dimensions_values = sale_order_line.product_template_attribute_value_ids.filtered(
                lambda ptav: 'dimensions' in (ptav.attribute_id.name or '').lower()
            )
            if dimensions_values:
                dimensoes_value = dimensions_values[0].name
                if dimensoes_value:
                    terms['DIMENSIONS'] = dimensoes_value
                    _logger.info(f"[CREATE] Selected DIMENSIONS: {dimensoes_value}")
            if (terms.get('DIMENSIONS') or '').strip().upper() == 'CUSTOM DIMENSIONS':
                match = re.search(
                    r"(CUSTOM\s+DIMENSIONS\s*[:\-]?\s*[^\n\r]+)",
                    normalized_description,
                    flags=re.IGNORECASE,
                )
                if match:
                    custom_dimensions = re.sub(r"\s+", " ", match.group(1)).strip(" ,")
                    if custom_dimensions:
                        terms['DIMENSIONS'] = custom_dimensions
                        _logger.info(f"[CREATE] Expanded CUSTOM DIMENSIONS: {custom_dimensions}")

        # If only generic FABRIC is provided, propagate it to all fabric-specific terms
        generic_fabric = (terms.get('FABRIC') or '').strip()
        if generic_fabric:
            has_specific_fabric = any(
                self._is_fabric_term(t) and t != 'FABRIC' and (terms.get(t) or '').strip()
                for t in terms
            )
            if not has_specific_fabric:
                for t in terms:
                    if self._is_fabric_term(t) and t != 'FABRIC':
                        terms[t] = generic_fabric

        # When procurement only carries MESMO fabric placeholders, recover concrete values
        # from the actual SO line attribute selection.
        if sale_order_line and not self._has_non_mesmo_fabric_terms(terms):
            fallback_fabrics = self._extract_fabric_terms_from_sale_line(sale_order_line)
            if fallback_fabrics:
                for fallback_term, fallback_value in fallback_fabrics.items():
                    if fallback_value:
                        terms[fallback_term] = fallback_value
                fallback_generic = fallback_fabrics.get('FABRIC') or ''
                if fallback_generic:
                    for fabric_term in terms:
                        if self._is_fabric_term(fabric_term) and not (terms.get(fabric_term) or '').strip():
                            terms[fabric_term] = fallback_generic
                _logger.info("[CREATE] Enriched fabric terms from SO line attributes: %s", fallback_fabrics)

        existing_description = str(vals.get('product_description_variants') or '').strip()
        if existing_description:
            existing_description = self._normalize_so_description_for_mo(existing_description)
            existing_description = self._normalize_pt_labels_to_en(existing_description)

        existing_terms = {}
        if existing_description and not description_from_so:
            normalized_existing = existing_description.replace('\r\n', '\n')
            for item in re.split(r',\s*|\n+', normalized_existing):
                if ': ' in item:
                    key, value = item.split(': ', 1)
                    key = key.strip().rstrip(':')
                    base_key = self._get_base_term(key)
                    if base_key not in self.TERM_NAMES:
                        continue
                    cleaned_value = re.sub(r"\s+", " ", value).strip()
                    if base_key != 'DIMENSIONS':
                        cleaned_value = re.sub(r"(?i)^CUSTOM\s*:\s*", "", cleaned_value).strip(" ,")
                    cleaned_value = self._strip_trailing_term_labels(cleaned_value, term=base_key)
                    normalized_key = base_key if base_key != key else key
                    if normalized_key == 'FABRIC:' and 'FABRIC' in self.TERM_NAMES:
                        normalized_key = 'FABRIC'
                    existing_terms[normalized_key] = cleaned_value
        else:
            # When description comes from SO, ignore any existing_terms (avoid duplicate FABRIC blocks).
            existing_terms = {}

        existing_bases = {}
        for existing_key in existing_terms:
            base_term = self._get_base_term(existing_key)
            existing_bases.setdefault(base_term, []).append(existing_key)

        for term, value in terms.items():
            if value:
                base_term = self._get_base_term(term)
                term_upper = term.upper()
                base_keys = existing_bases.get(base_term, [])
                has_specific = any(key.upper() != term_upper for key in base_keys)

                if has_specific:
                    _logger.info(
                        f"[CREATE] Skipping base term '{term}' because specific variants {base_keys} already exist."
                    )
                    continue

                existing_terms[term] = value
                if term not in base_keys:
                    existing_bases.setdefault(base_term, []).append(term)

        # Normalize fabric terms: drop MESMO TECIDO and collapse to single FABRIC when appropriate
        fabric_keys = [k for k in existing_terms if self._is_fabric_term(k)]
        if fabric_keys:
            non_mesmo_vals = []
            has_mesmo = False
            effective_fabric_keys = []
            for k in list(fabric_keys):
                raw = existing_terms.get(k) or ''
                raw = self._strip_trailing_term_labels(raw)
                raw = re.sub(r"\s+", " ", raw).strip(" ,;:")
                is_mesmo, _custom = self._parse_mesmo_tecido(raw)
                if is_mesmo:
                    has_mesmo = True
                    existing_terms.pop(k, None)
                    continue
                if raw:
                    existing_terms[k] = raw
                    non_mesmo_vals.append(raw)
                    effective_fabric_keys.append(k)
                else:
                    existing_terms.pop(k, None)

            unique_non_mesmo = []
            seen_vals = set()
            for val in non_mesmo_vals:
                key = val.lower()
                if key in seen_vals:
                    continue
                seen_vals.add(key)
                unique_non_mesmo.append(val)

            if len(unique_non_mesmo) == 1 and (has_mesmo or len(set(effective_fabric_keys)) == 1):
                for k in list(existing_terms):
                    if self._is_fabric_term(k):
                        existing_terms.pop(k, None)
                existing_terms['FABRIC'] = unique_non_mesmo[0]

        # Prefer PT labels for PT customers when building MO description.
        prefer_pt = False
        partner = False
        if vals.get('procurement_group_id'):
            group = self.env['procurement.group'].browse(vals['procurement_group_id'])
            sale = getattr(group, 'sale_id', False)
            partner = sale and sale.partner_id or False
        if not partner and sale_order_line:
            partner = sale_order_line.order_id.partner_id
        prefer_pt = self._prefer_pt_labels_for_partner(partner, self.env.context.get('lang'))

        output_terms = self._translate_terms_for_output(existing_terms, prefer_pt=prefer_pt)
        vals['product_description_variants'] = ', '.join(
            f"{key}: {value}" for key, value in output_terms.items()
        )
        _logger.info(f"[CREATE] Final product_description_variants: {vals['product_description_variants']}")

        product_qty = sale_order_line.product_uom_qty if sale_order_line else 1

        oldest_bom = self._search_oldest_bom(vals.get('product_id'))
        duplicated_bom = self._duplicate_bom(oldest_bom, product_qty)

        if duplicated_bom:
            line_matches = self._map_terms_to_bom_lines(duplicated_bom, terms)
            self._apply_consumption_values(duplicated_bom, line_matches, product_qty)
            self._duplicate_and_assign_to_bom(
                duplicated_bom,
                line_matches,
                terms,
                has_mesmo_tecido=has_mesmo_tecido,
                product_qty=product_qty,
            )

        vals['state'] = 'draft'
        production = super(MrpProduction, self).create(vals)
        if duplicated_bom:
            production.write({'bom_id': duplicated_bom.id})
            production._resequence_raw_moves_from_bom()
            _logger.info(f"[CREATE] Assigned duplicated BoM {duplicated_bom.id} to Manufacturing Order {production.id}")

        return production

    def _resequence_raw_moves_from_bom(self):
        for production in self:
            bom = production.bom_id
            moves = production.move_raw_ids
            if not bom or not moves:
                continue

            bom_order = {
                line.id: index
                for index, line in enumerate(bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)), start=1)
            }

            ordered_moves = moves.sorted(
                key=lambda move: (
                    bom_order.get(move.bom_line_id.id, 10 ** 6),
                    move.sequence,
                    move.id,
                )
            )

            for index, move in enumerate(ordered_moves, start=1):
                target_sequence = index * 10
                if move.sequence != target_sequence:
                    move.sequence = target_sequence

    def _search_oldest_bom(self, product_id):
        product = self.env['product.product'].browse(product_id)
        bom = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', product.product_tmpl_id.id)],
            order='create_date asc',
            limit=1
        )
        _logger.info(
            f"[BOM] Found oldest BoM for product {product.product_tmpl_id.id}: {bom.id if bom else 'No BoM found'}"
        )
        return bom

    @staticmethod
    def _bom_line_signature(line):
        product_uom = line.product_uom_id or line.product_id.uom_id
        return (
            line.product_id.id,
            product_uom.id if product_uom else False,
            round(line.product_qty or 0.0, 6),
            line.operation_id.id or False,
            line.child_bom_id.id or False,
            tuple(sorted(line.bom_product_template_attribute_value_ids.ids)),
        )


    def _duplicate_bom(self, bom, product_qty):
        if bom:
            original_lines = bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id))
            original_positions_by_signature = defaultdict(list)
            for index, original_line in enumerate(original_lines, start=1):
                original_positions_by_signature[self._bom_line_signature(original_line)].append(index * 10)

            duplicated_bom = bom.copy()
            _logger.info(f"[BOM] Duplicated BoM {bom.id} to new BoM {duplicated_bom.id}")

            unmatched_lines = self.env['mrp.bom.line']
            for line in duplicated_bom.bom_line_ids.sorted(key=lambda l: l.id):
                signature = self._bom_line_signature(line)
                positions = original_positions_by_signature.get(signature) or []
                if positions:
                    target_sequence = positions.pop(0)
                else:
                    unmatched_lines |= line
                    continue
                if line.sequence != target_sequence:
                    line.sequence = target_sequence

            if unmatched_lines:
                next_sequence = (len(original_lines) + 1) * 10
                for line in unmatched_lines.sorted(key=lambda l: l.id):
                    line.sequence = next_sequence
                    next_sequence += 10
                _logger.warning(
                    "[BOM] Could not map %s copied BoM lines back to original order; appended them at the end.",
                    len(unmatched_lines),
                )

            if duplicated_bom.product_qty != product_qty:
                duplicated_bom.product_qty = product_qty
                _logger.info(f"[BOM] Updated duplicated BoM product_qty to {product_qty}")

            for line in duplicated_bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)):
                product_name = line.product_id.name

                term_in_line, _keyword = self._identify_term(product_name)
                component_uom = line.product_uom_id or line.product_id.uom_id
                is_fabric_component = (
                    term_in_line
                    and 'FABRIC' in term_in_line
                    and self._is_fabric_uom(component_uom)
                )

                if not is_fabric_component:
                    original_qty = line.product_qty
                    scaled_qty = original_qty * product_qty
                    line.product_qty = scaled_qty
                    _logger.info(
                        "[BOM] Scaled component %s: Original Qty %s, New Qty %s",
                        line.product_id.name,
                        original_qty,
                        scaled_qty,
                    )
                else:
                    _logger.info(
                        "[BOM] Skipping fabric component %s in bulk scaling step; will be set from consumption table.",
                        line.product_id.name,
                    )

            return duplicated_bom
        return None

    def _apply_consumption_values(self, bom, line_matches, product_qty):
        if not bom:
            return

        for line in bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)):
            line_data = line_matches.get(line.id)
            if not line_data:
                _logger.info(
                    f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms "
                    f"(sanitized name: '{self._strip_bracket_content(line.product_id.name)}')."
                )
                continue

            term = line_data['primary_term']
            if term not in self.BOM_TERMS:
                _logger.info(
                    f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms."
                )
                continue

            component_uom = line.product_uom_id or line.product_id.uom_id
            is_fabric_term = self._is_fabric_term(term)
            is_fabric_uom = self._is_fabric_uom(component_uom)

            component_template = line.product_id.product_tmpl_id

            if not is_fabric_term or not is_fabric_uom:
                _logger.info(
                    f"[BOM] Retaining original quantity for line {line.id} (term '{term}'): "
                    f"Component: {component_template.name}, Product Qty: {line.product_qty}"
                )
                continue

            consumption_value_per_unit = self._get_consumption_value(component_template, product_qty)
            total_consumption_value = consumption_value_per_unit * product_qty

            # If consumption table is not configured (all zeros), keep BoM quantity.
            if float_is_zero(
                total_consumption_value,
                precision_rounding=(component_uom and component_uom.rounding) or 0.0001,
            ) and not float_is_zero(
                line.product_qty,
                precision_rounding=(component_uom and component_uom.rounding) or 0.0001,
            ):
                _logger.warning(
                    "[BOM] Consumption table returned 0.0 for %s (term '%s'); keeping original BoM qty %s.",
                    component_template.name,
                    term,
                    line.product_qty,
                )
                continue

            if line.product_qty != total_consumption_value:
                line.product_qty = total_consumption_value
                _logger.info(
                    f"[BOM] Updated BoM line {line.id}: "
                    f"Component: {component_template.name}, "
                    f"Per-unit value: {consumption_value_per_unit}, "
                    f"Product Qty: {product_qty}, "
                    f"Total Consumption Value: {total_consumption_value}"
                )
            else:
                _logger.info(f"[BOM] Skipping BoM line {line.id}, consumption value already correct.")

    def _duplicate_and_assign_to_bom(self, bom, line_matches, term_values, has_mesmo_tecido=False, product_qty=1):
        if not bom:
            return

        # --- Preprocess fabric (UoM = m) lines to handle MESMO TECIDO (keep MESMO line, remove donor line) ---
        fabric_lines = []
        for line in bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)):
            line_data = line_matches.get(line.id)
            if not line_data:
                continue

            term = line_data['primary_term']
            component_uom = line.product_uom_id or line.product_id.uom_id
            if not (self._is_fabric_term(term) and self._is_fabric_uom(component_uom)):
                continue

            # Prefer the value for this primary term; fallback to any value
            raw_value = ''
            for t, v in (line_data.get('replacements') or []):
                if t == term and v:
                    raw_value = v
                    break
            if not raw_value:
                for _t, v in (line_data.get('replacements') or []):
                    if v:
                        raw_value = v
                        break

            raw_value = re.sub(r"\s+", " ", (raw_value or '')).strip(" ,;:")
            raw_value = self._strip_trailing_term_labels(raw_value)

            is_mesmo, mesmo_custom = self._parse_mesmo_tecido(raw_value)

            fabric_lines.append({
                'line': line,
                'term': term,
                'is_mesmo': is_mesmo,
                'mesmo_custom': self._strip_trailing_term_labels(mesmo_custom),
                'raw_value': raw_value,
            })

        has_mesmo_in_fabric = has_mesmo_tecido or any(item['is_mesmo'] for item in fabric_lines)

        donors_to_unlink = self.env['mrp.bom.line']
        for item in fabric_lines:
            if not item['is_mesmo']:
                continue

            donor = None
            for cand in fabric_lines:
                if cand['is_mesmo']:
                    continue
                if cand['line'] in donors_to_unlink:
                    continue
                donor = cand
                break

            if not donor:
                _logger.warning("[FABRIC] MESMO TECIDO detected but no other fabric line found to merge.")
                continue

            # Do NOT sum quantities for MESMO TECIDO (keep MESMO line qty as-is)
            _logger.info(
                "[FABRIC] MESMO TECIDO detected: keeping qty %s on line %s and removing donor line %s (qty %s not added)",
                item['line'].product_qty, item['line'].id, donor['line'].id, donor['line'].product_qty
            )

            # ? Naming adjustment:
            # If MESMO TECIDO exists and there is another fabric, keep the OTHER (donor) fabric name (more complete).
            # Only fall back to MESMO custom if donor has no usable value (edge-case).
            resolved_name = donor.get('raw_value') or item.get('mesmo_custom') or ''
            resolved_name = self._strip_trailing_term_labels(resolved_name)
            item['raw_value'] = resolved_name
            item['is_mesmo'] = False  # resolved; treat as normal fabric now

            donors_to_unlink |= donor['line']

        # If a generic FABRIC line exists alongside specific fabric lines, merge qty and remove generic line.
        generic_fabric_lines = [
            item for item in fabric_lines
            if (item.get('term') or '').strip().rstrip(':').upper() == 'FABRIC'
        ]
        specific_fabric_lines = [
            item for item in fabric_lines
            if (item.get('term') or '').strip().rstrip(':').upper() != 'FABRIC'
            and not item.get('is_mesmo')
        ]
        if has_mesmo_in_fabric and generic_fabric_lines and specific_fabric_lines:
            for generic in generic_fabric_lines:
                if generic['line'] in donors_to_unlink:
                    continue
                target = None
                gen_value = (generic.get('raw_value') or '').strip().lower()
                for cand in specific_fabric_lines:
                    if cand['line'] in donors_to_unlink:
                        continue
                    cand_value = (cand.get('raw_value') or '').strip().lower()
                    if gen_value and cand_value and gen_value == cand_value:
                        target = cand
                        break
                if not target:
                    for cand in specific_fabric_lines:
                        if cand['line'] in donors_to_unlink:
                            continue
                        target = cand
                        break
                if not target:
                    continue

                target_line = target['line']
                generic_line = generic['line']
                generic_qty = None
                try:
                    generic_qty = self._get_consumption_value(
                        generic_line.product_id.product_tmpl_id,
                        product_qty,
                    ) * product_qty
                except Exception:
                    generic_qty = generic_line.product_qty

                try:
                    target_line.product_qty = generic_qty
                except Exception:
                    target_line.write({'product_qty': generic_qty})

                if not (target.get('raw_value') or '').strip() and (generic.get('raw_value') or '').strip():
                    target['raw_value'] = generic.get('raw_value')

                donors_to_unlink |= generic_line
                _logger.info(
                    "[FABRIC] Replaced line %s qty with generic FABRIC line %s qty %s and removed generic.",
                    target_line.id, generic_line.id, generic_qty
                )

        # --- Main duplication / assignment pass ---
        dimensions_value = (term_values or {}).get('DIMENSIONS')
        wants_custom_dimensions = (dimensions_value or '').strip().upper().startswith('CUSTOM DIMENSIONS')

        for line in bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)):
            if line in donors_to_unlink:
                continue

            line_data = line_matches.get(line.id)
            term = line_data['primary_term'] if line_data else None

            if term == 'DIMENSIONS':
                _logger.info("[DUPLICATE] Term 'DIMENSIONS' detected, skipping duplication for BoM components.")
                continue

            original_variant = line.product_id
            product = original_variant.product_tmpl_id

            component_uom = line.product_uom_id or line.product_id.uom_id
            is_fabric_uom = self._is_fabric_uom(component_uom)
            is_fabric_component = is_fabric_uom
            replacements = [
                (replacement_term, value)
                for replacement_term, value in (line_data.get('replacements', []) if line_data else [])
                if value
            ]
            line_specific_value = ''
            if not is_fabric_component:
                has_term_value = any(
                    replacement_term == term and value
                    for replacement_term, value in replacements
                )
                if not has_term_value:
                    line_specific_value = self._get_variant_term_value(original_variant, term)
                    if not line_specific_value and not self._is_fabric_term(term):
                        line_specific_value = self._get_variant_fallback_value(
                            original_variant,
                            is_fabric_component=is_fabric_component,
                        )
                if line_specific_value:
                    replacements.append((term, line_specific_value))
                    _logger.info(
                        "[DUPLICATE] Using line-specific value '%s' for term '%s' on variant %s",
                        line_specific_value,
                        term,
                        original_variant.id,
                    )

                existing_terms = {replacement_term for replacement_term, _value in replacements}

                if self._is_fabric_term(term) and 'WOOD' not in existing_terms:
                    wood_value = self._get_variant_term_value(original_variant, 'WOOD')
                    if wood_value:
                        replacements.append(('WOOD', wood_value))
                        existing_terms.add('WOOD')
                        _logger.info(
                            "[DUPLICATE] Added WOOD value '%s' to composite fabric component for variant %s",
                            wood_value,
                            original_variant.id,
                        )

                for replacement_term, _value in (line_data.get('replacements', []) if line_data else []):
                    if replacement_term in existing_terms:
                        continue
                    if replacement_term == 'DIMENSIONS':
                        continue

                    extra_value = self._get_variant_term_value(original_variant, replacement_term)
                    if not extra_value:
                        continue

                    replacements.append((replacement_term, extra_value))
                    existing_terms.add(replacement_term)
                    _logger.info(
                        "[DUPLICATE] Filled missing value '%s' for term '%s' on variant %s",
                        extra_value,
                        replacement_term,
                        original_variant.id,
                    )

            combined_replacement = self._combine_replacements(
                term,
                replacements,
                is_fabric_component=is_fabric_component,
            ) if line_data else ''

            if not combined_replacement and not (wants_custom_dimensions and not is_fabric_component):
                continue

            _logger.info(
                "[DIMENSIONS] Line %s term '%s' fabric=%s dims_value='%s'",
                line.id,
                term,
                is_fabric_component,
                dimensions_value or '',
            )
            _logger.info(
                f"[DUPLICATE] Found product variant for '{term}' in BoM: "
                f"{original_variant.id} - {original_variant.display_name}"
            )

            # If this is a fabric meter-line and it was MESMO-resolved above, force its resolved raw_value
            if self._is_fabric_term(term) and is_fabric_uom:
                resolved = None
                for item in fabric_lines:
                    if item['line'].id == line.id:
                        resolved = item
                        break
                if resolved:
                    combined_replacement = resolved['raw_value'] or combined_replacement

            if combined_replacement:
                duplicate_name = self._build_duplicate_name(
                    product.name,
                    combined_replacement,
                    term,
                    is_fabric_uom=is_fabric_uom,
                    suffix_source=original_variant.display_name,
                )
            else:
                duplicate_name = product.name

            if not is_fabric_component:
                _logger.info(
                    "[DIMENSIONS] Appending dimensions to '%s' (dims_value='%s')",
                    duplicate_name,
                    dimensions_value or '',
                )
                duplicate_name = self._append_dimensions_term(duplicate_name, dimensions_value)

            _logger.info(f"[DUPLICATE] Generated duplicate name '{duplicate_name}' for term '{term}'")

            duplicate_variant = self._get_or_create_duplicate_variant(original_variant, duplicate_name, term)
            line.write({'product_id': duplicate_variant.id})
            _logger.info(
                f"[BOM] Replaced original product {original_variant.id} with duplicated product {duplicate_variant.id} in BoM line"
            )

        if donors_to_unlink:
            try:
                donors_to_unlink.unlink()
            except Exception as e:
                _logger.exception("[FABRIC] Failed to unlink donor fabric lines after MESMO merge: %s", e)

        # Re-sequence final BoM lines so the generated MO components follow the visible BoM order.
        for index, line in enumerate(bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)), start=1):
            target_sequence = index * 10
            if line.sequence != target_sequence:
                line.sequence = target_sequence

    def _get_or_create_duplicate_variant(self, original_variant, duplicate_name, term):
        ProductVariant = self.env['product.product'].with_context(active_test=False)
        original_attribute_ids = set(original_variant.product_template_attribute_value_ids.ids)
        original_signature = self._get_variant_signature(original_variant)
        duplicate_name = self._canonicalize_duplicate_name(duplicate_name)

        existing_variants = ProductVariant.search([('name', '=', duplicate_name)], order="active desc, create_date desc")
        if existing_variants:
            reusable = self._pick_reusable_variant(existing_variants, original_signature, duplicate_name)
            if reusable:
                return reusable

            _logger.warning(
                "[DUPLICATE] Found variants named '%s' but none match signature %s; creating new variant.",
                duplicate_name,
                list(original_signature),
            )

        # Fallback for formatting drifts (spacing/punctuation/case): find by
        # canonicalized name + exact attribute signature before creating a copy.
        fuzzy_variants = self._search_candidate_variants(ProductVariant, duplicate_name)
        if fuzzy_variants:
            reusable = self._pick_reusable_variant(
                fuzzy_variants,
                original_signature,
                duplicate_name,
                compare_canonical_name=True,
            )
            if reusable:
                return reusable

        original_template = original_variant.product_tmpl_id
        duplicate_template = original_template.copy()
        duplicate_template.name = duplicate_name

        duplicate_variant = self._match_variant_by_signature(
            duplicate_template.product_variant_ids,
            original_signature,
        )
        if not duplicate_variant:
            duplicate_variant = duplicate_template.product_variant_id

        duplicate_variant.name = duplicate_name
        mapped_ptav_ids = self._map_template_ptav_ids(duplicate_template, original_variant)
        if mapped_ptav_ids:
            duplicate_variant.write({
                'product_template_attribute_value_ids': [(6, 0, mapped_ptav_ids)],
            })

        self._copy_custom_fields(original_template, duplicate_template)
        self._copy_supplierinfo(
            original_template,
            duplicate_template,
            original_variant=original_variant,
            duplicate_variant=duplicate_variant,
        )
        self._copy_variant_fields(original_variant, duplicate_variant)

        _logger.info(f"[DUPLICATE] Created new product variant: {duplicate_variant.display_name}")

        self._assign_vendor_to_product(duplicate_template, term)

        return duplicate_variant

    @staticmethod
    def _canonicalize_duplicate_name(name):
        text = re.sub(r"\s+", " ", (name or "")).strip()
        if not text:
            return text
        text = re.sub(r"\s*,\s*", ", ", text)
        text = re.sub(r"\s*:\s*", ": ", text)
        text = re.sub(r"\s*-\s*", " - ", text)
        text = re.sub(r"\(\s+", "(", text)
        text = re.sub(r"\s+\)", ")", text)
        text = re.sub(r",\s*,+", ", ", text)
        return text.strip(" ,;")

    def _search_candidate_variants(self, product_variant_model, duplicate_name):
        tokens = re.findall(r"\w+", duplicate_name or "", flags=re.UNICODE)
        if not tokens:
            return product_variant_model.browse()
        if len(tokens) == 1:
            pattern = tokens[0]
        else:
            pattern = "%".join(tokens[:8])
        return product_variant_model.search([('name', 'ilike', pattern)], limit=300, order="active desc, create_date desc")

    def _pick_reusable_variant(self, variants, target_signature, target_name, compare_canonical_name=False):
        target_canonical = self._canonicalize_duplicate_name(target_name)
        for variant in variants:
            if self._get_variant_signature(variant) != target_signature:
                continue
            if compare_canonical_name:
                if self._canonicalize_duplicate_name(variant.name) != target_canonical:
                    continue
            if variant.active:
                _logger.info(
                    "[DUPLICATE] Reusing existing product variant '%s' with matching attributes, ID: %s",
                    target_name,
                    variant.id,
                )
                return variant

        for variant in variants:
            if self._get_variant_signature(variant) != target_signature:
                continue
            if compare_canonical_name:
                if self._canonicalize_duplicate_name(variant.name) != target_canonical:
                    continue
            if not variant.active:
                variant.write({'active': True})
                _logger.info(
                    "[DUPLICATE] Reactivated matching product variant '%s' with ID: %s",
                    target_name,
                    variant.id,
                )
                return variant
        return False

    @staticmethod
    def _get_variant_signature(variant):
        return frozenset(
            (
                ptav.attribute_id.id,
                ptav.product_attribute_value_id.id,
            )
            for ptav in variant.product_template_attribute_value_ids
            if ptav.attribute_id and ptav.product_attribute_value_id
        )

    def _map_template_ptav_ids(self, target_template, source_variant):
        source_pairs = set(
            (
                ptav.attribute_id.id,
                ptav.product_attribute_value_id.id,
            )
            for ptav in source_variant.product_template_attribute_value_ids
            if ptav.attribute_id and ptav.product_attribute_value_id
        )
        if not source_pairs:
            return []

        template_ptavs = target_template.product_variant_ids.mapped('product_template_attribute_value_ids')
        mapped_ids = []
        for ptav in template_ptavs:
            pair = (ptav.attribute_id.id, ptav.product_attribute_value_id.id)
            if pair in source_pairs:
                mapped_ids.append(ptav.id)

        return list(set(mapped_ids))

    @staticmethod
    def _match_variant_by_signature(variants, target_signature):
        target_signature = frozenset(target_signature or [])
        for variant in variants:
            signature = frozenset(
                (
                    ptav.attribute_id.id,
                    ptav.product_attribute_value_id.id,
                )
                for ptav in variant.product_template_attribute_value_ids
                if ptav.attribute_id and ptav.product_attribute_value_id
            )
            if signature == target_signature:
                return variant
        fallback = variants[:1]
        return fallback if fallback else variants

    def _copy_variant_fields(self, original_variant, duplicate_variant):
        fields_to_copy = ['default_code', 'barcode']
        values_to_write = {}
        for field in fields_to_copy:
            if hasattr(original_variant, field):
                value = getattr(original_variant, field)
                if value:
                    values_to_write[field] = value

        if values_to_write:
            duplicate_variant.write(values_to_write)

    def _append_dimensions_term(self, name, dimensions_value):
        cleaned_dimensions = re.sub(r"\s+", " ", (dimensions_value or '')).strip(" ,")
        if not cleaned_dimensions:
            return name

        suffix = self._extract_suffix(name)
        base_name = name[:-len(suffix)] if suffix else name

        is_custom_dimensions = cleaned_dimensions.strip().upper().startswith('CUSTOM DIMENSIONS')
        dimension_segment = cleaned_dimensions if is_custom_dimensions else f"DIMENSIONS: {cleaned_dimensions}"
        base_name_lower = (base_name or '').lower()
        suffix_lower = (suffix or '').lower()
        if (
            dimension_segment.lower() in base_name_lower
            or dimension_segment.lower() in suffix_lower
            or re.search(r"\bdimensions\b", suffix_lower)
            or re.search(r"\bcustom\s+dimensions\b", suffix_lower)
        ):
            return name
        if is_custom_dimensions:
            updated_base = re.sub(
                r"\bDIMENSIONS\s*:\s*CUSTOM\s+DIMENSIONS\b",
                dimension_segment,
                base_name,
                flags=re.IGNORECASE,
            )
            updated_base = re.sub(
                r"\bCUSTOM\s+DIMENSIONS\b(?!\s*:)",
                dimension_segment,
                updated_base,
                flags=re.IGNORECASE,
            )
            if updated_base != base_name:
                _logger.info(
                    "[DIMENSIONS] Replacing existing CUSTOM DIMENSIONS label in '%s' -> '%s'",
                    base_name,
                    updated_base,
                )
                return self._append_suffix(updated_base, suffix)

        if base_name:
            if base_name.endswith(','):
                base_with_dimensions = f"{base_name} {dimension_segment}"
            else:
                base_with_dimensions = f"{base_name}, {dimension_segment}" if dimension_segment not in base_name else base_name
        else:
            base_with_dimensions = dimension_segment

        return self._append_suffix(base_with_dimensions, suffix)

    def _assign_vendor_to_product(self, duplicate_product, term):
        vendor_name = None

        if vendor_name:
            vendor = self.env['res.partner'].search([('name', '=', vendor_name)], limit=1)
            if vendor:
                self.env['product.supplierinfo'].create({
                    'product_tmpl_id': duplicate_product.id,
                    'partner_id': vendor.id,
                    'min_qty': 0.00,
                    'price': 0.00,
                    'currency_id': self.env.user.company_id.currency_id.id,
                    'delay': 7,
                    'date_start': fields.Date.today(),
                })
                _logger.info(f"[VENDOR] Assigned vendor '{vendor_name}' to product {duplicate_product.name}")
            else:
                _logger.warning(f"[VENDOR] Vendor '{vendor_name}' not found for product {duplicate_product.name}")

    def _get_consumption_value(self, product_template, product_qty):
        _logger.info(f"Fetching consumption values for component: {product_template.name}, Quantity: {product_qty}")

        consumption_table = [
            product_template.price_1, product_template.price_2, product_template.price_3,
            product_template.price_4, product_template.price_5, product_template.price_6,
            product_template.price_7, product_template.price_8, product_template.price_9,
            product_template.price_10
        ]

        _logger.info(f"Consumption table values for {product_template.name}: {consumption_table}")

        if product_qty < 1:
            _logger.warning(f"Invalid quantity ({product_qty}). Defaulting to the first value in the table.")
            return consumption_table[0]

        index = min(int(product_qty) - 1, len(consumption_table) - 1)
        selected_value = consumption_table[index]

        _logger.info(
            f"Selected consumption value for Component: {product_template.name}, "
            f"Quantity: {product_qty}, "
            f"Selected Row: {index + 1}, "
            f"Value: {selected_value}"
        )
        return selected_value

    def _copy_custom_fields(self, original_product, duplicate_product):
        try:
            custom_fields = [
                'price_1', 'price_2', 'price_3', 'price_4', 'price_5',
                'price_6', 'price_7', 'price_8', 'price_9', 'price_10'
            ]

            for field in custom_fields:
                setattr(duplicate_product, field, getattr(original_product, field, 0.0))

            _logger.info(
                f"[COPY] Successfully copied custom fields from product {original_product.id} to {duplicate_product.id}"
            )
        except Exception as e:
            _logger.error(
                f"[COPY] Failed to copy custom fields from product {original_product.id} to {duplicate_product.id}: {str(e)}"
            )

    def _copy_supplierinfo(self, original_product, duplicate_product, original_variant=None, duplicate_variant=None):
        supplier_infos = original_product.seller_ids
        if not supplier_infos:
            return

        for supplier_info in supplier_infos:
            supplier_product_id = False
            if original_variant and duplicate_variant and supplier_info.product_id:
                if supplier_info.product_id.id == original_variant.id:
                    supplier_product_id = duplicate_variant.id
            values = {
                'product_tmpl_id': duplicate_product.id,
                'product_id': supplier_product_id,
                'partner_id': supplier_info.partner_id.id,
                'min_qty': supplier_info.min_qty,
                'price': supplier_info.price,
                'currency_id': supplier_info.currency_id.id,
                'delay': supplier_info.delay,
                'date_start': supplier_info.date_start,
                'date_end': supplier_info.date_end,
                'product_name': supplier_info.product_name,
                'product_code': supplier_info.product_code,
                'company_id': supplier_info.company_id.id or False,
            }
            self.env['product.supplierinfo'].create(values)

    @classmethod
    def _identify_term(cls, name, term_values=None):
        matches = cls._match_terms(name, term_values)
        if not matches:
            return None, None
        term, keyword = matches[0]
        return term, keyword

    @classmethod
    def _match_terms(cls, name, term_values=None):
        sanitized_name = cls._strip_bracket_content(name)
        normalized_name = cls._normalize_text(sanitized_name)
        _logger.debug(
            "[IDENTIFY] Checking name '%s' (sanitized: '%s') for matching terms.",
            name,
            sanitized_name,
        )

        if not normalized_name:
            return []

        matches = {}

        def add_match(term, keyword, source, position):
            if term not in cls.TERM_PRIORITY:
                return
            score = 0
            if source == 'special':
                score += 3
            elif source == 'keyword':
                score += 2
            elif source == 'label':
                score += 1

            # Composite labels shared by WOOD/FABRIC should resolve to FABRIC terms.
            if source == 'special' and keyword in cls.FABRIC_DOMINANT_SPECIAL_LABELS:
                if cls._is_fabric_term(term):
                    score += 5
                else:
                    score -= 5

            if term_values and term_values.get(term):
                score += 10

            priority = cls.TERM_PRIORITY.get(term, len(cls.TERM_PRIORITY))
            candidate = (score, position, priority, term, keyword)
            existing = matches.get(term)
            if not existing:
                matches[term] = candidate
                return

            existing_sort = (-existing[0], existing[1], existing[2])
            candidate_sort = (-candidate[0], candidate[1], candidate[2])
            if candidate_sort < existing_sort:
                matches[term] = candidate

        for term, keywords in cls.TERM_DEFINITIONS:
            matched = False
            for keyword in keywords:
                normalized_keyword = cls._normalize_text(keyword)
                position = cls._find_keyword_position(normalized_keyword, normalized_name)
                if position is not None:
                    add_match(term, keyword, 'keyword', position)
                    matched = True
                    break

            if not matched and normalized_name == cls._normalize_text(term):
                add_match(term, term, 'label', 0)
                matched = True

            if not matched:
                for label in cls.SPECIAL_LABELS.get(term, []):
                    normalized_label = cls._normalize_text(label)
                    if normalized_name == normalized_label:
                        add_match(term, label, 'special', 0)
                        break
                    if normalized_label:
                        starts_idx = normalized_name.find(normalized_label)
                        if starts_idx == 0:
                            add_match(term, label, 'special', 0)
                            break

        if not matches:
            return []

        # If a specific FABRIC term matches, drop the generic FABRIC match.
        if 'FABRIC' in matches:
            has_specific_fabric = any(
                cls._is_fabric_term(term) and term != 'FABRIC'
                for term in matches.keys()
            )
            if has_specific_fabric:
                matches.pop('FABRIC', None)

        sorted_matches = sorted(matches.values(), key=lambda item: (-item[0], item[1], item[2]))
        return [(term, keyword) for _score, _position, _priority, term, keyword in sorted_matches]

    @staticmethod
    def _find_keyword_position(keyword, name_lower):
        if not keyword or not name_lower:
            return None
        if ' ' in keyword:
            idx = name_lower.find(keyword)
            return idx if idx >= 0 else None
        match = re.search(rf'\b{re.escape(keyword)}\b', name_lower)
        return match.start() if match else None

    @staticmethod
    def _keyword_in_name(keyword, name_lower):
        return MrpProduction._find_keyword_position(keyword, name_lower) is not None
    @staticmethod
    def _normalize_text(value):
        if not value:
            return ''

        normalized = unicodedata.normalize('NFKD', value)
        stripped = ''.join(char for char in normalized if not unicodedata.combining(char))
        return stripped.lower()

    @staticmethod
    def _is_fabric_replacement_text(value):
        text = re.sub(r"\s+", " ", (value or '')).strip().upper()
        if not text:
            return False
        prefixes = (
            'FABRIC',
            'MAIN FABRIC',
            'PILLOW FABRIC',
            'FABRIC USED IN',
            'TECIDO',
            'TECIDO PRINCIPAL',
            'TECIDO DA ALMOFADA',
            'TECIDO USADO',
        )
        return any(text.startswith(prefix) for prefix in prefixes)


    def _build_duplicate_name(self, original_name, replacement, term, is_fabric_uom=True, suffix_source=None):
        if not replacement:
            return original_name

        cleaned_replacement = re.sub(r"\s+", " ", replacement).strip()
        cleaned_replacement = self._strip_trailing_term_labels(cleaned_replacement, term=term)
        sanitized_name = self._strip_bracket_content(original_name)
        suffix = self._extract_suffix(original_name)
        suffix_source = suffix_source or original_name
        suffix_for_check = self._extract_suffix(suffix_source)

        if self._is_fabric_term(term):
            if is_fabric_uom:
                return cleaned_replacement
            base = self._remove_all_fabric_labels(original_name)
            base = self._strip_bracket_content(base) or base
            base = re.sub(r"\s+", " ", (base or '')).strip(" ,;:-")
            if not base:
                return cleaned_replacement
            if cleaned_replacement.lower() in base.lower():
                return base
            return f"{base} {cleaned_replacement}".strip()
        has_fabric_segments = bool(
            re.search(r"(?i)\b(?:FABRIC|TECIDO)\b[^,]*:", cleaned_replacement)
        )
        if self._is_fabric_replacement_text(cleaned_replacement) or has_fabric_segments:
            sanitized_name = self._remove_all_fabric_labels(sanitized_name)
            sanitized_name = self._strip_bracket_content(sanitized_name) or sanitized_name
            sanitized_name = re.sub(r"\s+", " ", (sanitized_name or '')).strip(" ,;:-")

        skip_replacement_in_base = False
        if cleaned_replacement and suffix_for_check:
            suffix_text = re.sub(r"[\(\)\[\]\{\}<>]", " ", suffix_for_check)
            normalized_suffix = self._normalize_text(suffix_text)
            _logger.info(
                "[DUPLICATE] Suffix check term=%s base=%s replacement=%s suffix=%s",
                term,
                sanitized_name or original_name,
                cleaned_replacement,
                suffix_text,
            )
            # Remove duplicated parts that already appear in the suffix
            parts = [p.strip() for p in cleaned_replacement.split(",") if p.strip()]
            if len(parts) > 1:
                kept = []
                for part in parts:
                    if self._normalize_text(part) in normalized_suffix:
                        continue
                    kept.append(part)
                if kept:
                    cleaned_replacement = ", ".join(kept)
                else:
                    cleaned_replacement = ""
                _logger.info(
                    "[DUPLICATE] Removed duplicated parts term=%s kept=%s",
                    term,
                    cleaned_replacement,
                )
            if suffix and cleaned_replacement and self._normalize_text(cleaned_replacement) in normalized_suffix:
                skip_replacement_in_base = True
            if not cleaned_replacement:
                skip_replacement_in_base = True
            _logger.info(
                "[DUPLICATE] After suffix check term=%s replacement=%s skip=%s",
                term,
                cleaned_replacement,
                skip_replacement_in_base,
            )
        elif cleaned_replacement:
            _logger.info(
                "[DUPLICATE] No suffix found for term=%s base=%s replacement=%s (suffix_source=%s)",
                term,
                sanitized_name or original_name,
                cleaned_replacement,
                suffix_source,
            )

        if sanitized_name != original_name:
            _logger.info(
                f"[DUPLICATE] Sanitized original name '{original_name}' to '{sanitized_name}' before rebuilding."
            )
        special_labels = self.SPECIAL_LABELS.get(term, [])
        if any(
            sanitized_name.lower().startswith(label.lower())
            for label in special_labels
            if label
        ):
            base_name = sanitized_name
        else:
            base_name = self._remove_all_term_labels(sanitized_name) or sanitized_name
        if term and term.upper() == 'METAL' and base_name:
            if not base_name.lower().startswith('metal '):
                base_name = f"Metal {base_name}"

        separators = [':', '-']
        for separator in separators:
            if separator in sanitized_name:
                prefix, _suffix = sanitized_name.split(separator, 1)
                prefix = prefix.strip()
                if not prefix:
                    continue
                resolved_prefix = self._resolve_label(prefix, term)
                if skip_replacement_in_base:
                    base = resolved_prefix
                elif separator == ':':
                    base = f"{resolved_prefix}: {cleaned_replacement}".strip()
                else:
                    base = f"{resolved_prefix} {separator} {cleaned_replacement}".strip()
                return self._append_suffix(base, suffix)

        if term and term.lower() in (sanitized_name or '').lower():
            if cleaned_replacement.lower() in base_name.lower():
                base = base_name
            else:
                base = base_name if skip_replacement_in_base else f"{base_name} - {cleaned_replacement}"
            return self._append_suffix(base, suffix)

        label = self._resolve_label(base_name or sanitized_name or original_name, term)
        base = label if skip_replacement_in_base else f"{label}: {cleaned_replacement}"
        return self._append_suffix(base, suffix)

    @staticmethod
    def _is_fabric_uom(uom):
        if not uom:
            return False
        return (uom.name or '').strip().lower() == 'm'

    @staticmethod
    def _replace_fabric_term_in_name(original_name, term, replacement):
        if not original_name:
            return replacement

        term_label = (term or '').strip()
        if not term_label:
            return original_name

        candidate_labels = [term_label, term_label.rstrip(':').strip()]
        for label in candidate_labels:
            if not label:
                continue
            pattern = re.compile(re.escape(label), re.IGNORECASE)
            if pattern.search(original_name):
                return pattern.sub(replacement, original_name, count=1)

        return original_name

    @staticmethod
    def _is_fabric_term(term):
        return 'FABRIC' in (term or '').upper()

    @staticmethod
    def _append_suffix(base, suffix):
        if not suffix:
            return base
        if suffix.startswith(' ') or base.endswith(' '):
            return f"{base}{suffix}"
        return f"{base} {suffix}"

    @staticmethod
    def _extract_suffix(original_name):
        if not original_name:
            return ''

        matches = re.findall(r"(\s*(?:\([^)]*\)|\[[^]]*\]|\{[^}]*\}|<[^>]*>))", original_name)
        return ''.join(matches)

    def _resolve_label(self, original_label, term):
        original_label = (original_label or '').strip()
        term_label = (term or '').strip()

        if original_label and original_label.lower() != term_label.lower():
            return original_label

        special_labels = self.SPECIAL_LABELS.get(term_label, [])
        if special_labels:
            if original_label:
                for candidate in special_labels:
                    if original_label.lower() == candidate.lower():
                        return candidate
            if len(special_labels) == 1:
                return special_labels[0]

        if original_label:
            return original_label

        if special_labels:
            return special_labels[0]

        return term_label

    @staticmethod
    def _strip_bracket_content(value):
        if not value:
            return value

        sanitized = re.sub(r"\s*\([^)]*\)", "", value)
        sanitized = re.sub(r"\s*\[[^]]*\]", "", sanitized)
        sanitized = re.sub(r"\s*\{[^}]*\}", "", sanitized)
        sanitized = re.sub(r"\s*<[^>]*>", "", sanitized)
        sanitized = sanitized.strip()
        _logger.debug("[SANITIZE] Input '%s' sanitized to '%s'", value, sanitized)
        return sanitized

    def _get_variant_term_value(self, variant, term):
        if not variant or not term:
            return ''

        term_norm = self._normalize_text(term)
        base_term = self.TERM_BASE_MAP.get(term, term)
        base_norm = self._normalize_text(base_term)

        for ptav in variant.product_template_attribute_value_ids:
            attr_name = self._normalize_text(ptav.attribute_id.name or '')
            if not attr_name:
                continue
            if term_norm and term_norm in attr_name:
                return ptav.name or ''
            if base_norm and base_norm in attr_name:
                return ptav.name or ''

        return ''

    def _get_variant_fallback_value(self, variant, is_fabric_component=False):
        if not variant:
            return ''

        display_name = self._normalize_text(variant.display_name or '')
        display_matches = []
        for ptav in variant.product_template_attribute_value_ids:
            attr_name = self._normalize_text(ptav.attribute_id.name or '')
            if not attr_name:
                continue
            if 'dimensions' in attr_name:
                continue
            if not is_fabric_component and 'fabric' in attr_name:
                continue

            value = ptav.name or ''
            value_norm = self._normalize_text(value)
            if value_norm and value_norm in display_name:
                display_matches.append(value)

        if len(display_matches) == 1:
            return display_matches[0]

        for term in self.TERM_NAMES:
            if not term or term == 'DIMENSIONS':
                continue
            if not is_fabric_component and self._is_fabric_term(term):
                continue

            term_norm = self._normalize_text(term)
            for ptav in variant.product_template_attribute_value_ids:
                attr_name = self._normalize_text(ptav.attribute_id.name or '')
                if not attr_name:
                    continue
                if 'dimensions' in attr_name:
                    continue
                if term_norm and term_norm in attr_name:
                    return ptav.name or ''

        return ''

    def _map_terms_to_bom_lines(self, bom, term_values):
        line_matches = {}
        if not bom:
            return line_matches

        for line in bom.bom_line_ids.sorted(key=lambda l: (l.sequence, l.id)):
            matches = self._match_terms(line.product_id.name, term_values)
            if not matches:
                sanitized_name = self._strip_bracket_content(line.product_id.name)
                _logger.info(
                    f"[BOM] Skipping BoM line product {line.product_id.id}, as it doesn't match specified terms "
                    f"(sanitized name: '{sanitized_name}')."
                )
                continue

            replacements = []
            for term, keyword in matches:
                extracted_text = term_values.get(term, '')
                replacements.append((term, extracted_text))
                _logger.info(f"[BOM] Extracted text for term '{term}': {extracted_text}")

            primary_term = matches[0][0]
            primary_term = self.TERM_BASE_MAP.get(primary_term, primary_term)
            line_matches[line.id] = {
                'primary_term': primary_term,
                'replacements': replacements,
            }

        return line_matches

    def _combine_replacements(self, primary_term, replacements, is_fabric_component=False):
        if not replacements:
            return ''

        unique_values = {}
        for term, value in replacements:
            cleaned_value = re.sub(r"\s+", " ", value or '').strip(" ,;:")
            cleaned_value = self._strip_trailing_term_labels(cleaned_value, term=term)
            if self._is_fabric_term(term):
                cleaned_value = self._strip_leading_fabric_labels(cleaned_value)
            if not cleaned_value:
                continue
            if term not in unique_values:
                unique_values[term] = cleaned_value

        if not unique_values:
            return ''

        base_term = self.TERM_BASE_MAP.get(primary_term, primary_term)
        has_specific = any(
            self.TERM_BASE_MAP.get(term, term) == base_term and term != base_term
            for term in unique_values
        )
        if has_specific:
            unique_values.pop(base_term, None)

        ordered_terms = list(unique_values.keys())
        is_fabric_context = self._is_fabric_term(primary_term) or any(self._is_fabric_term(t) for t in ordered_terms)

        # In fabric context (especially Estofo unit components), keep only fabric terms.
        # This prevents unrelated terms (e.g. WOOD) from leaking into fabric component names.
        if is_fabric_context and is_fabric_component:
            ordered_terms = [t for t in ordered_terms if self._is_fabric_term(t)]
            unique_values = {t: unique_values[t] for t in ordered_terms if t in unique_values}
            if not ordered_terms:
                return ''
        # If specific fabric terms exist, drop generic FABRIC to avoid duplicate naming.
        if is_fabric_context and 'FABRIC' in unique_values:
            specific_fabric_terms = [
                t for t in ordered_terms
                if t != 'FABRIC' and self._is_fabric_term(t)
            ]
            if specific_fabric_terms:
                unique_values.pop('FABRIC', None)
                ordered_terms = [t for t in ordered_terms if t != 'FABRIC']

        if is_fabric_context and not is_fabric_component:
            fabric_terms = [t for t in ordered_terms if self._is_fabric_term(t)]
            non_fabric_terms = [t for t in ordered_terms if not self._is_fabric_term(t)]

            # If all fabric terms resolve to a single value, collapse to generic FABRIC/TECIDO label.
            fabric_values = []
            seen_vals = set()
            for fabric_term in fabric_terms:
                value = unique_values.get(fabric_term) or ''
                value = self._strip_trailing_term_labels(value, term=fabric_term)
                value = self._strip_leading_fabric_labels(value)
                value = re.sub(r"\s+", " ", value).strip(" ,;:")
                if not value:
                    continue
                key = value.lower()
                if key in seen_vals:
                    continue
                seen_vals.add(key)
                fabric_values.append(value)
            if len(fabric_values) == 1 and not non_fabric_terms:
                return f"TECIDO: {fabric_values[0]}"

            segments = []
            seen_segments = set()
            for term in ordered_terms:
                segment_value = unique_values.get(term) or ''
                segment_value = self._strip_trailing_term_labels(segment_value, term=term)
                if self._is_fabric_term(term):
                    segment_value = self._strip_leading_fabric_labels(segment_value)
                segment_value = re.sub(r"\s+", " ", segment_value).strip(" ,;:")
                if not segment_value:
                    continue
                segment_key = (term, segment_value.lower())
                if segment_key in seen_segments:
                    continue
                seen_segments.add(segment_key)
                segments.append(f"{self._get_pt_term_label(term)}: {segment_value}")

            return ', '.join(segments)

        # ? FABRIC: values-only
        # Adjustment:
        # - If MESMO TECIDO exists AND there are other (non-mesmo) fabrics, DROP MESMO (even with custom) and keep the other fabrics.
        # - If ONLY MESMO exists and it has custom, return the custom.
        # - If ONLY MESMO exists with no custom, return empty.
        if is_fabric_context and is_fabric_component:
            mesmo_customs = []
            has_mesmo = False

            # First detect MESMO TECIDO + collect customs
            for t in ordered_terms:
                v = unique_values.get(t) or ''
                is_mesmo, custom = self._parse_mesmo_tecido(v)
                if is_mesmo:
                    has_mesmo = True
                    custom = self._strip_trailing_term_labels(custom)
                    custom = re.sub(r"\s+", " ", (custom or "")).strip(" ,;:")
                    if custom:
                        mesmo_customs.append(custom)

            # Build non-mesmo parts (real fabrics)
            parts = []
            seen = set()
            for t in ordered_terms:
                v = unique_values[t]
                if self._is_mesmo_tecido(v):
                    continue
                v = re.sub(r"\bMESMO(?:\s+(?:TECIDO|FABRIC))?\b", "", v, flags=re.IGNORECASE)
                v = self._strip_trailing_term_labels(v)
                v = self._strip_leading_fabric_labels(v)
                v = re.sub(r"\s+", " ", v).strip(" ,;:")
                if not v:
                    continue
                key = v.lower()
                if key in seen:
                    continue
                seen.add(key)
                parts.append(v)

            # ? If MESMO exists and we have other fabrics, keep the other fabrics (more complete)
            if has_mesmo and parts:
                return ", ".join(parts)

            # If no other fabrics exist, but MESMO has custom(s), use them
            if mesmo_customs:
                out = []
                seen2 = set()
                for c in mesmo_customs:
                    k = c.lower()
                    if k in seen2:
                        continue
                    seen2.add(k)
                    out.append(c)
                return ", ".join(out)

            # If only MESMO existed (no custom) -> empty; else normal parts
            return ", ".join(parts)

        if len(unique_values) == 1:
            only_term = ordered_terms[0]
            only_base_term = self.TERM_BASE_MAP.get(only_term, only_term)
            if only_term == primary_term or only_base_term == base_term:
                return unique_values[only_term]

        segments = [f"{term}: {unique_values[term]}" for term in ordered_terms]
        return ', '.join(segments)
